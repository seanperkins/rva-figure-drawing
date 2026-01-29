# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RVA Figure Drawing Calendar is a static site aggregating figure drawing sessions in Richmond, VA. It uses Claude CLI with Playwright MCP for AI-powered web scraping, commits normalized JSON to the repo, and serves via GitHub Pages.

## Development Commands

```bash
# Local development server
cd site && python -m http.server 8000
# Visit http://localhost:8000

# Run scraper manually (requires Claude CLI + Playwright MCP)
./scripts/update.sh

# Validate events.json
jq empty site/data/events.json
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Claude CLI +    │────▶│ events.json  │────▶│ Static Site     │
│ Playwright MCP  │     │ (normalized) │     │ (GitHub Pages)  │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

**Data Flow:**
1. `update.sh` invokes Claude with `scrape-prompt.md`
2. Claude uses Playwright MCP to scrape 6 venue sources
3. Events are normalized to JSON with deduplication
4. JSON is validated with jq, then committed and pushed
5. GitHub Pages serves the static site which reads the JSON

**Key Files:**
- `scripts/scrape-prompt.md` - Scraping instructions for Claude (sources, output format, rules)
- `scripts/update.sh` - Automation: scrape → validate → commit → push
- `site/data/events.json` - Aggregated event data
- `site/app.js` - Frontend event rendering and filtering logic

## Event Data Schema

Each event in `events.json` has:
- `source`: Source identifier (visarts, studio23, artspace, artworks, vmfa, eventbrite)
- `date`: YYYY-MM-DD format
- `startTime`/`endTime`: HH:MM (24hr)
- `costValue`: Numeric cost for filtering (null if free/unknown)
- `tags`: Array of ["open-session", "instructed", "costumed", "nude"]
- `status`: "confirmed" | "projected"
- `registrationStatus`: "available" | "waitlist" | "closed" | "sold-out" | "unknown"

## Scraping Sources

The scraper visits these URLs (see `scripts/scrape-prompt.md` for details):
- VisArts: visarts.org/classes
- Studio Two Three: studiotwothree.org/classes
- Artspace: artspacegallery.org
- Art Works RVA: artworksrva.com/rva-thriving-artists-2
- VMFA Studio School: vmfa.museum/studio-school
- Eventbrite: eventbrite.com/d/va--richmond/figure-drawing

## Frontend

Zero-build vanilla JS/HTML/CSS. Two views:
- **List view**: Filterable event cards
- **Calendar view**: Monthly grid with event indicators

Filters: cost (free/paid), type (open-session/instructed), location dropdown
