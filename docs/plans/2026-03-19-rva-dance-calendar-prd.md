# RVA Dance Calendar — Product Requirements Document

## Overview

A static site aggregating social dance events in Richmond, VA. Same architecture as the RVA Figure Drawing Calendar: Claude CLI + Playwright MCP scrapes venue websites, normalizes events to JSON, commits to the repo, and serves via GitHub Pages.

The goal is a single place for Richmond dancers to find classes, socials, and workshops across all dance styles — salsa, swing, ballroom, contra, bachata, and more.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Claude CLI +    │────▶│ events.json  │────▶│ Static Site     │
│ Playwright MCP  │     │ (normalized) │     │ (GitHub Pages)  │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

**Data Flow:**
1. `update.sh` invokes Claude with `scrape-prompt.md`
2. Claude uses Playwright MCP to scrape venue sources
3. Events are normalized to JSON with deduplication
4. JSON is validated with jq, then committed and pushed
5. GitHub Pages serves the static site which reads the JSON

**Stack:** Zero-build vanilla HTML/CSS/JS. No frameworks, no bundlers.

## Event Data Schema

```json
{
  "source": "rvaswing",
  "sourceUrl": "https://rvaswing.blogspot.com/",
  "title": "First Friday Swing Dance",
  "date": "2026-04-03",
  "startTime": "19:00",
  "endTime": "22:30",
  "location": "The Dance Space",
  "address": "6004 West Broad St, Richmond, VA 23230",
  "cost": "$10",
  "costValue": 10.0,
  "url": "https://rvaswing.blogspot.com/",
  "description": "Beginner lesson 7-7:45pm, then open swing dancing",
  "danceStyles": ["west-coast-swing", "lindy-hop"],
  "eventType": "social",
  "level": "all-levels",
  "status": "confirmed",
  "registrationStatus": "available",
  "recurring": true
}
```

### Field Definitions

| Field | Type | Description |
|---|---|---|
| `source` | string | Source identifier (see Sources below) |
| `sourceUrl` | string | URL of the page scraped |
| `title` | string | Event title |
| `date` | string | `YYYY-MM-DD` |
| `startTime` | string | `HH:MM` (24hr) |
| `endTime` | string | `HH:MM` (24hr) or null |
| `location` | string | Venue name |
| `address` | string | Full street address |
| `cost` | string | Human-readable cost string |
| `costValue` | number/null | Lowest numeric cost for filtering (null = unknown/free) |
| `url` | string | Direct link to event or registration |
| `description` | string | Brief description |
| `danceStyles` | string[] | See Dance Styles below |
| `eventType` | string | `"class"`, `"social"`, `"workshop"`, `"performance"` |
| `level` | string | `"beginner"`, `"intermediate"`, `"advanced"`, `"all-levels"` |
| `status` | string | `"confirmed"` or `"projected"` |
| `registrationStatus` | string | `"available"`, `"waitlist"`, `"closed"`, `"sold-out"`, `"unknown"` |
| `recurring` | boolean | Whether this is a recurring weekly/monthly event |

### Dance Styles (tag vocabulary)

- `salsa`
- `bachata`
- `kizomba`
- `west-coast-swing`
- `lindy-hop`
- `east-coast-swing`
- `ballroom`
- `contra`
- `two-step`
- `tango`
- `zouk`
- `hustle`
- `line-dancing`
- `hip-hop`
- `other`

## Scraping Sources

### 1. The Dance Space (source: `"dancespace"`)
- URL: https://sites.google.com/view/thedancespace
- Location: "The Dance Space", "6004 West Broad St, Richmond, VA 23230"
- Events: Friday Ballroom Dancing, First Friday WCS, 2nd Sunday Rhythm Night, beginner group classes
- Dance styles: ballroom, west-coast-swing, salsa, tango, hustle

### 2. RVA Swing (source: `"rvaswing"`)
- URL: https://rvaswing.blogspot.com/
- Location: Various (often at The Dance Space)
- Events: Monthly swing dances with beginner lessons
- Dance styles: lindy-hop, east-coast-swing, west-coast-swing

