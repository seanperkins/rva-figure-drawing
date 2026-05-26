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
from .cache import get_cache

SOURCES_FILE = Path(__file__).parent.parent / "sources.json"

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
        default_tags: list[str] | None = None,
    ):
        super().__init__()
        self.source_id = source_id
        self.source_url = source_url
        self.default_location = default_location
        self.default_address = default_address
        self.extra_instructions = extra_instructions
        self.default_tags = default_tags or ["open-session", "nude"]

    def scrape(self) -> list[Event]:
        """Invoke Claude to scrape the page."""
        prompt = SCRAPE_PROMPT.format(
            url=self.source_url,
            extra_instructions=self.extra_instructions,
        )

        try:
            # Run Claude CLI
            result = subprocess.run(
                ["claude", "-p", prompt, "--print", "--output-format", "text", "--model", "sonnet"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"  [{self.source_id}] Claude error: {result.stderr}")
                return []

            # Parse JSON output
            output = result.stdout.strip()

            # Try to extract JSON from the output
            events_data = self._extract_json(output)

            if events_data is None:
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


def load_sources() -> list[dict]:
    """Load source definitions from sources.json."""
    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def create_scraper(source: dict) -> ClaudePlaywrightScraper:
    """Create a scraper from a source config dict."""
    return ClaudePlaywrightScraper(
        source_id=source["id"],
        source_url=source["url"],
        default_location=source.get("location", ""),
        default_address=source.get("address", ""),
        extra_instructions=source.get("extraInstructions", ""),
        default_tags=source.get("defaultTags"),
    )
