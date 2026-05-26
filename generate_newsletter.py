#!/usr/bin/env python3
"""Generate a newsletter issue using the Anthropic API directly."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    # Determine issue info
    index_path = Path("newsletters/index.json")
    issues = []
    if index_path.exists():
        with open(index_path) as f:
            issues = json.load(f)

    last_issue_num = issues[-1]["issue_number"] if issues else 0
    last_issue_date = issues[-1]["date"] if issues else ""
    next_issue = last_issue_num + 1
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if last_issue_date:
        date_range = f"from {last_issue_date} to {today}"
    else:
        date_range = f"the past 7 days (up to and including {today})"

    # Load CLAUDE.md for instructions
    claude_md = Path("CLAUDE.md").read_text()

    # Load only the CSS/style block from the reference newsletter to save tokens
    ref_path = Path("newsletters/2026-05-22-newsletter.html")
    ref_css = ""
    if ref_path.exists():
        ref_html = ref_path.read_text()
        style_start = ref_html.find("<style>")
        style_end = ref_html.find("</style>")
        if style_start != -1 and style_end != -1:
            ref_css = ref_html[style_start : style_end + len("</style>")]

    system_prompt = f"""You are a newsletter generator. Follow these instructions exactly:

{claude_md}

IMPORTANT: Output ONLY the raw HTML for the newsletter. No markdown fences, no explanation, just the HTML starting with <!DOCTYPE html>."""

    user_prompt = f"""Generate Issue #{next_issue} of Claude & Co. for {today}.

Cover news {date_range}.

First, search the web for recent Anthropic/Claude news and broader tech news for this date range. Then write the complete newsletter as a self-contained HTML file with inline CSS, following the structure and style guide in the instructions.

Use this exact CSS style block from the reference newsletter:

{ref_css}

Generate the new issue now. Output only the HTML."""

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Generating Issue #{next_issue} for {today}...")
    print(f"Covering news {date_range}")

    # Call the API with web search enabled (server-side tool, no client loop needed)
    messages = [{"role": "user", "content": user_prompt}]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=messages,
    )

    # Handle pause_turn — the model may need to continue after running out of iterations
    while response.stop_reason == "pause_turn":
        print("Model paused, continuing...")
        messages.append({"role": "assistant", "content": response.content})
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=system_prompt,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
            messages=messages,
        )

    # Extract final HTML from response
    html_content = ""
    for block in response.content:
        if hasattr(block, "text"):
            html_content += block.text

    # Clean up if wrapped in code fences
    html_content = html_content.strip()
    if html_content.startswith("```"):
        lines = html_content.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing fence
        html_content = "\n".join(lines)

    if not html_content.startswith("<!DOCTYPE"):
        print("WARNING: Output may not be valid HTML", file=sys.stderr)
        print(f"First 200 chars: {html_content[:200]}", file=sys.stderr)

    # Save newsletter
    output_path = Path(f"newsletters/{today}-newsletter.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content)
    print(f"Saved to {output_path}")

    # Update index.json
    new_entry = {
        "issue_number": next_issue,
        "date": today,
        "filename": f"{today}-newsletter.html",
        "subject": f"Claude & Co. #{next_issue}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Try to extract a better subject from the HTML title
    import re

    title_match = re.search(r"<title>(.*?)</title>", html_content)
    if title_match:
        new_entry["subject"] = title_match.group(1)

    issues.append(new_entry)
    with open(index_path, "w") as f:
        json.dump(issues, f, indent=2)
    print(f"Updated {index_path}")

    print("Done!")


if __name__ == "__main__":
    main()
