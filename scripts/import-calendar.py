#!/usr/bin/env python3
"""
Script to import events from Google Calendar iCal feed and convert to JSON format
"""

import requests
import json
from datetime import datetime, timedelta
from ics import Calendar
import pytz
import os

# Build paths relative to the script's location
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))

# Configuration
ICAL_URL = "https://calendar.google.com/calendar/ical/f81dd042d9553c506027f96a0335662281bfcb7c772ee33f7f5629f6294779e3%40group.calendar.google.com/public/basic.ics"
OUTPUT_FILE = os.path.join(BASE_DIR, "themes/mcp-theme/data/events.json")
TIMEZONE = "America/Phoenix"
DEFAULT_IMAGE = "/images/demo.png"
FETCH_MONTHS = 4

def fetch_ical_data():
    """Fetch iCal data from Google Calendar"""
    print("Fetching calendar data...")
    response = requests.get(ICAL_URL)
    response.raise_for_status()

    # # --- Debugging line added ---
    # with open("debug_calendar.ics", "w", encoding="utf-8") as f:
    #     f.write(response.text)
    # print("Saved raw calendar data to 'scripts/debug_calendar.ics' for inspection.")
    # # --- End of debugging line ---

    return response.text

def parse_and_match_events(ical_data, existing_events):
    """
    Parses iCal data, matches against existing events, and returns new events.
    It also updates existing_events in-place by adding calendarUids where they can be matched.
    """
    print("Parsing and matching calendar events...")
    cal = Calendar(ical_data)
    new_events = []
    
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    future_limit = now + timedelta(days=30 * FETCH_MONTHS)
    
    print("\n--- All Events Found in Calendar Feed (Sorted by Title) ---")
    sorted_events = sorted(cal.events, key=lambda e: e.name or '')
    for event in sorted_events:
        start_dt_raw = event.begin.datetime
        start_dt_str = start_dt_raw.strftime('%Y-%m-%d %H:%M') if hasattr(start_dt_raw, 'strftime') else 'All-day event'
        print(f"  - Found: {event.name} (Starts: {start_dt_str})")
    print("----------------------------------------------------------\n")
    
    print(f"Looking for events between {now.strftime('%Y-%m-%d')} and {future_limit.strftime('%Y-%m-%d')}")
    
    existing_uids = {event.get("calendarUid") for event in existing_events if event.get("calendarUid")}
    print(f"Found {len(existing_uids)} existing events with UIDs.")

    unmatched_cal_events = []

    for event in cal.events:
        if event.uid in existing_uids:
            continue # Already exists, skip
        
        # Check date range
        start_dt = event.begin.datetime
        if start_dt.year == 1970:
            continue # Invalid date
        if start_dt.tzinfo is None:
            start_dt = tz.localize(start_dt)
        else:
            start_dt = start_dt.astimezone(tz)
            
        if not (now <= start_dt <= future_limit):
            continue # Outside our date range
            
        unmatched_cal_events.append(event)

    print(f"Found {len(unmatched_cal_events)} calendar events to process after filtering.")

    # Try to match existing events that are missing a UID
    matched_cal_events_by_uid = set()
    for event_json in existing_events:
        if event_json.get("calendarUid"):
            continue

        for cal_event in unmatched_cal_events:
            if cal_event.uid in matched_cal_events_by_uid:
                continue

            # Fuzzy match based on date, time, and title substring
            start_dt_cal = cal_event.begin.datetime.astimezone(tz)
            
            # Normalize to strings for comparison
            cal_date = start_dt_cal.strftime("%Y-%m-%d")
            cal_time = start_dt_cal.strftime("%H:%M:%S")
            json_time = event_json.get("startTime", "")
            json_title = event_json.get("title", "").lower()
            cal_title = cal_event.name.lower() if cal_event.name else ""

            # More robust time matching: compare only the HH:MM part.
            time_matches = False
            if json_time and len(json_time) >= 5 and len(cal_time) >= 5:
                if json_time[:5] == cal_time[:5]:
                    time_matches = True

            if (event_json.get("startDate") == cal_date and
                time_matches and
                json_title in cal_title):
                
                print(f"  ✓ Matched existing event '{json_title}' to calendar event. Adding UID: {cal_event.uid}")
                event_json["calendarUid"] = cal_event.uid
                matched_cal_events_by_uid.add(cal_event.uid)
                existing_uids.add(cal_event.uid) # Add to set to prevent re-adding as new
                break # Move to next JSON event

    # Add any remaining unmatched calendar events as new events
    print("Identifying truly new events...")
    for cal_event in unmatched_cal_events:
        if cal_event.uid in matched_cal_events_by_uid or cal_event.uid in existing_uids:
            continue
            
        print(f"  + Found new event to add: {cal_event.name}")
        # Process and create a new json_event
        # For all-day events we avoid timezone conversion to preserve the literal calendar date.
        if cal_event.all_day:
            start_dt_raw = cal_event.begin.datetime  # likely naive or at 00:00 UTC
            start_date_str = start_dt_raw.strftime("%Y-%m-%d")

            # For all-day events, iCal DTEND is exclusive; subtract one day to get true end.
            if cal_event.end:
                true_end = cal_event.end.datetime - timedelta(days=1)
            else:
                true_end = start_dt_raw

            end_date_str = true_end.strftime("%Y-%m-%d")

            start_time_str = "00:00"
            end_time_str = "23:59"
        else:
            start_dt = cal_event.begin.datetime.astimezone(tz)
            end_dt = cal_event.end.datetime.astimezone(tz) if cal_event.end else start_dt + timedelta(hours=1)

            start_date_str = start_dt.strftime("%Y-%m-%d")
            end_date_str = end_dt.strftime("%Y-%m-%d")
            start_time_str = start_dt.strftime("%H:%M")
            end_time_str = end_dt.strftime("%H:%M")

        category = "general"
        tags = []
        name_lower = cal_event.name.lower() if cal_event.name else ""
        desc_lower = cal_event.description.lower() if cal_event.description else ""
        
        if any(word in name_lower or word in desc_lower for word in ['protest', 'rally', 'march', 'demonstration']):
            category = "protest"; tags = ["activism", "protest"]
        elif any(word in name_lower or word in desc_lower for word in ['vote', 'voting', 'election', 'registration']):
            category = "civic"; tags = ["voting", "democracy"]
        elif any(word in name_lower or word in desc_lower for word in ['book', 'reading', 'discussion', 'education']):
            category = "education"; tags = ["books", "discussion", "community"]
        elif any(word in name_lower or word in desc_lower for word in ['meeting', 'planning']):
            category = "meeting"; tags = ["planning", "organization"]
            
        location_name = cal_event.location if cal_event.location else "TBD"

        json_event = {
            "id": "event-placeholder-id",
            "calendarUid": cal_event.uid,
            "title": cal_event.name or "Untitled Event",
            "description": cal_event.description or f"Join us for {cal_event.name}",
            "startDate": start_date_str,
            "dayOfWeek": datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%A"),
            "startTime": start_time_str,
            "endDate": end_date_str,
            "endTime": end_time_str,
            "allDay": cal_event.all_day or False,
            "location": {"name": location_name, "address": cal_event.location if cal_event.location else "", "city": "Tucson", "state": "AZ"},
            "organizer": {"name": "Take Action Tucson", "email": "contact@takeactiontucson.org", "phone": "(520) 555-0123"},
            "image": DEFAULT_IMAGE, "category": category, "tags": tags, "cost": "free",
            "registrationRequired": False, "registrationUrl": None, "capacity": None,
            "status": "confirmed", "featured": category in ["protest", "civic"]
        }
        new_events.append(json_event)
        
    print(f"\nFound {len(new_events)} new events to add.")
    return new_events


