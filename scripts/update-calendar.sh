#!/bin/bash
# Script to update calendar events from Google Calendar

echo "Updating Take Action Tucson calendar events..."

# Check if we're in the right directory
if [ ! -f "scripts/import-calendar.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Check if Python dependencies are installed
echo "Checking Python dependencies..."
python3 -c "import requests, icalendar, pytz" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Python dependencies..."
    pip3 install -r scripts/requirements.txt
fi

# Run the import script
echo "Fetching events from Google Calendar..."
cd scripts
python3 import-calendar.py
cd ..

echo "Calendar update complete!"
echo "You can now refresh your Hugo site to see the latest events." 