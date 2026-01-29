#!/usr/bin/env python3
"""
RVA Figure Drawing Calendar - Main Scrape Script

This script orchestrates all scrapers and outputs events.json.

Usage:
    python scrape.py                    # Normal run with caching
    python scrape.py --force            # Force refresh, ignore cache
    python scrape.py --stats            # Show cache statistics
    python scrape.py --clear-cache      # Clear all cached data
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scrapers import run_all_scrapers, get_cache


def main():
    parser = argparse.ArgumentParser(description="Scrape figure drawing events")
    parser.add_argument("--force", action="store_true", help="Force refresh, ignore cache")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached data")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--sources", "-s", type=str, help="Comma-separated list of sources to scrape")
    args = parser.parse_args()

    cache = get_cache()

    if args.stats:
        stats = cache.get_stats()
        print("Cache Statistics:")
        print(f"  Total sources cached: {stats['total_sources']}")
        for source, info in stats.get("sources", {}).items():
            status = "EXPIRED" if info["expired"] else "valid"
            print(f"  - {source}: {info['event_count']} events, {info['age_minutes']} min old ({status})")
        return

    if args.clear_cache:
        cache.invalidate_all()
        print("Cache cleared")
        return

    # Parse sources
    sources = None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",")]

    # Run scrapers
    events = run_all_scrapers(force_refresh=args.force, sources=sources)

    # Build output
    output = {
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "events": events,
    }

    # Output
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(f"\nWrote {len(events)} events to {output_path}")
    else:
        # Print to stdout for piping
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
