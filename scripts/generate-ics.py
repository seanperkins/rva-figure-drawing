#!/usr/bin/env python3
"""
Generate calendar.ics from events.json for calendar subscription.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def escape_ics(text):
    """Escape special characters for ICS format."""
    if not text:
        return ""
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def format_ics_date(date_str, time_str=None):
    """Format date and time for ICS (YYYYMMDDTHHMMSS)."""
    date_part = date_str.replace("-", "")
    if time_str:
        time_part = time_str.replace(":", "") + "00"
    else:
        time_part = "000000"
    return f"{date_part}T{time_part}"


def generate_vevent(event):
    """Generate a VEVENT block for an event."""
    uid = f"{event['date']}-{event.get('startTime', '0000').replace(':', '')}-{event['source']}@rvafiguredrawing"

    dtstart = format_ics_date(event["date"], event.get("startTime"))
    dtend = format_ics_date(event["date"], event.get("endTime") or event.get("startTime"))

    location = event.get("location", "")
    if event.get("address"):
        location = f"{location}, {event['address']}"

    description_parts = [
        event.get("description", ""),
        f"Cost: {event['cost']}" if event.get("cost") else "",
        f"Register: {event['url']}" if event.get("url") else "",
    ]
    description = "\\n\\n".join(part for part in description_parts if part)

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}Z",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{escape_ics(event.get('title', 'Figure Drawing'))}",
        f"LOCATION:{escape_ics(location)}",
        f"DESCRIPTION:{escape_ics(description)}",
    ]

    if event.get("url"):
        lines.append(f"URL:{event['url']}")

    lines.append("END:VEVENT")
    return "\r\n".join(lines)


def get_future_events(events_data):
    """Filter events to only include today and future dates."""
    today = datetime.now().strftime("%Y-%m-%d")
    return [e for e in events_data.get("events", []) if e.get("date", "") >= today]


def generate_ics(events_data):
    """Generate full ICS calendar content."""
    header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//RVA Figure Drawing//Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:RVA Figure Drawing",
        "X-WR-CALDESC:Figure drawing sessions in Richmond, VA",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
    ]

    footer = ["END:VCALENDAR"]

    future_events = get_future_events(events_data)
    vevents = [generate_vevent(event) for event in future_events]

    return "\r\n".join(header + vevents + footer)


def main():
    if len(sys.argv) < 3:
        print("Usage: generate-ics.py <events.json> <calendar.ics>")
        sys.exit(1)

    events_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not events_path.exists():
        print(f"Error: {events_path} not found")
        sys.exit(1)

    with open(events_path, "r", encoding="utf-8") as f:
        events_data = json.load(f)

    ics_content = generate_ics(events_data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ics_content)

    event_count = len(get_future_events(events_data))
    print(f"Generated {output_path} with {event_count} events")


if __name__ == "__main__":
    main()
