#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# install_cron.sh — Install the cron job for The Claude Dispatch
#
# Runs the newsletter generator every Monday and Wednesday at 8:00 AM.
# ──────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"

if [ ! -x "$RUN_SCRIPT" ]; then
    chmod +x "$RUN_SCRIPT"
fi

CRON_SCHEDULE="0 8 * * 1,3"  # 8:00 AM on Monday (1) and Wednesday (3)
CRON_ENTRY="$CRON_SCHEDULE $RUN_SCRIPT"

# Check if already installed
if crontab -l 2>/dev/null | grep -qF "$RUN_SCRIPT"; then
    echo "Cron job already installed:"
    crontab -l | grep "$RUN_SCRIPT"
    echo ""
    echo "To remove it:  crontab -e  (and delete the line)"
    exit 0
fi

# Add to existing crontab
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "Cron job installed successfully!"
echo ""
echo "  Schedule: Every Monday and Wednesday at 8:00 AM"
echo "  Command:  $RUN_SCRIPT"
echo ""
echo "Verify with:  crontab -l"
echo "Remove with:  crontab -e  (delete the line)"
echo ""
echo "NOTE: cron only runs when your Mac is awake. See README.md for"
echo "alternatives if you need more reliable scheduling."
