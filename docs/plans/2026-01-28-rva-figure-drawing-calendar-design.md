# Richmond Figure Drawing Calendar - Design Document

**Date:** 2026-01-28
**Status:** Validated via proof-of-concept

## Overview

A static site aggregating figure drawing sessions in Richmond, VA. Hosted on GitHub Pages with automated daily data updates.

## Data Sources

| Source | URL | Type |
|--------|-----|------|
| VisArts | https://www.visarts.org/classes/?fwp_classes_duration=open-figure-draw-paint | Venue |
| Studio Two Three | https://www.studiotwothree.org/classes | Venue |
| Artspace | https://www.artspacegallery.org/ | Venue |
| Art Works RVA | https://artworksrva.com/rva-thriving-artists-2/ | Aggregator |
| VMFA Studio School | https://vmfa.museum/studio-school/ | Venue |
| Eventbrite (RVA) | Search: "figure drawing richmond va" | Aggregator |

**Note:** Unkindness Art was evaluated but appears to be a tattoo studio without figure drawing events.

## Architecture

### Scraping Approach: Claude + Playwright MCP

Instead of writing custom Python scrapers with brittle CSS selectors, we use Claude CLI with the Playwright MCP to:

1. Navigate to each source URL
2. Take a page snapshot
3. Extract events using Claude's understanding of the page structure
4. Output normalized JSON

**Validated:** Successfully extracted 15 events from VisArts and 1 from Studio Two Three.

### File Structure

```
├── data/
│   └── events.json          # Aggregated event data
├── site/
│   ├── index.html           # Calendar view
│   ├── style.css
│   └── app.js
├── scripts/
│   ├── scrape-prompt.md     # Prompt for Claude scraping
│   └── update.sh            # Daily cron script
├── docs/
│   └── plans/
│       └── 2026-01-28-rva-figure-drawing-calendar-design.md
└── README.md
```

## Data Model

```json
{
  "source": "visarts",
  "sourceUrl": "https://...",
  "title": "Figure Drawing (TH-D)",
  "date": "2026-02-05",
  "startTime": "13:00",
  "endTime": "15:30",
  "location": "Visual Arts Center of Richmond",
  "address": "1812 W Main St, Richmond, VA 23220",
  "cost": "$7 ($3 tuition + model fee)",
  "costValue": 7,
  "url": "https://...",
  "description": "Open figure drawing session...",
  "tags": ["open-session", "nude"],
  "status": "confirmed | projected",
  "registrationStatus": "available | waitlist | closed | sold-out",
  "instructor": "Mary Beth Beasley"
}
```

### Key Fields

- **`status`**: `confirmed` (has direct URL) vs `projected` (inferred from recurrence pattern)
- **`costValue`**: Numeric for filtering; extracted as lowest number from cost string
- **`tags`**: `open-session`, `instructed`, `costumed`, `nude`

## Design Decisions

### Recurring Events
- **Approach:** Hybrid - expand recurrence within 90-day rolling window
- **Rationale:** Keeps calendar actionable without stale far-future entries

### Deduplication
- **Match criteria:** Same date + same location + same start time
- **Priority:** Venue sites preferred over aggregators (Eventbrite)

### Update Frequency
- **Schedule:** Daily via cron
- **Rationale:** Figure drawing sessions don't change frequently; daily is polite to source sites

## Static Site Features

### Views
- Calendar view (month/week)
- List view (upcoming events)

### Filters
- Date range
- Cost (Free / Paid / All)
- Type (open-session, instructed, costumed, nude)
- Location

### Additional
- Last-updated timestamp
- Mobile-friendly responsive design
- Direct links to registration

## Automation

### update.sh

```bash
#!/bin/bash
cd /path/to/rva-figure-drawing-calendar

# Run Claude with scraping prompt
claude -p "$(cat scripts/scrape-prompt.md)" --print > data/events.json.tmp

# Validate output
if jq empty data/events.json.tmp 2>/dev/null; then
    mv data/events.json.tmp data/events.json

    # Commit and push
    git add data/events.json
    git commit -m "Update events $(date +%Y-%m-%d)"
    git push
else
    echo "Invalid JSON output, skipping update"
    rm data/events.json.tmp
fi
```

### Cron Entry

```
0 6 * * * /path/to/rva-figure-drawing-calendar/scripts/update.sh
```

## Implementation Plan

1. **Scrape prompt** - Write the Claude prompt that visits all sources and extracts events
2. **Static site** - Build HTML/CSS/JS calendar interface
3. **Update script** - Automation script with validation
4. **GitHub Pages** - Deploy and configure
5. **Cron setup** - Schedule daily updates

## Nice to Have (Future)

- iCal export (.ics feed)
- Source discovery script (find new venues via search)
- Email/RSS notifications for new events
