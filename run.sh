#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# run.sh — Generate and send Claude & Co.
#
# Called by cron (or manually). Invokes Claude Code to generate
# the newsletter, then sends it via Gmail SMTP.
# ──────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="$SCRIPT_DIR/run.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ── 1. Determine issue number and date range ─────────────────

LAST_ISSUE_DATE=""
LAST_ISSUE_NUM=0

if [ -f newsletters/index.json ]; then
    LAST_ISSUE_NUM=$(python3 -c "
import json
with open('newsletters/index.json') as f:
    issues = json.load(f)
print(issues[-1]['issue_number'] if issues else 0)
" 2>/dev/null || echo "0")

    LAST_ISSUE_DATE=$(python3 -c "
import json
with open('newsletters/index.json') as f:
    issues = json.load(f)
print(issues[-1]['date'] if issues else '')
" 2>/dev/null || echo "")
fi

NEXT_ISSUE=$((LAST_ISSUE_NUM + 1))
TODAY=$(date '+%Y-%m-%d')

if [ -z "$LAST_ISSUE_DATE" ]; then
    DATE_RANGE="the past 7 days (up to and including $TODAY)"
else
    DATE_RANGE="from $LAST_ISSUE_DATE to $TODAY"
fi

log "Starting generation — Issue #$NEXT_ISSUE covering $DATE_RANGE"

# ── 2. Build the prompt for Claude Code ───────────────────────

PROMPT="Generate Issue #$NEXT_ISSUE of Claude & Co. for $TODAY.

Cover news $DATE_RANGE.

Follow ALL instructions in CLAUDE.md exactly. Do the following:

1. Use WebSearch to find recent Anthropic/Claude news and broader tech news for the date range.
2. Write the complete newsletter as a self-contained HTML file with inline CSS, following the structure in CLAUDE.md.
3. Save the HTML file to newsletters/${TODAY}-newsletter.html using the Write tool.
4. Read the current newsletters/index.json, then update it by appending this new issue entry with these fields:
   - \"issue_number\": $NEXT_ISSUE
   - \"date\": \"$TODAY\"
   - \"filename\": \"${TODAY}-newsletter.html\"
   - \"subject\": (a short subject line for the email, like \"Claude & Co. #$NEXT_ISSUE — [brief headline]\")
   - \"generated_at\": (current ISO timestamp)

Do NOT skip any step. Do NOT ask questions — just generate the newsletter."

# ── 3. Invoke Claude Code ─────────────────────────────────────

log "Invoking Claude Code..."

claude -p "$PROMPT" \
    --allowedTools "WebSearch,WebFetch,Read,Write,Glob,Grep,Edit" \
    >> "$LOG_FILE" 2>&1

NEWSLETTER_FILE="newsletters/${TODAY}-newsletter.html"

if [ ! -f "$NEWSLETTER_FILE" ]; then
    log "ERROR: Newsletter file was not created: $NEWSLETTER_FILE"
    exit 1
fi

log "Newsletter generated: $NEWSLETTER_FILE"

# ── 4. Send the email ─────────────────────────────────────────

log "Sending email..."
python3 send_email.py "$NEWSLETTER_FILE" 2>&1 | tee -a "$LOG_FILE"

log "Done — Issue #$NEXT_ISSUE sent successfully."
