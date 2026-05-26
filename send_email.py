#!/usr/bin/env python3
"""Send the latest newsletter issue via Resend API."""

import csv
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path


def load_dotenv(path: str = ".env"):
    """Minimal .env loader."""
    env_path = Path(__file__).parent / path
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            os.environ.setdefault(key, value)


def get_latest_issue() -> dict | None:
    """Return the most recent entry from index.json, or None."""
    index_path = Path(__file__).parent / "newsletters" / "index.json"
    if not index_path.exists():
        return None
    with open(index_path) as f:
        issues = json.load(f)
    if not issues:
        return None
    return issues[-1]


def prepare_email_html(html: str, browser_url: str | None = None) -> str:
    """Prepare newsletter HTML for email delivery."""
    # Strip all <script>...</script> blocks
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)

    # Remove the theme toggle button
    html = re.sub(
        r'<button[^>]*id\s*=\s*["\']theme-toggle["\'][^>]*>[\s\S]*?</button>',
        "", html, flags=re.IGNORECASE,
    )

    # Remove the progress bar
    html = re.sub(
        r'<div[^>]*id\s*=\s*["\']progress-bar["\'][^>]*>[\s\S]*?</div>',
        "", html, flags=re.IGNORECASE,
    )

    # Inject "View in browser" banner right after <body...>
    if browser_url:
        banner = (
            '<div style="background-color:#C15F3C; text-align:center; '
            'padding:12px 20px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif; '
            'font-size:13px; letter-spacing:0.05em; text-transform:uppercase;">'
            f'<a href="{browser_url}" style="color:#FFFFFF; text-decoration:none;" '
            'target="_blank">View in browser for the full interactive experience &#8594;</a>'
            '</div>'
        )
        html = re.sub(
            r"(<body[^>]*>)",
            rf"\1{banner}",
            html,
            count=1,
            flags=re.IGNORECASE,
        )

    return html


def fetch_subscribers() -> list[str]:
    """Fetch subscriber emails from the Google Sheet CSV export."""
    sheet_url = os.environ.get("SUBSCRIBERS_SHEET_URL", "").strip()
    fallback = os.environ.get("RECIPIENT_EMAIL", "").strip()
    fallback_list = [e.strip() for e in fallback.split(",") if e.strip()] if fallback else []

    if not sheet_url:
        return fallback_list

    try:
        req = urllib.request.Request(sheet_url, headers={"User-Agent": "ClaudeDispatch/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")

        reader = csv.reader(io.StringIO(raw))
        header = next(reader, None)
        if not header:
            print("WARNING: Subscriber sheet is empty, using fallback recipients")
            return fallback_list

        email_col = None
        for i, col in enumerate(header):
            if "email" in col.lower():
                email_col = i
                break
        if email_col is None:
            print("WARNING: No 'email' column found in sheet, using fallback recipients")
            return fallback_list

        emails = []
        for row in reader:
            if len(row) > email_col:
                addr = row[email_col].strip()
                if "@" in addr and addr not in emails:
                    emails.append(addr)

        if not emails:
            print("WARNING: No subscribers in sheet yet, using fallback recipients")
            return fallback_list

        for fb in fallback_list:
            if fb not in emails:
                emails.insert(0, fb)

        print(f"Loaded {len(emails)} subscriber(s) from Google Sheet")
        return emails

    except Exception as e:
        print(f"WARNING: Could not fetch subscriber sheet ({e}), using fallback recipients")
        return fallback_list


def send_via_resend(api_key: str, from_addr: str, to: str, subject: str, html: str):
    """Send an email via Resend API."""
    payload = json.dumps({
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "html": html,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend API {e.code}: {body}") from e


def send_newsletter(html_path: str | None = None):
    """Send an HTML newsletter file via Resend."""

    load_dotenv()

    resend_api_key = os.environ.get("RESEND_API_KEY")
    from_addr = os.environ.get("FROM_EMAIL", "Claude & Co. <onboarding@resend.dev>")
    base_url = os.environ.get("NEWSLETTER_BASE_URL", "").strip().rstrip("/")

    recipients = fetch_subscribers()

    if not resend_api_key or not recipients:
        print("ERROR: Missing RESEND_API_KEY or no recipients configured.")
        print("Set RESEND_API_KEY and either SUBSCRIBERS_SHEET_URL or RECIPIENT_EMAIL.")
        sys.exit(1)

    # Determine which file to send
    if html_path:
        newsletter_file = Path(html_path)
    else:
        latest = get_latest_issue()
        if not latest:
            print("ERROR: No newsletter issues found in index.json")
            sys.exit(1)
        newsletter_file = Path(__file__).parent / "newsletters" / latest["filename"]

    if not newsletter_file.exists():
        print(f"ERROR: Newsletter file not found: {newsletter_file}")
        sys.exit(1)

    html_content = newsletter_file.read_text(encoding="utf-8")

    # Build the browser URL
    browser_url = f"{base_url}/{newsletter_file.name}" if base_url else None

    # Prepare email-safe HTML
    email_html = prepare_email_html(html_content, browser_url)

    # Extract subject line
    latest = get_latest_issue()
    subject = latest["subject"] if latest and latest.get("subject") else f"Claude & Co. — {newsletter_file.stem}"

    # Send to each subscriber
    print("Sending via Resend API...")
    for addr in recipients:
        try:
            result = send_via_resend(resend_api_key, from_addr, addr, subject, email_html)
            print(f"  Sent to {addr} (id: {result.get('id', 'unknown')})")
        except Exception as e:
            print(f"  FAILED to send to {addr}: {e}")

    print(f"Newsletter delivered to {len(recipients)} recipient(s): {newsletter_file.name}")
    if browser_url:
        print(f"Browser link: {browser_url}")


if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    send_newsletter(path_arg)
