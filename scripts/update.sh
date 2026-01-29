#!/bin/bash
#
# RVA Figure Drawing Calendar - Update Script
# Runs Claude to scrape events, validates output, commits and pushes
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_FILE="$PROJECT_DIR/data/events.json"
PROMPT_FILE="$SCRIPT_DIR/scrape-prompt.md"
LOG_FILE="$PROJECT_DIR/data/scrape.log"

cd "$PROJECT_DIR"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting scrape" >> "$LOG_FILE"

# Run Claude with the scrape prompt
echo "Running Claude scraper..."
if ! claude -p "$(cat "$PROMPT_FILE")" --print --output-format json > "$DATA_FILE.tmp" 2>> "$LOG_FILE"; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Claude failed" >> "$LOG_FILE"
    rm -f "$DATA_FILE.tmp"
    exit 1
fi

# Validate JSON output
echo "Validating JSON..."
if ! jq empty "$DATA_FILE.tmp" 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Invalid JSON output" >> "$LOG_FILE"
    echo "Invalid JSON:" >> "$LOG_FILE"
    head -100 "$DATA_FILE.tmp" >> "$LOG_FILE"
    rm -f "$DATA_FILE.tmp"
    exit 1
fi

# Check that we got at least some events
EVENT_COUNT=$(jq '.events | length' "$DATA_FILE.tmp" 2>/dev/null || echo "0")
if [ "$EVENT_COUNT" -lt 1 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No events found, keeping previous data" >> "$LOG_FILE"
    rm -f "$DATA_FILE.tmp"
    exit 0
fi

# Replace the data file
mv "$DATA_FILE.tmp" "$DATA_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Scraped $EVENT_COUNT events" >> "$LOG_FILE"

# Git commit and push (if in a git repo)
if [ -d .git ]; then
    if ! git diff --quiet "$DATA_FILE" 2>/dev/null; then
        echo "Committing changes..."
        git add "$DATA_FILE"
        git commit -m "Update events $(date '+%Y-%m-%d')"

        if git remote -v | grep -q origin; then
            echo "Pushing to remote..."
            git push origin main || git push origin master || true
        fi

        echo "$(date '+%Y-%m-%d %H:%M:%S') - Committed and pushed" >> "$LOG_FILE"
    else
        echo "No changes to commit"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - No changes" >> "$LOG_FILE"
    fi
fi

echo "Done!"
