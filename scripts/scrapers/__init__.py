"""
RVA Figure Drawing Calendar - Modular Scraper System

This package provides efficient scrapers with:
- Source-specific caching with configurable TTLs
- HTTP caching with ETag/Last-Modified support
- JSON-LD extraction where available
- Parallel execution
- Claude + Playwright integration for dynamic sites

Usage:
    from scrapers import run_all_scrapers
    events = run_all_scrapers()
"""

from .cache import get_cache, ScraperCache, SOURCE_TTLS
from .base import Event, BaseScraper

__all__ = [
    "get_cache",
    "ScraperCache",
    "SOURCE_TTLS",
    "Event",
    "BaseScraper",
    "run_all_scrapers",
]


def run_all_scrapers(
    force_refresh: bool = False,
    sources: list[str] | None = None,
) -> list[dict]:
    """
    Run all scrapers and return combined events.

    Args:
        force_refresh: If True, ignore cache and scrape fresh data
        sources: If provided, only run these specific sources

    Returns:
        List of event dictionaries
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime

    from .claude_scraper import (
        create_visarts_scraper,
        create_vmfa_scraper,
        create_studiotwothree_scraper,
        create_eventbrite_scraper,
    )

    # All available scrapers
    all_scrapers = {
        "visarts": create_visarts_scraper,
        "vmfa": create_vmfa_scraper,
        "studiotwothree": create_studiotwothree_scraper,
        "eventbrite": create_eventbrite_scraper,
    }

    # Filter to requested sources
    if sources:
        scrapers_to_run = {k: v for k, v in all_scrapers.items() if k in sources}
    else:
        scrapers_to_run = all_scrapers

    if force_refresh:
        cache = get_cache()
        for source_id in scrapers_to_run:
            cache.invalidate(source_id)
        print(f"Cache cleared for: {list(scrapers_to_run.keys())}")

    all_events = []
    print(f"Running {len(scrapers_to_run)} scrapers: {list(scrapers_to_run.keys())}")

    # Check which sources actually need scraping (not cached)
    cache = get_cache()
    cached_events = []
    scrapers_needed = []

    for source_id, factory in scrapers_to_run.items():
        cached = cache.get(source_id)
        if cached and not force_refresh:
            print(f"  [{source_id}] Using cache ({cached.age_minutes()} min old, {len(cached.events)} events)")
            cached_events.extend(cached.events)
        else:
            scrapers_needed.append((source_id, factory))

    if not scrapers_needed:
        print("All sources served from cache!")
        all_events = cached_events
    else:
        print(f"Scraping {len(scrapers_needed)} sources: {[s[0] for s in scrapers_needed]}")

        # Run scrapers that need fresh data
        # Note: Running sequentially because Claude CLI doesn't handle parallel well
        for source_id, factory in scrapers_needed:
            scraper = factory()
            try:
                events = scraper.run()
                all_events.extend(events)
            except Exception as e:
                print(f"  [{source_id}] Failed: {e}")

        # Add cached events
        all_events.extend(cached_events)

    # Sort by date
    all_events.sort(key=lambda e: (e.get("date", ""), e.get("startTime", "")))

    # Deduplicate (same date + location + time)
    seen = set()
    unique_events = []
    for event in all_events:
        key = (event.get("date"), event.get("location"), event.get("startTime"))
        if key not in seen:
            seen.add(key)
            unique_events.append(event)

    print(f"\nTotal: {len(unique_events)} unique events")
    return unique_events
