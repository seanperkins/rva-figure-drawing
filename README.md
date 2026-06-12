# RVA Figure Drawing Calendar

A static site aggregating figure drawing sessions in Richmond, VA.

## Live Site

[**https://seanperkins.github.io/rva-figure-drawing/**](https://seanperkins.github.io/rva-figure-drawing/)

## How It Works

1. Claude CLI (Sonnet) with Playwright MCP scrapes event sources daily
2. Events are normalized to JSON and committed to this repo
3. GitHub Pages serves the static site
4. The site reads `site/data/events.json` and renders a filterable calendar
5. A weekly discovery job searches for new figure drawing sources in the RVA area

## Data Sources

Sources are defined in [`scripts/sources.json`](scripts/sources.json). To add a new source, append an entry:

```json
{
  "id": "short-kebab-case-id",
  "url": "https://example.com/events",
  "location": "Venue Name",
  "address": "123 Main St, Richmond, VA 23220",
  "defaultTags": ["open-session", "nude"],
  "cacheTtlHours": 24,
  "extraInstructions": "Scraping hints for this source"
}
```

Current sources:

- [VisArts](https://www.visarts.org) - Visual Arts Center of Richmond
- [Studio Two Three](https://www.studiotwothree.org) - Printmaking & arts nonprofit
- [Artspace](https://www.artspacegallery.org) - Community gallery
- [Art Works RVA](https://artworksrva.com) - Thriving Artists program
- [VMFA Studio School](https://vmfa.museum/studio-school/) - Museum art school
- [Eventbrite](https://www.eventbrite.com/d/va--richmond/figure-drawing/) - Event aggregator

## Local Development

```bash
# Serve the site locally
cd site
python -m http.server 8000
# Visit http://localhost:8000
```

## Scripts

```bash
# Run a scrape (uses caching, only hits stale sources)
./scripts/update.sh

# Force refresh all sources (ignore cache)
python3 scripts/scrape.py --force

# Scrape specific sources only
python3 scripts/scrape.py --sources visarts,vmfa

# View cache stats
python3 scripts/scrape.py --stats

# Clear cache
python3 scripts/scrape.py --clear-cache

# Discover new sources
./scripts/discover-sources.sh
```

## Automation (launchd)

Two launchd agents handle scheduled tasks. launchd is used instead of cron because it handles MacBook sleep correctly — if the Mac is asleep at the scheduled time, the job runs when it wakes up.

| Job | Schedule | Script |
|-----|----------|--------|
| `com.rva-figure-drawing.update` | Daily at 8:00 AM | `scripts/update.sh` |
| `com.rva-figure-drawing.discover` | Mondays at 9:00 AM | `scripts/discover-sources.sh` |

### Install

```bash
# Symlink plists and load
ln -sf "$(pwd)/scripts/launchd/com.rva-figure-drawing.update.plist" ~/Library/LaunchAgents/
ln -sf "$(pwd)/scripts/launchd/com.rva-figure-drawing.discover.plist" ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.rva-figure-drawing.update.plist
launchctl load ~/Library/LaunchAgents/com.rva-figure-drawing.discover.plist
```

### Manage

```bash
# Check status
launchctl list | grep rva-figure

# Manually trigger a run
launchctl start com.rva-figure-drawing.update
launchctl start com.rva-figure-drawing.discover

# View logs
tail -f logs/update-stdout.log
tail -f logs/discover-stdout.log

# Unload
launchctl unload ~/Library/LaunchAgents/com.rva-figure-drawing.update.plist
launchctl unload ~/Library/LaunchAgents/com.rva-figure-drawing.discover.plist
```

## Notifications

Both scripts send macOS notification banners via [`terminal-notifier`](https://github.com/julienXX/terminal-notifier). Clicking a notification opens the relevant log file.

```bash
# Prerequisite
brew install terminal-notifier
```

| Script | Event | Type | Click opens |
|--------|-------|------|-------------|
| `update.sh` | Scrape succeeded | Normal | Dismisses |
| `update.sh` | Scraper failed | Error + sound | `logs/scrape.log` |
| `update.sh` | Invalid JSON output | Error + sound | `logs/scrape.log` |
| `update.sh` | No events found | Error + sound | `logs/scrape.log` |
| `discover-sources.sh` | No new sources | Normal | Dismisses |
| `discover-sources.sh` | New sources found | Normal | Dismisses |
| `discover-sources.sh` | Discovery failed | Error + sound | `logs/discover.log` |

Notification logic lives in `scripts/notify.sh`.

## Project Structure

```
├── site/
│   ├── index.html          # Calendar interface
│   ├── style.css
│   ├── app.js
│   └── data/
│       ├── events.json     # Aggregated event data
│       └── calendar.ics    # Subscribable calendar
├── scripts/
│   ├── sources.json        # Configurable source definitions
│   ├── scrape.py           # Main scraper entry point
│   ├── update.sh           # Scrape → validate → commit → push
│   ├── discover-sources.sh # Weekly new source discovery
│   ├── notify.sh           # macOS notification helper
│   ├── generate-ics.py     # ICS calendar generator
│   ├── scrape-prompt.md    # Legacy Claude scraping prompt
│   ├── scrapers/           # Scraper modules with caching
│   └── launchd/            # macOS launchd plist files
└── docs/
    └── plans/              # Design documents
```
