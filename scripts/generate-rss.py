#!/usr/bin/env python3
"""
Generate feed.xml (RSS 2.0) from events.json for feed-reader subscription.
"""

import json
import sys
from datetime import datetime, timezone
from email.utils import formatdate
from pathlib import Path
from xml.sax.saxutils import escape

SITE_URL = "https://seanperkins.github.io/rva-figure-drawing/"
FEED_URL = "https://seanperkins.github.io/rva-figure-drawing/data/feed.xml"


def parse_event_datetime(date_str, time_str):
    """Parse YYYY-MM-DD + HH:MM into a datetime."""
    if time_str:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return datetime.strptime(date_str, "%Y-%m-%d")


def format_event_time(event):
    """Human-friendly time range, e.g. '7:00 PM – 9:00 PM'."""
    def to_12h(t):
        h, m = t.split(":")
        h = int(h)
        suffix = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12}:{m} {suffix}"

    start = event.get("startTime")
    end = event.get("endTime")
    if start and end:
        return f"{to_12h(start)} – {to_12h(end)}"
    if start:
        return to_12h(start)
    return ""


def generate_item(event, build_dt):
    """Generate an RSS <item> for an event."""
    event_dt = parse_event_datetime(event["date"], event.get("startTime"))
    weekday = event_dt.strftime("%a, %b %-d")
    time_range = format_event_time(event)

    title_prefix = f"{weekday}"
    if time_range:
        title_prefix += f" · {time_range}"
    title = f"{title_prefix} — {event.get('title', 'Figure Drawing')}"

    location = event.get("location", "")
    if event.get("address"):
        location = f"{location}, {event['address']}" if location else event["address"]

    description_parts = []
    if location:
        description_parts.append(f"Location: {location}")
    if event.get("cost"):
        description_parts.append(f"Cost: {event['cost']}")
    if event.get("instructor"):
        description_parts.append(f"Instructor: {event['instructor']}")
    if event.get("description"):
        description_parts.append(event["description"])
    description = " | ".join(description_parts)

    uid = f"{event['date']}-{(event.get('startTime') or '0000').replace(':', '')}-{event['source']}@rvafiguredrawing"
    link = event.get("url") or SITE_URL

    # Use scrape build time as pubDate so new events surface in readers.
    pub_date = formatdate(build_dt.timestamp(), usegmt=True)

    lines = [
        "    <item>",
        f"      <title>{escape(title)}</title>",
        f"      <link>{escape(link)}</link>",
        f"      <guid isPermaLink=\"false\">{escape(uid)}</guid>",
        f"      <pubDate>{pub_date}</pubDate>",
        f"      <description>{escape(description)}</description>",
    ]
    for tag in event.get("tags", []):
        lines.append(f"      <category>{escape(tag)}</category>")
    lines.append("    </item>")
    return "\n".join(lines)


def get_future_events(events_data):
    """Filter events to only include today and future dates, sorted ascending."""
    today = datetime.now().strftime("%Y-%m-%d")
    future = [e for e in events_data.get("events", []) if e.get("date", "") >= today]
    future.sort(key=lambda e: (e.get("date", ""), e.get("startTime") or ""))
    return future


def generate_rss(events_data):
    """Generate full RSS 2.0 feed content."""
    build_dt = datetime.now(timezone.utc)
    build_date = formatdate(build_dt.timestamp(), usegmt=True)
    future_events = get_future_events(events_data)
    items = [generate_item(e, build_dt) for e in future_events]

    header = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        "    <title>RVA Figure Drawing</title>",
        f"    <link>{SITE_URL}</link>",
        "    <description>Figure drawing sessions in Richmond, VA</description>",
        "    <language>en-us</language>",
        f"    <lastBuildDate>{build_date}</lastBuildDate>",
        f'    <atom:link href="{FEED_URL}" rel="self" type="application/rss+xml" />',
    ]
    footer = ["  </channel>", "</rss>"]
    return "\n".join(header + items + footer) + "\n"


def main():
    if len(sys.argv) < 3:
        print("Usage: generate-rss.py <events.json> <feed.xml>")
        sys.exit(1)

    events_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not events_path.exists():
        print(f"Error: {events_path} not found")
        sys.exit(1)

    with open(events_path, "r", encoding="utf-8") as f:
        events_data = json.load(f)

    rss_content = generate_rss(events_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rss_content)

    event_count = len(get_future_events(events_data))
    print(f"Generated {output_path} with {event_count} events")


if __name__ == "__main__":
    main()
