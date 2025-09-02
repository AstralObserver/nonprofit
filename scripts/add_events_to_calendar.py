#!/usr/bin/env python3
"""
Script to add events from CSV to Take Action Tucson's Google Calendar
Usage: python add_events_to_calendar.py [--file events.csv]

Requirements:
- google-auth
- google-auth-oauthlib
- google-api-python-client
- pandas

Install with: pip install google-auth google-auth-oauthlib google-api-python-client pandas
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Google Calendar API settings
SCOPES = ['https://www.googleapis.com/auth/calendar']
CALENDAR_ID = '8d4036a00ad9265a9e585749fed4f2c2ecebad265c42789dbb1f9f5042191859@group.calendar.google.com'
TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json'  # OAuth client ID credentials

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Add events from CSV to Google Calendar')
    parser.add_argument('--file', default='events.csv', help='CSV file containing events data')
    parser.add_argument('--dry-run', action='store_true', help='Print event data without adding to calendar')
    return parser.parse_args()

def get_credentials():
    """Get valid user credentials for Google Calendar API."""
    creds = None
    
    # Try to load credentials from token file
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Check if credentials are valid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If no valid credentials, go through OAuth flow
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found!")
                print("Please download OAuth 2.0 Client ID credentials from Google Cloud Console")
                print("and save as credentials.json in the same directory as this script.")
                sys.exit(1)
                
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def create_event(row, timezone='America/Phoenix'):
    """Create a Google Calendar event from a CSV row."""
    # Format datetime strings
    start_datetime = f"{row['start_date']}T{row['start_time']}:00"
    end_datetime = f"{row['end_date']}T{row['end_time']}:00"
    
    # Create event object
    event = {
        'summary': row['summary'],
        'location': row['location'],
        'description': f"Organizer: {row['organizer']}",
        'start': {
            'dateTime': start_datetime,
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end_datetime,
            'timeZone': timezone,
        },
    }
    
    return event

def add_events_to_calendar(events, dry_run=False):
    """Add events to Google Calendar."""
    if dry_run:
        print("DRY RUN - Events will not be added to calendar")
        for event in events:
            print(f"Event: {event['summary']}")
            print(f"  Start: {event['start']['dateTime']}")
            print(f"  End: {event['end']['dateTime']}")
            print(f"  Location: {event['location']}")
            print(f"  Description: {event['description']}")
            print("---")
        return
    
    # Get credentials and build service
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    # Add each event
    for event in events:
        try:
            created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            print(f"Event created: {event['summary']} ({created_event['htmlLink']})")
        except Exception as e:
            print(f"Error creating event {event['summary']}: {e}")

def main():
    """Main function."""
    args = parse_arguments()
    
    # Check if file exists
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found!")
        sys.exit(1)
    
    # Read CSV file
    try:
        df = pd.read_csv(args.file)
        print(f"Found {len(df)} events in {args.file}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    # Check required columns
    required_columns = ['summary', 'start_date', 'start_time', 'end_date', 'end_time', 'location', 'organizer']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: CSV file is missing required columns: {', '.join(missing_columns)}")
        sys.exit(1)
    
    # Create events
    events = [create_event(row) for _, row in df.iterrows()]
    
    # Add events to calendar
    add_events_to_calendar(events, args.dry_run)
    
    print("Done!")

if __name__ == "__main__":
    main()