### 3. RVA Dance Studio / Salsa with Boris (source: `"rvadance"`)
- URL: https://www.rvadance.net/events
- Location: "RVA Dance Studio" (check site for address)
- Events: Weekly salsa/bachata/kizomba classes and socials
- Dance styles: salsa, bachata, kizomba, zouk

### 4. TADAMS — Contra Dance (source: `"tadams"`)
- URL: https://tadamsva.org/dances/
- Location: Lewis Ginter Recreation Center / Ginter Hall
- Events: 2nd & 4th Saturday contra dances, Sunday afternoon dances
- Dance styles: contra
- Note: Live music at every dance, beginners welcome, no partner needed

### 5. West End Latin & Ballroom Dance Club (source: `"westendballroom"`)
- URL: https://www.westendballroom.org/
- Events: Sunday beginner classes, regular social dances
- Dance styles: ballroom, salsa, swing

### 6. Eventbrite — Richmond Dance Events (source: `"eventbrite"`)
- URL: https://www.eventbrite.com/d/va--richmond/dance-classes/
- Also: https://www.eventbrite.com/d/va--richmond/salsa-social-dancing/
- Catch-all for: Salsa Sundays at Stone Brewing, singles line dancing, pop-up workshops
- Dance styles: varies

### 7. Arthur Murray Richmond (source: `"arthurmurray"`)
- URL: https://arthurmurrayrichmond.com/
- Location: "Arthur Murray Richmond", "3983 Deep Rock Rd, Richmond, VA 23233"
- Events: Group classes, social dance parties
- Dance styles: ballroom, salsa, swing, tango

### 8. Rigby's Jig (source: `"rigbysjig"`)
- URL: https://rigbysjig.com/
- Events: Group and private lessons, wedding dance prep
- Dance styles: ballroom, swing, tango, line-dancing

## Frontend

### Views

1. **List view** — Filterable event cards showing date, time, location, dance style tags, cost, and event type
2. **Calendar view** — Monthly grid with event indicators, click to see day's events

### Filters

| Filter | Options |
|---|---|
| Dance style | Multi-select from dance styles list |
| Event type | Class / Social / Workshop / All |
| Level | Beginner / Intermediate / Advanced / All Levels |
| Cost | Free / Paid / All |
| Location | Dropdown of all venues |

### Event Cards

Each card shows:
- Date and time
- Event title
- Venue name and address
- Dance style tags (color-coded pills)
- Event type badge (class/social/workshop)
- Cost
- Level indicator
- Link to source/registration
- "Recurring" indicator if applicable

### Design Notes

- Mobile-first responsive layout
- Color-coded dance style tags for quick scanning
- Source color coding per venue (like the figure drawing calendar)
- "Tonight" / "This Week" quick filters at the top
- Dark/light mode support

## Key Files

```
rva-dance-calendar/
├── CLAUDE.md                    # Project instructions
├── scripts/
│   ├── scrape-prompt.md         # Scraping instructions for Claude
│   └── update.sh                # Automation: scrape → validate → commit → push
├── site/
│   ├── index.html               # Main page
│   ├── app.js                   # Frontend rendering and filtering
│   ├── style.css                # Styles
│   └── data/
│       └── events.json          # Aggregated event data
└── docs/
    └── plans/                   # Design docs
```

## Development Commands

```bash
# Local development server
cd site && python -m http.server 8000

# Run scraper manually (requires Claude CLI + Playwright MCP)
./scripts/update.sh

# Validate events.json
jq empty site/data/events.json
```

## Success Criteria

- Aggregates events from all 8 sources into a single JSON file
- Events are deduplicated (same event on Eventbrite and venue site)
- Filters work intuitively across all dimensions
- Calendar and list views render correctly on mobile and desktop
- Scraper runs daily via cron/launchd and auto-commits
- Site loads fast (no build step, no frameworks, minimal assets)

## Out of Scope (for now)

- User accounts or saved preferences
- Email/push notifications for new events
- Venue reviews or ratings
- Event submission by venue owners
- Backend server (this is a static site)
