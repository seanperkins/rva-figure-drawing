# RVA Figure Drawing Calendar - Scrape Prompt

You are scraping figure drawing events in Richmond, VA. Use the Playwright MCP to visit each source and extract events.

## Output Format

Output a single JSON object with this structure:

```json
{
  "lastUpdated": "ISO-8601 timestamp",
  "events": [...]
}
```

Each event must have:
```json
{
  "source": "source-id",
  "sourceUrl": "URL of the page scraped",
  "title": "Event title",
  "date": "YYYY-MM-DD",
  "startTime": "HH:MM (24hr)",
  "endTime": "HH:MM (24hr)",
  "location": "Venue name",
  "address": "Full address",
  "cost": "Human-readable cost string",
  "costValue": null or lowest numeric cost,
  "url": "Direct link to event/registration",
  "description": "Brief description",
  "tags": ["open-session" | "instructed" | "costumed" | "nude"],
  "status": "confirmed",
  "registrationStatus": "available | waitlist | closed | sold-out | unknown"
}
```

## Sources to Scrape

### 1. VisArts (source: "visarts")
- Navigate to: https://www.visarts.org/classes/?fwp_classes_duration=open-figure-draw-paint
- Location: "Visual Arts Center of Richmond", "1812 W Main St, Richmond, VA 23220"
- Look for: Figure Drawing classes with dates, times, costs
- Tags: ["open-session", "nude"]
- Note: Cost shows "$3 tuition" but total is ~$7 with model fee

### 2. Studio Two Three (source: "studio23")
- Navigate to: https://www.studiotwothree.org/classes
- Location: "Studio Two Three", "109 W 15th St, Richmond, VA 23224"
- Look for: Classes with "Figure Drawing" in the title
- Tags: ["open-session", "nude"]

### 3. Artspace (source: "artspace")
- Navigate to: https://www.artspacegallery.org/
- Look for: Events or classes related to figure drawing
- Location: "Artspace", "0 E 4th St, Richmond, VA 23224"

### 4. Art Works RVA / Thriving Artists (source: "artworks")
- Navigate to: https://artworksrva.com/rva-thriving-artists-2/
- Look for: Figure drawing sessions, life drawing events
- May link to Eventbrite for registration

### 5. VMFA Studio School (source: "vmfa")
- Navigate to: https://vmfa.museum/studio-school/
- Then look for figure drawing in their class listings
- Location: "VMFA Studio School", "200 N Arthur Ashe Blvd, Richmond, VA 23220"

### 6. Eventbrite Search (source: "eventbrite")
- Navigate to: https://www.eventbrite.com/d/va--richmond/figure-drawing/
- Extract any figure drawing events in Richmond area
- Use the venue info from each event listing

## Rules

1. **Only include figure drawing / life drawing events** - Skip other art classes
2. **Only include future events** - Skip any events with dates before today
3. **Extract actual dates** - Don't include events without specific dates
4. **Prefer venue URLs over Eventbrite** - If same event exists on both, keep venue version
5. **Set status to "confirmed"** for all events with direct URLs
6. **If a source has no figure drawing events, skip it** - Don't create placeholder entries
7. **If a source fails to load, log the error but continue** - Don't fail the entire scrape

## Deduplication

Before outputting, remove duplicates:
- Same date + same location + same start time = duplicate
- Keep the entry from the venue's own site (not Eventbrite)

## Output

Output ONLY the JSON object, no markdown code fences, no explanation. The output must be valid JSON.
