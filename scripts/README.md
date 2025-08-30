# Take Action Tucson Calendar Tools

This directory contains Python tools to manage the events displayed on the Take Action Tucson website and to interact with the source Google Calendar.

There are three main workflows supported by these scripts:

1.  **Updating the Website from Google Calendar**
2.  **Manually Editing Website Events**
3.  **Adding Events to Google Calendar from a CSV File**

---

## 1. Updating the Website from Google Calendar

This workflow fetches the latest events from the public Take Action Tucson Google Calendar and updates the website's data files.

-   **Primary Script:** `import-calendar.py`
-   **Helper Script:** `update-calendar.sh`

### Usage

The easiest way to update the website is to run the helper script from the **project root directory**:

```bash
./scripts/update-calendar.sh
```

This script will automatically:
1.  Check for and install required Python packages (`requests`, `ics`, `pytz`).
2.  Run `import-calendar.py` to fetch calendar data.
3.  The script merges new events from the calendar with existing events stored in `themes/mcp-theme/static/data/events.json`, preserving manual edits and matching existing events to avoid duplicates.

---

## 2. Manually Editing Website Events

This workflow allows for detailed editing of the event data used by the website, including adding images, correcting details, and managing event properties.

-   **Primary Script:** `event_editor_gui.py`

### Usage

Run the script directly from the `scripts` directory:

```bash
python event_editor_gui.py
```

This will launch a graphical user interface (GUI) that allows you to:
-   Navigate through all events currently in `events.json`.
-   Edit fields like title, description, time, and location.
-   Add or change an event's image by dragging-and-dropping a file or using the file selector.
-   Save all changes back to the `events.json` file.

### Prerequisites

You must have the required Python packages installed. You can install them with:

```bash
pip install -r requirements.txt
```

---

## 3. Adding Events to Google Calendar from a CSV File

This workflow is for populating the Google Calendar itself by uploading events from a structured CSV file. This is useful for bulk additions.

-   **Primary Script:** `add_events_to_calendar.py`
-   **Helper Script:** `add_events.sh`
-   **Data File:** `events.csv`

### Usage

1.  **Fill out `events.csv`**: Add your event details to the `events.csv` file in the `scripts` directory.
2.  **Set up Credentials**: You must have a `credentials.json` file in the `scripts` directory. This is an OAuth 2.0 Client ID file you can get from your Google Cloud Console.
3.  **Run the script**: Execute the helper script from within the `scripts` directory.

    ```bash
    ./add_events.sh
    ```
    The script will guide you through the Google authentication process the first time you run it.

### Prerequisites

This workflow requires Google API client libraries. Install them using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Event CSV Format

The CSV file must have the following columns:
- `summary`: Event title (in ALL CAPS for consistency)
- `start_date`: Start date in YYYY-MM-DD format
- `start_time`: Start time in HH:MM format (24-hour)
- `end_date`: End date in YYYY-MM-DD format
- `end_time`: End time in HH:MM format (24-hour)
- `location`: Event location
- `organizer`: Event organizer name(s)

## Workflow for Calendar Updates

1. Update `events.csv` with new events
2. Add the events to Google Calendar using Google Apps Script
3. Generate the static calendar page with `update_calendar.sh`
4. Deploy the updated site
