import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import shutil
from pathlib import Path
import tkinterdnd2 as tkdnd
from PIL import Image, ImageTk # For image previews
import sys
import subprocess
from datetime import datetime
import copy
import threading
import requests

class EventEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Take Action Tucson - Event Editor")
        self.root.geometry("1150x900")

        # Define file paths
        self.base_path = Path(__file__).resolve().parent.parent
        self.json_path = self.base_path / "themes/mcp-theme/data/events.json"
        self.completed_json_path = self.base_path / "themes/mcp-theme/data/completed_events.json"
        self.image_dir = self.base_path / "themes/mcp-theme/assets/images"

        # Form fields definition
        self.form_fields = [
            ("ID", "id", False),
            ("Calendar UID", "calendarUid", False),
            ("Title", "title", True),
            ("Description", "description", True, 5),
            ("Start Date", "startDate", True),
            ("Day of Week", "dayOfWeek", False),
            ("Start Time", "startTime", True),
            ("End Date", "endDate", True),
            ("End Time", "endTime", True),
            ("Location Name", "location.name", True),
            ("Location Address", "location.address", True),
            ("Organizer", "organizer.name", True),
            ("Organizer Email", "organizer.email", True),
            ("Organizer Website", "organizer.website", True)
        ]
        
        # Load data
        self.events = []
        self.organizers = {}
        self.current_event_index = 0
        self.event_listbox = None # For the new event list
        self.is_programmatic_selection = False # Flag to prevent event loops
        self.load_events()

        # Create UI
        self.create_widgets()

        # Display first event
        if self.events:
            self.populate_event_listbox()
            self.display_event()
        else:
            messagebox.showinfo("No Events", f"No events found in {self.json_path}. Please run the import script or create a new event.")

    def load_events(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.events = data.get("events", [])
                self.extract_organizers()
                self.sort_events() # Sort on initial load
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error Loading File", f"Could not load or parse events.json:\n{e}")
            self.events = []
            self.organizers = {}

    def save_events(self):
        if not self.events:
            messagebox.showwarning("No Events", "There is nothing to save.")
            return

        # First, apply the currently displayed data
        self.apply_changes()

        output_data = {
            "calendar": {
                "name": "Take Action Tucson Events",
                "lastUpdated": self.get_current_iso_time(),
            },
            "events": self.events,
        }

        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", "events.json has been saved successfully!")
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Could not save events.json:\n{e}")

    def extract_organizers(self):
        self.organizers = {}
        for event in self.events:
            organizer = event.get("organizer")
            if organizer and isinstance(organizer, dict) and "name" in organizer:
                name = organizer.get("name", "").strip()
                if name and name not in self.organizers:
                    self.organizers[name] = {
                        "name": name,
                        "email": organizer.get("email", ""),
                        "website": organizer.get("website", "")
                    }

    def create_widgets(self):
        # --- Main Layout ---
        main_container = ttk.Frame(self.root, padding="5")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left frame for the main editor form
        editor_frame = ttk.Frame(main_container)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right frame for the event list
        list_frame = ttk.LabelFrame(main_container, text="Events", padding=(5, 10))
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        
        # --- Event Listbox ---
        self.event_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, exportselection=False, width=40)
        self.event_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.event_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.event_listbox.config(yscrollcommand=list_scrollbar.set)
        
        self.event_listbox.bind('<<ListboxSelect>>', self.on_listbox_select)

        # --- Navigation (always visible above tabs) ---
        nav_frame = ttk.Frame(editor_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.prev_button = ttk.Button(nav_frame, text="<< Previous", command=self.prev_event)
        self.prev_button.pack(side=tk.LEFT)
        
        self.nav_label = ttk.Label(nav_frame, text="Event 1 of 1", anchor=tk.CENTER)
        self.nav_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.next_button = ttk.Button(nav_frame, text="Next >>", command=self.next_event)
        self.next_button.pack(side=tk.RIGHT)
        
        # --- Notebook Setup ---
        notebook = ttk.Notebook(editor_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        details_tab = ttk.Frame(notebook)
        desc_tab = ttk.Frame(notebook)
        notebook.add(details_tab, text="Details")
        notebook.add(desc_tab, text="Description")

        # --- Details Tab Content ---
        form_frame = ttk.LabelFrame(details_tab, text="Event Details", padding="5")
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Allow the last few columns to stretch when the window is resized
        for col in range(4):
            form_frame.columnconfigure(col, weight=1)

        # Store widget references here so other methods can access them
        self.fields = {}

        # We will handle the Date and Time related widgets manually so they can
        # reside on single rows. Skip them in the generic loop below.
        skip_for_custom_layout = {"startDate", "endDate", "startTime", "endTime", "description"}

        # Build the standard fields first (everything except the ones we will
        # place manually).
        row_index = 0
        for label, key, is_editable, *span in self.form_fields:
            if key in skip_for_custom_layout:
                continue  # Handle later

            ttk.Label(form_frame, text=label).grid(row=row_index, column=0, sticky=tk.W, pady=2)

            if "description" in key:
                # Description will live in separate tab; skip here
                continue
            else:
                widget = ttk.Entry(form_frame)

                # Special handling for Start Date so we can set up a StringVar
                if key == "startDate":
                    # NOTE: Start Date entry is now created later in the custom layout.
                    pass

                # If this is the location.address row, add a Validate button
                if key == "location.address":
                    widget.grid(row=row_index, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
                    validate_btn = ttk.Button(form_frame, text="Validate", width=9,
                                              command=self.validate_address)
                    validate_btn.grid(row=row_index, column=3, sticky=tk.W, padx=(5, 0), pady=2)
                    # Store reference for progress indication
                    self._validate_btn = validate_btn
                # Organizer name narrow etc
                elif key == "organizer.name":
                    widget.grid(row=row_index, column=1, sticky=(tk.W, tk.E), pady=2)
                else:
                    widget.grid(row=row_index, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2)

            # Save reference
            self.fields[key] = widget

            # Comboboxes and icon labels (for organizer) need to align with the new columns → keep same behaviour.
            if key == 'organizer.name':
                self.organizer_combobox = ttk.Combobox(form_frame, state="readonly", width=25)
                self.organizer_combobox.grid(row=row_index, column=2, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=2)
                self.organizer_combobox.bind("<<ComboboxSelected>>", self.on_organizer_selected)

                organizer_names = sorted([name for name in self.organizers.keys() if name])
                self.organizer_combobox['values'] = organizer_names

            # Icons for email/website have been removed per user request.

            # Read-only handling
            if not is_editable:
                if isinstance(widget, ttk.Entry):
                    widget.config(state="readonly")
                else:
                    widget.config(state="disabled")

            row_index += 1

        # ---------- Custom Date Row (Start Date | End Date) ----------
        ttk.Label(form_frame, text="Start Date").grid(row=row_index, column=0, sticky=tk.W, pady=2)

        self.start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(form_frame, textvariable=self.start_date_var)
        self.start_date_var.trace_add("write", self.update_day_of_week)
        start_date_entry.grid(row=row_index, column=1, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(form_frame, text="End Date", anchor="e").grid(row=row_index, column=2, sticky=tk.E, padx=(5,0), pady=1)
        end_date_entry = ttk.Entry(form_frame)
        end_date_entry.grid(row=row_index, column=3, sticky=(tk.W, tk.E), pady=2)

        # Save references so other methods work unchanged
        self.fields["startDate"] = start_date_entry
        self.fields["endDate"] = end_date_entry

        row_index += 1

        # ---------- Custom Time Row (All Day ▢ | Start Time | End Time) ----------
        # All-day field is not part of the original fields dict, so we manage it separately.
        self.all_day_var = tk.BooleanVar(value=False)
        all_day_cb = ttk.Checkbutton(form_frame, text="All Day", variable=self.all_day_var,
                                     command=self.on_all_day_toggle)
        all_day_cb.grid(row=row_index, column=0, sticky=tk.W, pady=2)

        start_time_entry = ttk.Entry(form_frame)
        start_time_entry.grid(row=row_index, column=1, sticky=(tk.W, tk.E), pady=2)

        end_time_entry = ttk.Entry(form_frame)
        end_time_entry.grid(row=row_index, column=2, sticky=(tk.W, tk.E), pady=2)

        # Make column 3 span optional to keep layout neat.
        form_frame.grid_columnconfigure(3, weight=0)

        self.fields["startTime"] = start_time_entry
        self.fields["endTime"] = end_time_entry

        # ---------- Event Type / Category Controls ----------
        row_index += 1

        type_controls_frame = ttk.Frame(form_frame)
        type_controls_frame.grid(row=row_index, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=3)

        # --- Event Type Checkboxes ---
        self.event_type_vars = {}
        event_type_frame = ttk.LabelFrame(type_controls_frame, text="Event Categories", padding=(5, 3))
        event_type_frame.pack(side=tk.LEFT, fill=tk.Y)

        event_types = ["In-Person", "Virtual", "Demonstrations"]
        for event_type in event_types:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(event_type_frame, text=event_type, variable=var)
            cb.pack(side=tk.LEFT, padx=10, pady=3)
            self.event_type_vars[event_type] = var

        # Keep a reference to the custom time entries for enable/disable toggle
        self._start_time_entry = start_time_entry
        self._end_time_entry = end_time_entry

        # Ensure initial state is correct
        self.on_all_day_toggle()

        # --- Image Section ---
        image_frame = ttk.LabelFrame(details_tab, text="Event Image", padding="5")
        image_frame.pack(fill=tk.X, pady=5)
        
        # Create a canvas for image preview and drop zone
        self.image_canvas = tk.Canvas(image_frame, height=150, bg="#f0f0f0", relief="sunken", borderwidth=1)
        self.image_canvas.pack(pady=3, padx=3, fill=tk.X, expand=True)
        
        self.canvas_text_id = None # To hold the ID of the text on the canvas
        self.photo_image = None # To hold a reference to the PhotoImage to prevent garbage collection
        
        # Bind drag and drop events to the canvas
        self.image_canvas.drop_target_register(tkdnd.DND_FILES)
        self.image_canvas.dnd_bind('<<Drop>>', self.handle_drop)
        self.image_canvas.bind('<Button-1>', lambda e: self.select_image())

        path_label_frame = ttk.Frame(image_frame)
        path_label_frame.pack(fill=tk.X, expand=True, pady=(3,0))

        self.image_path_var = tk.StringVar(value="No image selected.")
        ttk.Label(path_label_frame, textvariable=self.image_path_var, foreground="grey").pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.select_image_button = ttk.Button(path_label_frame, text="Select Image...", command=self.select_image)
        self.select_image_button.pack(side=tk.RIGHT, padx=(5,0))
        self.new_image_path = None # To store path of newly selected image

        # --- Actions (visible in all tabs) ---
        action_frame = ttk.Frame(editor_frame)
        action_frame.pack(fill=tk.X, pady=(5, 0))

        self.new_event_button = ttk.Button(action_frame, text="New Event", command=self.add_new_event)
        self.new_event_button.pack(side=tk.LEFT, padx=(0, 5))

        self.duplicate_event_button = ttk.Button(action_frame, text="Duplicate Event", command=self.duplicate_event)
        self.duplicate_event_button.pack(side=tk.LEFT, padx=(0, 5))

        self.delete_event_button = ttk.Button(action_frame, text="Delete Event", command=self.delete_event)
        self.delete_event_button.pack(side=tk.LEFT, padx=(0, 5))

        self.archive_button = ttk.Button(action_frame, text="Archive Past Events", command=self.archive_past_events)
        self.archive_button.pack(side=tk.LEFT, padx=(0, 5))

        if sys.platform in ["linux", "darwin"]:
            self.update_button = ttk.Button(action_frame, text="Update from Calendar", command=self.run_update_script)
            self.update_button.pack(side=tk.LEFT)

        self.save_button = ttk.Button(action_frame, text="Save All Events", command=self.save_events)
        self.save_button.pack(side=tk.RIGHT)

        # ---------------- Description Tab -----------------
        self.description_text = tk.Text(desc_tab, wrap=tk.WORD)
        self.description_text.pack(fill=tk.BOTH, expand=True)

        # --- Button row specific to Description tab ---
        desc_button_frame = ttk.Frame(desc_tab)
        desc_button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        link_btn = ttk.Button(desc_button_frame, text="Link", command=self.insert_weblink_template)
        link_btn.pack(side=tk.LEFT, padx=5, pady=3)

        cr_btn = ttk.Button(desc_button_frame, text="<p>", width=3, command=self.insert_paragraph_break)
        cr_btn.pack(side=tk.LEFT, padx=(0, 5), pady=3)

        # Include description field in self.fields mapping
        self.fields["description"] = self.description_text

        # Bind tab change event to sync description
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def display_event(self):
        if not self.events:
            self.nav_label.config(text="No events loaded.")
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")
            self.clear_form()
            return
            
        event = self.events[self.current_event_index]
        self.nav_label.config(text=f"Event {self.current_event_index + 1} of {len(self.events)}")

        self.organizer_combobox.set('') # Reset combobox
        
        # Create a map for faster lookup of field properties
        is_editable_map = {key: is_editable for _, key, is_editable, *_ in self.form_fields}
        
        # Set new classification controls
        current_types = event.get("eventType", [])
        if isinstance(current_types, str):
            current_types = [current_types] if current_types else []
            
        for type_name, var in self.event_type_vars.items():
            var.set(type_name in current_types)

        self.get_in_dict(event, 'location', {}) # Ensure location sub-dict exists
        self.get_in_dict(event, 'organizer', {}) # Ensure organizer sub-dict exists

        # Sync All-Day first so the time widgets have the right enabled state
        self.all_day_var.set(bool(event.get("allDay", False)))
        self.on_all_day_toggle()

        for key, widget in self.fields.items():
            value = self.get_in_dict(event, key)
            is_editable = is_editable_map.get(key, True)

            # Reset any validation colors when loading a new event
            if key == "location.address" and isinstance(widget, ttk.Entry):
                widget.config(style="TEntry")  # Reset to default ttk style

            if isinstance(widget, ttk.Entry):
                # Manage widget state
                intended_state = "normal" if is_editable else "readonly"
                widget.config(state="normal") # Must be normal to change

                if key == 'startDate':
                    self.start_date_var.set(str(value) if value is not None else "")
                else:
                    # Normalize time for display if this is a time field
                    if key in ("startTime", "endTime") and isinstance(value, str):
                        value = self._normalize_time(value)
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value) if value is not None else "")
                
                widget.config(state=intended_state) # Restore intended state
            elif isinstance(widget, tk.Text):
                intended_state = "normal" if is_editable else "disabled"
                widget.config(state="normal")
                widget.delete("1.0", tk.END)
                widget.insert("1.0", str(value) if value is not None else "")
                widget.config(state=intended_state)

        # --- Day of Week Validation ---
        stored_day = self.get_in_dict(event, 'dayOfWeek', '')
        start_date_str = self.get_in_dict(event, 'startDate', '')
        correct_day = ""

        if start_date_str:
            try:
                dt = datetime.strptime(start_date_str, '%Y-%m-%d')
                correct_day = dt.strftime('%A')
            except ValueError:
                correct_day = "" # Invalid date format

        # Case-insensitive comparison, ignoring whitespace
        if correct_day and stored_day.strip().lower() != correct_day.lower():
            proceed = messagebox.askyesno(
                "Correct Day of Week?",
                f"The stored day of week ('{stored_day}') does not match the calculated day for that date ('{correct_day}').\n\n"
                f"Would you like to correct it to '{correct_day}'?"
            )
            if proceed:
                # Update the UI widget
                day_of_week_widget = self.fields.get("dayOfWeek")
                if day_of_week_widget:
                    day_of_week_widget.config(state="normal")
                    day_of_week_widget.delete(0, tk.END)
                    day_of_week_widget.insert(0, correct_day)
                    day_of_week_widget.config(state="readonly")
                
                # Update the underlying event data in memory so it gets saved
                self.set_in_dict(event, 'dayOfWeek', correct_day)

        # --- End Date Validation ---
        start_date_str = self.get_in_dict(event, 'startDate', '')
        end_date_str = self.get_in_dict(event, 'endDate', '')

        if start_date_str and end_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')

                if end_dt < start_dt:
                    proceed = messagebox.askyesno(
                        "Correct End Date?",
                        f"The event's end date ({end_date_str}) is before its start date ({start_date_str}).\n\n"
                        f"Would you like to set the end date to be the same as the start date?"
                    )
                    if proceed:
                        # Update UI widget for endDate
                        end_date_widget = self.fields.get("endDate")
                        if end_date_widget:
                            end_date_widget.delete(0, tk.END)
                            end_date_widget.insert(0, start_date_str)

                        # Update the underlying event data
                        self.set_in_dict(event, 'endDate', start_date_str)

            except ValueError:
                # Silently ignore if dates are malformed
                pass

        # Handle image display
        self.new_image_path = None
        current_image = event.get("image")
        self.image_path_var.set(current_image or "No image selected.")

        full_image_path = None
        if current_image:
            # image paths are like '/images/foo.jpg'. We need to find them in the assets directory.
            relative_image_path = current_image.lstrip('/')
            assets_dir = self.base_path / "themes/mcp-theme/assets"
            full_image_path = assets_dir / relative_image_path
        
        self._load_and_display_image(full_image_path)

        # Update button states
        num_events = len(self.events)
        if num_events > 1:
            self.prev_button.config(state="normal")
            self.next_button.config(state="normal")
        else:
            self.prev_button.config(state="disabled")
            self.next_button.config(state="disabled")

        # Update selection in the listbox
        if self.event_listbox and self.event_listbox.size() > self.current_event_index:
            self.is_programmatic_selection = True
            self.event_listbox.selection_clear(0, tk.END)
            self.event_listbox.selection_set(self.current_event_index)
            self.event_listbox.activate(self.current_event_index)
            self.event_listbox.see(self.current_event_index)
            self.is_programmatic_selection = False

    def on_organizer_selected(self, event=None):
        selected_name = self.organizer_combobox.get()
        if selected_name in self.organizers:
            organizer_data = self.organizers[selected_name]
            
            name_widget = self.fields.get("organizer.name")
            email_widget = self.fields.get("organizer.email")
            website_widget = self.fields.get("organizer.website")

            if name_widget and isinstance(name_widget, ttk.Entry):
                name_widget.delete(0, tk.END)
                name_widget.insert(0, organizer_data.get("name", ""))
            
            if email_widget and isinstance(email_widget, ttk.Entry):
                email_widget.delete(0, tk.END)
                email_widget.insert(0, organizer_data.get("email", ""))
            
            if website_widget and isinstance(website_widget, ttk.Entry):
                website_widget.delete(0, tk.END)
                website_widget.insert(0, organizer_data.get("website", ""))

    def apply_changes(self):
        """Saves the data from the form back to the current event in memory."""
        if not self.events: return
        
        # First sync description from large text box if it exists
        if hasattr(self, 'description_text') and self.description_text:
            desc_content = self.description_text.get("1.0", tk.END).strip()
            self.events[self.current_event_index]["description"] = desc_content

        event = self.events[self.current_event_index]

        old_date = event.get('startDate')
        old_time = event.get('startTime')
        old_title = event.get('title')
        current_id = event.get('id')

        for key, widget in self.fields.items():
            if isinstance(widget, ttk.Entry):
                value = widget.get()
                # Normalize time when saving
                if key in ("startTime", "endTime"):
                    value = self._normalize_time(value)
            elif isinstance(widget, tk.Text):
                value = widget.get("1.0", tk.END).strip()
            self.set_in_dict(event, key, value)
        
        # Save the All-Day flag
        event["allDay"] = self.all_day_var.get()

        # Save new classification fields
        selected_types = [type_name for type_name, var in self.event_type_vars.items() if var.get()]
        event["eventType"] = selected_types

        # Handle image update
        if self.new_image_path:
            event_id = event.get('id', f"event_{self.get_current_iso_time()}")
            ext = Path(self.new_image_path).suffix
            new_filename = f"{event_id}{ext}"
            dest_path = self.image_dir / new_filename
            
            try:
                # Ensure the destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(self.new_image_path, dest_path)
                event['image'] = f"/images/{new_filename}"
                self.image_path_var.set(event['image'])
                self.new_image_path = None # Reset after copy
                print(f"Image copied to {dest_path}")
            except Exception as e:
                messagebox.showerror("Image Copy Error", f"Could not copy image:\n{e}")

        # Check if a value affecting sort order has changed
        new_date = event.get('startDate')
        new_time = event.get('startTime')
        new_title = event.get('title')
        
        if old_date != new_date or old_time != new_time or old_title != new_title:
            self.sort_events(keep_selection_id=current_id)
        else:
            # Update listbox entry to reflect changes if not re-sorting
            if self.event_listbox and self.events:
                idx = self.current_event_index
                event_data = self.events[idx]
                date = event_data.get('startDate', 'No Date')
                title = event_data.get('title', 'Untitled Event')

                self.is_programmatic_selection = True
                self.event_listbox.delete(idx)
                self.event_listbox.insert(idx, f"{date} - {title}")
                self.event_listbox.selection_set(idx)
                self.is_programmatic_selection = False

    def next_event(self):
        self.apply_changes()  # Save current event before navigating
        if not self.events:
            return
        num_events = len(self.events)
        self.current_event_index = (self.current_event_index + 1) % num_events
        self.display_event()

    def prev_event(self):
        self.apply_changes()  # Save current event before navigating
        if not self.events:
            return
        num_events = len(self.events)
        self.current_event_index = (self.current_event_index - 1 + num_events) % num_events
        self.display_event()
    
    def _load_and_display_image(self, image_path):
        """Loads, resizes, and displays an image on the canvas."""
        self.image_canvas.delete("all")
        self.photo_image = None # Clear old image reference

        try:
            # Get actual canvas dimensions after UI updates
            self.image_canvas.update_idletasks()
            canvas_w = self.image_canvas.winfo_width()
            canvas_h = self.image_canvas.winfo_height()

            if not image_path or not Path(image_path).exists():
                self.image_canvas.create_text(
                    canvas_w / 2, canvas_h / 2,
                    text="Drag and drop an image here\nor click to select",
                    font=("", 12, "italic"), fill="grey", justify=tk.CENTER, anchor="center"
                )
                if image_path:
                    self.image_path_var.set(f"Not Found: {Path(image_path).name}")
                return

            # Open image with Pillow
            with Image.open(image_path) as img:
                # Resize image to fit canvas while maintaining aspect ratio
                img.thumbnail((canvas_w - 10, canvas_h - 10), Image.Resampling.LANCZOS)
                
                # Create Tkinter-compatible image and keep a reference
                self.photo_image = ImageTk.PhotoImage(img)
                
                # Display image on canvas
                self.image_canvas.create_image(canvas_w / 2, canvas_h / 2, image=self.photo_image, anchor="center")

        except Exception as e:
            self.image_canvas.delete("all")
            self.canvas_text_id = self.image_canvas.create_text(
                canvas_w / 2, canvas_h / 2,
                text=f"Error loading image:\n{Path(image_path).name}",
                font=("", 10), fill="red", justify=tk.CENTER, anchor="center"
            )
            messagebox.showerror("Image Error", f"Could not display image: {image_path}\n\nMake sure Pillow is installed (pip install Pillow).\n\nError: {e}")

    def select_image(self):
        filepath = filedialog.askopenfilename(
            title="Select an Event Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.gif"), ("All Files", "*.*")]
        )
        if filepath:
            self.new_image_path = filepath
            self.image_path_var.set(f"NEW: {Path(filepath).name}")
            self._load_and_display_image(filepath)

    def get_current_iso_time(self):
        return datetime.now().isoformat() + "Z"

    def handle_drop(self, event):
        """Handle dropped files"""
        filepath = event.data
        # Remove curly braces if present (Windows file paths)
        filepath = filepath.strip('{}')
        if filepath:
            self.new_image_path = filepath
            self.image_path_var.set(f"NEW: {Path(filepath).name}")
            self._load_and_display_image(filepath)

    def run_update_script(self):
        """Runs the update-calendar.sh script."""
        script_path = self.base_path / 'scripts' / 'update-calendar.sh'
        if not script_path.exists():
            messagebox.showerror("Script Not Found", f"The script was not found at:\n{script_path}")
            return

        if not os.access(script_path, os.X_OK):
            messagebox.showwarning("Permission Denied", "The update script is not executable.\nAttempting to set permissions...")
            try:
                # Add execute permission for the user (chmod u+x)
                os.chmod(script_path, os.stat(script_path).st_mode | 0o100)
            except Exception as e:
                messagebox.showerror("Permission Error", f"Could not make script executable:\n{e}")
                return

        proceed = messagebox.askyesno(
            "Confirm Update",
            "This will fetch the latest events from Google Calendar, overwriting local data.\n\n"
            "It is highly recommended you save any changes first.\n\n"
            "Do you want to continue?"
        )
        if not proceed:
            return

        progress_window = tk.Toplevel(self.root)
        progress_window.title("Updating...")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        ttk.Label(progress_window, text="Running update script, please wait...").pack(pady=20, padx=20)
        self.root.update_idletasks()

        try:
            result = subprocess.run(
                [str(script_path)],
                cwd=self.base_path,
                capture_output=True,
                text=True,
                check=False
            )
        finally:
            progress_window.destroy()

        if result.returncode == 0:
            reload = messagebox.askyesno(
                "Success!",
                "Calendar update completed successfully.\n\nDo you want to reload the events in the editor now?\n(Any unsaved changes will be lost)"
            )
            if reload:
                self.current_event_index = 0
                self.load_events()
                self.display_event()
        else:
            error_details = result.stderr or result.stdout or "No output from script."
            messagebox.showerror("Update Failed", f"The calendar update script failed (code {result.returncode}):\n\n{error_details}")

    def add_new_event(self):
        """Creates a new, blank event and displays it for editing."""
        if self.events:
            self.apply_changes()

        new_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        today_str = datetime.now().strftime('%Y-%m-%d')
        day_of_week = datetime.now().strftime('%A')

        new_event = {
            "id": new_id,
            "calendarUid": "",
            "title": "New Event Title",
            "description": "",
            "startDate": today_str,
            "dayOfWeek": day_of_week,
            "startTime": "TBD",
            "endDate": today_str,
            "endTime": "TBD",
            "allDay": False,
            "location": {"name": "", "address": ""},
            "organizer": {"name": "", "email": "", "website": ""},
            "eventType": [],
            "image": ""
        }

        self.events.append(new_event)
        self.current_event_index = len(self.events) - 1
        self.populate_event_listbox()
        self.display_event()

        messagebox.showinfo(
            "New Event Created",
            "A new event has been created. Fill in the details and remember to save."
        )

        self.fields["title"].focus_set()
        self.fields["title"].select_range(0, tk.END)

    def delete_event(self):
        """Deletes the current event, moves it to the archive, and removes it from the editor."""
        if not self.events:
            messagebox.showwarning("No Event", "There is no event to delete.")
            return

        event_to_delete = self.events[self.current_event_index]
        title = event_to_delete.get('title', 'this event')

        proceed = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{title}'?\n\n"
            "This will move the event to the archive and remove it from the main calendar. "
            "This action cannot be undone from the editor."
        )
        if not proceed:
            return

        # Move to archive
        if self._add_events_to_archive([event_to_delete]):
            # Remove from main list
            del self.events[self.current_event_index]

            # If we deleted the last event, clamp index to the new last event
            if self.current_event_index >= len(self.events) and self.events:
                self.current_event_index = len(self.events) - 1

            self.sort_events()  # Re-sort and repopulate listbox
            self.display_event()  # Display new current event or clear form

            messagebox.showinfo(
                "Event Deleted",
                f"'{title}' has been deleted and moved to the archive.\n\n"
                "IMPORTANT: Click 'Save All Events' to make the removal from the main calendar permanent."
            )
        else:
            messagebox.showerror("Delete Error", "Failed to move the event to the archive. Deletion was cancelled.")

    def duplicate_event(self):
        """Duplicates the current event, gives it a new ID, and displays it."""
        if not self.events:
            messagebox.showwarning("No Event", "There is no event to duplicate.")
            return

        self.apply_changes()

        current_event = self.events[self.current_event_index]
        new_event = copy.deepcopy(current_event)

        new_id = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        new_event['id'] = new_id

        self.events.append(new_event)
        
        # Sort and select the new one
        self.sort_events(keep_selection_id=new_id)
        
        self.display_event()

        messagebox.showinfo(
            "Event Duplicated",
            "The event has been duplicated. Remember to adjust the date and save."
        )

    def update_day_of_week(self, *args):
        """Callback to update the Day of Week field when startDate changes."""
        date_str = self.start_date_var.get()
        day_of_week_widget = self.fields.get("dayOfWeek")
        day_of_week = ""

        if date_str:
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                day_of_week = dt.strftime('%A')
            except ValueError:
                pass
        
        if day_of_week_widget:
            day_of_week_widget.config(state="normal")
            day_of_week_widget.delete(0, tk.END)
            day_of_week_widget.insert(0, day_of_week)
            day_of_week_widget.config(state="readonly")

    def on_all_day_toggle(self):
        """Enable/disable the Start/End Time fields when the All Day box is toggled."""
        state = "disabled" if self.all_day_var.get() else "normal"
        if hasattr(self, "_start_time_entry") and hasattr(self, "_end_time_entry"):
            self._start_time_entry.config(state=state)
            self._end_time_entry.config(state=state)

    def archive_past_events(self):
        """Finds events from yesterday or earlier, moves them to a separate JSON file,
        and removes them from the main event list in the editor."""

        if not self.events:
            messagebox.showinfo("No Events", "There are no events to archive.")
            return

        proceed = messagebox.askyesno(
            "Confirm Archive",
            "This will move all events dated yesterday or earlier into 'completed_events.json' "
            "and remove them from the editor.\n\n"
            "You must click 'Save All Events' afterwards to make this change permanent.\n\n"
            "Continue?"
        )
        if not proceed:
            return

        today = datetime.now().date()
        past_events = []
        upcoming_events = []

        for event in self.events:
            try:
                event_date = datetime.strptime(event.get('startDate', ''), '%Y-%m-%d').date()
                if event_date < today:
                    past_events.append(event)
                else:
                    upcoming_events.append(event)
            except (ValueError, TypeError):
                upcoming_events.append(event)

        if not past_events:
            messagebox.showinfo("No Past Events", "No events from yesterday or earlier were found.")
            return

        if self._add_events_to_archive(past_events):
            self.events = upcoming_events
            self.current_event_index = 0
            self.sort_events() # Re-sort and repopulate
            self.display_event()

            messagebox.showinfo(
                "Archive Complete",
                f"{len(past_events)} event(s) were archived to completed_events.json.\n\n"
                "IMPORTANT: Click 'Save All Events' to finalize the changes."
            )

    def _add_events_to_archive(self, events_to_archive):
        """Helper function to read the archive, add new events, and write it back."""
        if not events_to_archive:
            return True

        existing_completed = []
        if self.completed_json_path.exists():
            try:
                with open(self.completed_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "events" in data:
                        existing_completed = data.get("events", [])
                    elif isinstance(data, list): # Handle old format
                        existing_completed = data
            except (json.JSONDecodeError, IOError) as e:
                messagebox.showwarning("Archive Warning", f"Could not read existing completed_events.json. A new file will be created.\nError: {e}")

        # Prevent adding duplicates by checking event IDs
        existing_ids = {event.get('id') for event in existing_completed if event.get('id')}
        new_events = [event for event in events_to_archive if event.get('id') not in existing_ids]

        if not new_events:
            return True # All events to be archived were already there

        all_completed = existing_completed + new_events
        output_data = {
            "calendar": {
                "name": "Take Action Tucson Completed Events",
                "lastUpdated": self.get_current_iso_time(),
            },
            "events": all_completed,
        }
        try:
            with open(self.completed_json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            messagebox.showerror("Archive Error", f"Failed to write to completed_events.json.\nError: {e}")
            return False

    def clear_form(self):
        """Clears all input fields and the image preview."""
        is_editable_map = {key: is_editable for _, key, is_editable, *_ in self.form_fields}
        
        for key, widget in self.fields.items():
            is_editable = is_editable_map.get(key, True)
            
            if isinstance(widget, ttk.Entry):
                state = "normal" if is_editable else "readonly"
                widget.config(state="normal")
                widget.delete(0, tk.END)
                widget.config(state=state)
            elif isinstance(widget, tk.Text):
                state = "normal" if is_editable else "disabled"
                widget.config(state="normal")
                widget.delete("1.0", tk.END)
                widget.config(state=state)
        
        for var in self.event_type_vars.values():
            var.set(False)
        
        self.organizer_combobox.set('')
        
        self.new_image_path = None
        self.image_path_var.set("No event loaded.")
        self._load_and_display_image(None)

    def populate_event_listbox(self):
        if not self.event_listbox:
            return
        self.event_listbox.delete(0, tk.END)
        for event in self.events:
            date = event.get('startDate', 'No Date')
            title = event.get('title', 'Untitled Event')
            self.event_listbox.insert(tk.END, f"{date} - {title}")

    def on_listbox_select(self, event=None):
        if self.is_programmatic_selection:
            return
            
        selection = self.event_listbox.curselection()
        if not selection:
            return
            
        selected_index = selection[0]
        
        if selected_index == self.current_event_index:
            return
            
        self.apply_changes()
        
        self.current_event_index = selected_index
        self.display_event()

    def sort_events(self, keep_selection_id=None):
        """Sorts events by date/time/title and optionally keeps an event selected."""
        def sort_key(event):
            date_str = event.get('startDate', '')
            time_str = event.get('startTime', '00:00:00')

            # Default to midnight for TBD times for sorting purposes
            if 'tbd' in time_str.lower():
                time_str = '00:00:00'

            # Try to build a full datetime object for sorting
            try:
                # Attempt to parse with seconds (more specific)
                dt_obj = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Fallback to parsing without seconds
                    dt_obj = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                except ValueError:
                    # If date is invalid, push to the very end
                    return (datetime.max, event.get('title', ''))
            
            # Primary key: datetime, Secondary key: title (for events at the same time)
            return (dt_obj, event.get('title', ''))

        self.events.sort(key=sort_key)

        # After sorting, we need to find the new index of our selected event
        if keep_selection_id:
            try:
                self.current_event_index = next(i for i, event in enumerate(self.events) if event.get('id') == keep_selection_id)
            except StopIteration:
                # If the event somehow disappeared (e.g., archived), default to first.
                self.current_event_index = 0
        
        # Refresh the listbox with sorted events
        self.populate_event_listbox()

    def insert_weblink_template(self):
        """Insert hyperlink template at cursor position in description text box."""
        if hasattr(self, 'description_text') and self.description_text:
            template = '<a href="#" target="_blank" rel="noopener noreferrer">#</a>'
            try:
                self.description_text.insert(tk.INSERT, template)
            except tk.TclError:
                self.description_text.insert(tk.END, template)

    def insert_paragraph_break(self):
        """Insert <p> tag followed by a newline to start a new paragraph."""
        if hasattr(self, 'description_text') and self.description_text:
            template = '<p>\n'
            try:
                self.description_text.insert(tk.INSERT, template)
            except tk.TclError:
                self.description_text.insert(tk.END, template)

    def validate_address(self):
        """Use Nominatim to validate the address in location.address field."""
        entry_widget = self.fields.get("location.address")
        validate_btn = getattr(self, '_validate_btn', None)
        if not entry_widget:
            return
        address = entry_widget.get().strip()
        if not address:
            messagebox.showwarning("No Address", "Please enter an address first.")
            return

        # Show visual feedback that validation is in progress
        if validate_btn:
            validate_btn.config(state="disabled")
            self._start_countdown(validate_btn, 5)  # 5 second countdown
        entry_widget.config(style="TEntry")  # Reset to normal while checking

        def worker():
            try:
                params = {"q": address, "format": "json", "limit": 1}
                headers = {"User-Agent": "TAT-EventEditor/1.0"}
                resp = requests.get("https://nominatim.openstreetmap.org/search", 
                                  params=params, headers=headers, timeout=5)
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}")
                data = resp.json()
                if not data:
                    self.root.after(0, lambda: self._validation_complete(entry_widget, validate_btn, success=False))
                    return
                # On success, color green
                self.root.after(0, lambda: self._validation_complete(entry_widget, validate_btn, success=True))
            except requests.exceptions.Timeout:
                self.root.after(0, lambda: self._validation_timeout(entry_widget, validate_btn))
            except Exception:
                self.root.after(0, lambda: self._validation_complete(entry_widget, validate_btn, success=False))

        threading.Thread(target=worker, daemon=True).start()

    def _validation_complete(self, widget, button, success: bool):
        """Handle completion of address validation."""
        # Cancel any ongoing countdown
        if hasattr(self, '_countdown_job'):
            self.root.after_cancel(self._countdown_job)
        self._color_address_field(widget, success)
        if button:
            button.config(text="Validate", state="normal")

    def _validation_timeout(self, widget, button):
        """Handle validation timeout."""
        # Orange/yellow background for timeout
        style = ttk.Style()
        style.configure("Timeout.TEntry", fieldbackground="#fff3cd", foreground="#856404")
        widget.config(style="Timeout.TEntry")
        if button:
            # Cancel any ongoing countdown
            if hasattr(self, '_countdown_job'):
                self.root.after_cancel(self._countdown_job)
            button.config(text="Timeout", state="normal")
            # Reset button text after 2 seconds
            self.root.after(2000, lambda: button.config(text="Validate"))

    def _color_address_field(self, widget, success: bool):
        """Color the address entry green if success, red if failed validation."""
        style = ttk.Style()
        if success:
            style.configure("Valid.TEntry", fieldbackground="#CBDDC9", foreground="#4e604c")
            widget.config(style="Valid.TEntry")
        else:
            # Red background for failed validation
            style.configure("Invalid.TEntry", fieldbackground="#ffcccc", foreground="#cc0000")
            widget.config(style="Invalid.TEntry")

    def on_tab_changed(self, event):
        """Sync description from large text box to form when switching tabs."""
        if hasattr(self, 'description_text') and self.description_text:
            desc_content = self.description_text.get("1.0", tk.END).strip()
            # Update the event data directly
            if self.events and 0 <= self.current_event_index < len(self.events):
                self.events[self.current_event_index]["description"] = desc_content

    def _start_countdown(self, button, seconds_left):
        """Start countdown timer on button."""
        if seconds_left > 0:
            button.config(text=f"{seconds_left}s")
            self._countdown_job = self.root.after(1000, lambda: self._start_countdown(button, seconds_left - 1))
        else:
            # This shouldn't normally be reached since timeout should trigger first
            button.config(text="...", state="normal")

    @staticmethod
    def get_in_dict(d, key, default=None):
        keys = key.split('.')
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, default)
            else:
                return default
        return d
        
    @staticmethod
    def set_in_dict(d, key, value):
        keys = key.split('.')
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    @staticmethod
    def _normalize_time(time_str: str) -> str:
        """Return time in HH:MM format, stripping any :SS part."""
        if not isinstance(time_str, str):
            return time_str
        parts = time_str.strip().split(":")
        if len(parts) >= 2:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
        return time_str.strip()

if __name__ == "__main__":
    root = tkdnd.Tk()
    app = EventEditor(root)
    root.mainloop() 