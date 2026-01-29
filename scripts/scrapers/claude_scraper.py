"""
Claude-based scraper for sources requiring JavaScript rendering.

This scraper invokes Claude with Playwright MCP to scrape dynamic pages,
but only when the cache is stale.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .base import BaseScraper, Event
from .cache import get_cache, SOURCE_TTLS


SCRAPE_PROMPT = '''You are scraping figure drawing events. Use Playwright to visit the URL and extract events.

Visit: {url}

Output a JSON array of events (no markdown, just raw JSON):
[
  {{
    "title": "Event title",
    "date": "YYYY-MM-DD",
    "startTime": "HH:MM",
    "endTime": "HH:MM",
    "location": "Venue name",
    "address": "Full address",
    "cost": "$XX",
    "costValue": XX.XX,
    "url": "Direct link",
    "description": "Brief description",
    "tags": ["open-session", "nude"],
    "registrationStatus": "available|waitlist|closed|sold-out|unknown"
  }}
]

Rules:
- Only include figure drawing / life drawing events
- Only include future events (today or later)
- Extract actual dates, not relative dates
- Output ONLY valid JSON array, nothing else

{extra_instructions}
'''


class ClaudePlaywrightScraper(BaseScraper):
    """
    A scraper that uses Claude with Playwright MCP for dynamic pages.
    Checks cache first to avoid unnecessary Claude invocations.
    """

    def __init__(
        self,
        source_id: str,
        source_url: str,
        default_location: str = "",
        default_address: str = "",
        extra_instructions: str = "",
    ):
        super().__init__()
        self.source_id = source_id
        self.source_url = source_url
        self.default_location = default_location
        self.default_address = default_address
        self.extra_instructions = extra_instructions
        self.default_tags = ["open-session", "nude"]

    def scrape(self) -> list[Event]:
        """Invoke Claude to scrape the page."""
        prompt = SCRAPE_PROMPT.format(
            url=self.source_url,
            extra_instructions=self.extra_instructions,
        )

        try:
            # Run Claude CLI
            result = subprocess.run(
                ["claude", "-p", prompt, "--print", "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode != 0:
                print(f"  [{self.source_id}] Claude error: {result.stderr}")
                return []

            # Parse JSON output
            output = result.stdout.strip()

            # Try to extract JSON from the output
            events_data = self._extract_json(output)

            if not events_data:
                print(f"  [{self.source_id}] No valid JSON in output")
                return []

            # Convert to Event objects
            events = []
            for data in events_data:
                event = Event(
                    source=self.source_id,
                    source_url=self.source_url,
                    title=data.get("title", ""),
                    date=data.get("date", ""),
                    start_time=data.get("startTime"),
                    end_time=data.get("endTime"),
                    location=data.get("location", self.default_location),
                    address=data.get("address", self.default_address),
                    cost=data.get("cost", ""),
                    cost_value=data.get("costValue"),
                    url=data.get("url", ""),
                    description=data.get("description", ""),
                    tags=data.get("tags", self.default_tags),
                    registration_status=data.get("registrationStatus", "unknown"),
                    instructor=data.get("instructor"),
                )
                events.append(event)

            return events

        except subprocess.TimeoutExpired:
            print(f"  [{self.source_id}] Claude timed out")
            return []
        except Exception as e:
            print(f"  [{self.source_id}] Error: {e}")
            return []

    def _extract_json(self, text: str) -> Optional[list]:
        """Extract JSON array from text output."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in the text
        import re
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None


def create_visarts_scraper() -> ClaudePlaywrightScraper:
    """Create VisArts scraper."""
    return ClaudePlaywrightScraper(
        source_id="visarts",
        source_url="https://www.visarts.org/classes/?fwp_classes_duration=open-figure-draw-paint",
        default_location="Visual Arts Center of Richmond",
        default_address="1812 W Main St, Richmond, VA 23220",
        extra_instructions="""
Look for Figure Drawing classes. Note:
- Cost shows "$3 tuition" but total is ~$7 with model fee
- Extract instructor name if shown
""",
    )


def create_vmfa_scraper() -> ClaudePlaywrightScraper:
    """Create VMFA scraper."""
    return ClaudePlaywrightScraper(
        source_id="vmfa",
        source_url="https://vmfa.museum/calendar/classes/?fwp_keywords=figure%20drawing",
        default_location="VMFA Studio School",
        default_address="200 N Arthur Ashe Blvd, Richmond, VA 23220",
        extra_instructions="""
Look for figure drawing classes in the Studio School listings.
These are usually instructed classes, so use tags: ["instructed", "nude"]
""",
    )


def create_studiotwothree_scraper() -> ClaudePlaywrightScraper:
    """Create Studio Two Three scraper."""
    return ClaudePlaywrightScraper(
        source_id="studiotwothree",
        source_url="https://www.studiotwothree.org/adult-workshops",
        default_location="Studio Two Three",
        default_address="3300 W Clay St, Richmond, VA 23230",
        extra_instructions="""
Look for events with "Figure Drawing" or "Drink & Draw" in the title.
These are usually open sessions.
""",
    )


def create_eventbrite_scraper() -> ClaudePlaywrightScraper:
    """Create Eventbrite scraper."""
    return ClaudePlaywrightScraper(
        source_id="eventbrite",
        source_url="https://www.eventbrite.com/d/va--richmond/figure-drawing/",
        extra_instructions="""
Search for figure drawing events in Richmond, VA.
For each event:
- Click through to get full details if needed
- Get the direct Eventbrite event URL
- Get the venue name and address from the event details
""",
    )
