# RVA Figure Drawing Calendar

A static site aggregating figure drawing sessions in Richmond, VA.

## Live Site

Visit: https://[username].github.io/rva-figure-drawing-calendar/site/

## How It Works

1. Claude CLI with Playwright MCP scrapes event sources daily
2. Events are normalized to JSON and committed to this repo
3. GitHub Pages serves the static site
4. The site reads `data/events.json` and renders a filterable calendar

## Data Sources

- [VisArts](https://www.visarts.org) - Visual Arts Center of Richmond
- [Studio Two Three](https://www.studiotwothree.org) - Printmaking & arts nonprofit
- [Artspace](https://www.artspacegallery.org) - Community gallery
- [VMFA Studio School](https://vmfa.museum/studio-school/) - Museum art school

## Local Development

```bash
# Serve the site locally
cd site
python -m http.server 8000
# Visit http://localhost:8000
```

## Manual Update

```bash
./scripts/update.sh
```

## Automation (Cron)

Add to crontab for daily updates at 6 AM:

```bash
crontab -e
# Add:
0 6 * * * /path/to/rva-figure-drawing-calendar/scripts/update.sh
```

## Project Structure

```
├── data/
│   └── events.json       # Aggregated event data
├── site/
│   ├── index.html        # Calendar interface
│   ├── style.css
│   └── app.js
├── scripts/
│   ├── scrape-prompt.md  # Claude scraping instructions
│   └── update.sh         # Automation script
└── docs/
    └── plans/            # Design documents
```
