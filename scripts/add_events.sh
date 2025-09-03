#!/bin/bash

# Change to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if required packages are installed
if ! python3 -c "import google, pandas" &> /dev/null; then
    echo "Installing required packages..."
    pip install google-auth google-auth-oauthlib google-api-python-client pandas
fi

# Check if credentials file exists
if [ ! -f "credentials.json" ]; then
    echo "ERROR: credentials.json file not found!"
    echo "Please download OAuth 2.0 Client ID credentials from Google Cloud Console"
    echo "and save as credentials.json in the same directory as this script."
    exit 1
fi

# Run the script
echo "Adding events to CIA calendar..."
python3 add_events_to_calendar.py "$@"