def load_existing_events(filename):
    """Load existing events from the JSON file."""
    if not os.path.exists(filename):
        print("No existing events file found. Starting fresh.")
        return []
        
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            events = data.get("events", [])
            print(f"Loaded {len(events)} existing events.")
            return events
    except (json.JSONDecodeError, FileNotFoundError):
        print("Could not read or parse existing events file. Starting fresh.")
        return []

def get_next_event_id(existing_events):
    """Get the next available event ID."""
    if not existing_events:
        return 1
    max_id = 0
    for event in existing_events:
        try:
            numeric_id = int(event.get("id", "event-0").split("-")[-1])
            if numeric_id > max_id:
                max_id = numeric_id
        except (ValueError, IndexError):
            continue
    return max_id + 1

def create_json_output(events):
    """Create the JSON output structure"""
    output = {
        "calendar": {
            "name": "Take Action Tucson",
            "lastUpdated": datetime.now().isoformat() + "Z",
            "timezone": TIMEZONE
        },
        "events": events
    }
    
    return output

def save_json_file(data, filename):
    """Save data to JSON file"""
    print(f"Saving {len(data['events'])} total events to {filename}")
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    """Main function"""
    try:
        # Load existing events
        existing_events = load_existing_events(OUTPUT_FILE)

        # Fetch and parse calendar data
        ical_data = fetch_ical_data()
        
        # This function modifies existing_events in place
        new_events = parse_and_match_events(ical_data, existing_events)
        
        if not new_events:
            print("No new events found to add.")
        else:
            print(f"Adding {len(new_events)} new events to the list.")

        # Combine, sort, and assign IDs
        all_events = existing_events + new_events
        all_events.sort(key=lambda x: (x['startDate'], x['startTime']))
        
        next_id = get_next_event_id(existing_events) # Pass original list to get starting ID
        for event in all_events:
            if event.get("id") == "event-placeholder-id":
                event["id"] = f"event-{next_id:03d}"
                next_id += 1

        json_data = create_json_output(all_events)
        
        # Save to file
        save_json_file(json_data, OUTPUT_FILE)
        print("Calendar update completed successfully!")
        
        # Print summary of newly added events
        if new_events:
            print("\nNewly added events:")
            for event in new_events:
                print(f"- {event['startDate']} {event['startTime'][:5]}: {event['title']}")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 