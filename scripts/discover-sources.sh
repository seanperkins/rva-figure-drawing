#!/bin/bash
#
# RVA Figure Drawing Calendar - Discover New Sources
# Runs weekly to find new figure drawing venues/sources in Richmond, VA
# and propose additions to sources.json
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCES_FILE="$SCRIPT_DIR/sources.json"
LOG_FILE="$PROJECT_DIR/logs/discover.log"
LOCK_FILE="$PROJECT_DIR/.discover.lock"
LAST_RUN_FILE="$PROJECT_DIR/.cache/last-discover-run"
MIN_DAYS_BETWEEN_RUNS=13

# Load notification helper
source "$SCRIPT_DIR/notify.sh"

# Cleanup function
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Ensure directories exist
mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$LAST_RUN_FILE")"

# Bi-weekly cadence guard: launchd fires weekly, but we only want to run
# every ~2 weeks. Skip if last successful run was less than 13 days ago.
if [ -f "$LAST_RUN_FILE" ]; then
    LAST_RUN=$(stat -f %m "$LAST_RUN_FILE" 2>/dev/null || echo 0)
    DAYS_SINCE=$(( ($(date +%s) - LAST_RUN) / 86400 ))
    if [ "$DAYS_SINCE" -lt "$MIN_DAYS_BETWEEN_RUNS" ]; then
        echo "Last discovery was $DAYS_SINCE days ago, skipping (bi-weekly cadence)"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Skipped (last run $DAYS_SINCE days ago)" >> "$LOG_FILE"
        exit 0
    fi
fi

# Check for lock file (prevent concurrent runs); auto-clear if stale (>6h)
STALE_LOCK_SECONDS=21600
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
    if [ "$LOCK_AGE" -gt "$STALE_LOCK_SECONDS" ]; then
        echo "Stale lock found (${LOCK_AGE}s old), removing"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleared stale lock (${LOCK_AGE}s)" >> "$LOG_FILE"
        rm -f "$LOCK_FILE"
    else
        echo "Another discovery is already running (lock ${LOCK_AGE}s old)"
        exit 1
    fi
fi
touch "$LOCK_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting source discovery" >> "$LOG_FILE"

# Read current sources for context
CURRENT_SOURCES=$(cat "$SOURCES_FILE")

PROMPT=$(cat <<'PROMPT_EOF'
You are helping maintain an RVA (Richmond, VA) figure drawing calendar.

Here are the sources we currently track:
PROMPT_EOF
)

PROMPT="$PROMPT
$CURRENT_SOURCES
"

PROMPT="$PROMPT"'
Search the web for figure drawing and life drawing sessions, classes, and open studios in Richmond, Virginia that we are NOT already tracking. Look for:

1. Art studios, galleries, or community spaces hosting figure drawing sessions
2. Recurring life drawing meetups or groups
3. Art schools or colleges with open figure drawing sessions
4. Any Eventbrite, Meetup, or similar listings for RVA figure drawing

For any NEW sources you find (not already in our list), output a JSON array of source objects to add. Use this exact format:

[
  {
    "id": "short-kebab-case-id",
    "url": "https://direct-url-to-their-events-or-classes-page",
    "location": "Venue Name",
    "address": "Full street address, Richmond, VA ZIP",
    "defaultTags": ["open-session", "nude"],
    "cacheTtlHours": 24,
    "extraInstructions": "Brief instructions for scraping this source"
  }
]

Rules:
- Only include sources in the Richmond, VA metro area
- Only include sources that specifically offer figure drawing / life drawing
- Do not include sources we already track (check the IDs and URLs above)
- Verify URLs are real and accessible before including them
- If no new sources are found, output an empty array: []
- Output ONLY the JSON array, nothing else
'

echo "Searching for new sources..."
RESULT=$(claude -p "$PROMPT" --print --output-format text --model sonnet 2>> "$LOG_FILE") || {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Claude failed" >> "$LOG_FILE"
    notify_error "RVA Drawing Calendar" "Source discovery failed" "$LOG_FILE"
    exit 1
}

# Try to extract JSON array from the result
NEW_SOURCES=$(echo "$RESULT" | python3 -c "
import sys, json, re
text = sys.stdin.read().strip()
# Try direct parse
try:
    data = json.loads(text)
    print(json.dumps(data))
    sys.exit(0)
except json.JSONDecodeError:
    pass
# Try to find JSON array in text
match = re.search(r'\[[\s\S]*\]', text)
if match:
    try:
        data = json.loads(match.group())
        print(json.dumps(data))
        sys.exit(0)
    except json.JSONDecodeError:
        pass
print('[]')
" 2>/dev/null) || NEW_SOURCES="[]"

# Check if we found anything new
COUNT=$(echo "$NEW_SOURCES" | jq 'length')

if [ "$COUNT" -eq 0 ]; then
    echo "No new sources found."
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No new sources found" >> "$LOG_FILE"
    touch "$LAST_RUN_FILE"
    notify "RVA Drawing Calendar" "Source discovery ran. No new sources found."
    exit 0
fi

echo "Found $COUNT new source(s)!"
echo "$NEW_SOURCES" | jq '.[].id'

# Merge new sources into sources.json
python3 -c "
import json, sys

with open('$SOURCES_FILE', 'r') as f:
    existing = json.load(f)

new = json.loads('''$NEW_SOURCES''')

existing_ids = {s['id'] for s in existing}
added = []
for source in new:
    if source['id'] not in existing_ids:
        existing.append(source)
        added.append(source['id'])

if added:
    with open('$SOURCES_FILE', 'w') as f:
        json.dump(existing, f, indent=2)
        f.write('\n')
    print(f'Added {len(added)} source(s): {added}')
else:
    print('All discovered sources already exist.')
"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Discovery complete, found $COUNT new source(s)" >> "$LOG_FILE"
touch "$LAST_RUN_FILE"

# If we're in a git repo and sources changed, commit
cd "$PROJECT_DIR"
if [ -d .git ] && ! git diff --quiet "$SOURCES_FILE" 2>/dev/null; then
    echo "Committing updated sources..."
    git add "$SOURCES_FILE"
    git commit -m "Add new figure drawing sources $(date '+%Y-%m-%d')"

    if git remote -v | grep -q origin; then
        git push origin main || git push origin master || true
    fi

    echo "$(date '+%Y-%m-%d %H:%M:%S') - Committed new sources" >> "$LOG_FILE"
fi

notify "RVA Drawing Calendar" "Found $COUNT new source(s)!"
echo "Done!"
