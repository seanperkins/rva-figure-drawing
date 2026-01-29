"""
Eventbrite scraper using JSON-LD extraction.

Eventbrite embeds structured data in individual event pages.
Strategy:
1. Fetch search results page
2. Extract event URLs from the page
3. Fetch each event page and extract JSON-LD
"""

import re
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin

from .base import BaseScraper, Event, extract_json_ld, find_events_in_json_ld, parse_json_ld_event


class EventLinkExtractor(HTMLParser):
    """Extract Eventbrite event links from search results."""

    def __init__(self):
        super().__init__()
        self.event_urls: list[str] = []
        self._event_pattern = re.compile(r"https://www\.eventbrite\.com/e/[^\"]+")

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if "/e/" in href and "eventbrite.com" in href:
                # Clean up the URL
                url = href.split("?")[0]  # Remove query params
                if url not in self.event_urls:
                    self.event_urls.append(url)

    def handle_data(self, data):
        # Also look for URLs in data-href or similar
        matches = self._event_pattern.findall(data)
        for url in matches:
            clean = url.split("?")[0]
            if clean not in self.event_urls:
                self.event_urls.append(clean)


class EventbriteScraper(BaseScraper):
    """Scraper for Eventbrite figure drawing events in Richmond."""

    source_id = "eventbrite"
    source_url = "https://www.eventbrite.com/d/va--richmond/figure-drawing/"
    default_tags = ["open-session", "nude"]

    def scrape(self) -> list[Event]:
        """Scrape Eventbrite for figure drawing events."""
        events = []

        # First, try to get event URLs from search results
        try:
            result = self.fetch(self.source_url, use_cache_headers=False)

            # Try JSON-LD from search page first
            json_ld_events = self.extract_json_ld_events(result.html)
            if json_ld_events:
                print(f"  [{self.source_id}] Found {len(json_ld_events)} events via JSON-LD")
                return json_ld_events

            # Extract event URLs from search results
            parser = EventLinkExtractor()
            parser.feed(result.html)

            # Limit to avoid too many requests
            event_urls = parser.event_urls[:20]
            print(f"  [{self.source_id}] Found {len(event_urls)} event URLs to check")

            # Fetch each event page for JSON-LD
            for url in event_urls:
                event = self._fetch_event_page(url)
                if event:
                    events.append(event)

        except Exception as e:
            print(f"  [{self.source_id}] Error fetching search page: {e}")

        return events

    def _fetch_event_page(self, url: str) -> Optional[Event]:
        """Fetch an individual event page and extract JSON-LD."""
        try:
            result = self.fetch(url, use_cache_headers=False)

            json_ld = extract_json_ld(result.html)
            event_data = find_events_in_json_ld(json_ld)

            if event_data:
                event = parse_json_ld_event(event_data[0], self.source_id, self.source_url)
                if event:
                    event.url = url
                    # Check if it's figure drawing related
                    title_lower = event.title.lower()
                    if "figure" in title_lower or "life drawing" in title_lower or "drawing" in title_lower:
                        event.tags = self.default_tags
                        return event
        except Exception as e:
            print(f"    Error fetching {url}: {e}")

        return None


def create_scraper() -> EventbriteScraper:
    """Factory function to create the scraper."""
    return EventbriteScraper()
