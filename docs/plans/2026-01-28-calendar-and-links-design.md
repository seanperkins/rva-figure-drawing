# Calendar Integration & Link Improvements Design

**Date:** 2026-01-28

## Overview

Improve link visibility in the UI, make locations clickable to Google Maps, and add calendar integration (per-event ICS download + subscription feed).

## Changes

### 1. Link Styling & Clickable Locations

- **Date color**: Change from blue (`--accent`) to neutral color - not a link, shouldn't look like one
- **Event titles**: Add external link icon (↗) after title text
- **Locations**: Make clickable with Google Maps link + ↗ icon
  - URL format: `https://www.google.com/maps/search/?api=1&query={encoded address}`
  - Uses the `address` field from event data

### 2. Per-Event "Add to Calendar"

- **Placement**: Upper right corner of event card, aligned with date row
- **Appearance**: Calendar icon (📅) + "Add to Calendar" text; icon-only on mobile
- **Behavior**: Click generates ICS client-side and triggers download
- **ICS content**: Title, date/time, location, address, description, registration URL

### 3. Calendar Subscription

- **Placement**: New section in footer, above sources
- **Content**:
  - Heading: "Subscribe to Calendar"
  - Description: "Automatically stay up to date with figure drawing events in Richmond."
  - Subscribe button
- **Button behavior**: `webcal://` protocol link to `calendar.ics`
- **calendar.ics**: Generated during scrape, contains all future events, includes refresh interval

## Files to Modify

1. `site/style.css` - Link styling, button styles, subscription section
2. `site/app.js` - Google Maps links, ICS generation, "Add to Calendar" buttons
3. `site/index.html` - Subscription section in footer
4. `scripts/scrape-prompt.md` - Generate calendar.ics during scrape
