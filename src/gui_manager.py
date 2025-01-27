import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

class TimeTrackerGUI:
    def __init__(self, db_manager, date_utils):
        self.root = tk.Tk()
        self.root.title("Time Tracker")
        self.db_manager = db_manager
        self.date_utils = date_utils
        
        self.selected_week = tk.StringVar()
        self.use_today = tk.BooleanVar(value=True)  # Set initial value to True
        self.use_today.trace('w', self.on_use_today_changed)  # Add trace for changes
        self.is_saving = False  # Add new flag to prevent duplicate saves
        self.setup_gui()
        self.update_ui_state()
        if not self.db_manager.is_connected:
            self.configure_database(initial=True)

    def setup_gui(self):
        # Add menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Add File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change DB location", command=self.configure_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Week selector
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Week selector controls (moved to left and stacked vertically)
        ttk.Label(frame, text="Select week:").grid(row=0, column=0, padx=5, sticky=tk.W)
        weeks = [self.date_utils.format_week_label(i) for i in range(53)]
        week_combo = ttk.Combobox(frame, textvariable=self.selected_week, values=weeks, width=24, state='readonly')
        week_combo.grid(row=1, column=0, padx=5, sticky=tk.W)
        week_combo.set(weeks[0])  # Set to current week

        # Configure column weights to push buttons to right
        frame.grid_columnconfigure(2, weight=1)  # Add space between week selector and buttons

        # Add database status label with left alignment
        self.status_label = ttk.Label(frame, text="", foreground="red")
        self.status_label.grid(row=2, column=0, pady=5, sticky=tk.W, padx=5)

        # Create frame for table and scrollbar with left alignment
        table_frame = ttk.Frame(frame)
        table_frame.grid(row=3, column=0, columnspan=4, pady=10, padx=5, sticky='nsew')
        
        # Configure grid weights to allow expansion
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Entry table with scrollbar
        self.tree = ttk.Treeview(table_frame, columns=('Project', 'System', 'Hours', 'Task', 'Day', 'Date', 'Notes'),
                                show='headings')
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid table and scrollbar
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Configure table frame grid weights
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        for col in ('Project', 'System', 'Hours', 'Task', 'Day', 'Date', 'Notes'):
            self.tree.heading(col, text=col)
            if col == 'Notes':
                self.tree.column(col, width=200)  # Make Notes column wider
            else:
                self.tree.column(col, width=100)

        # Add bindings for in-place editing and deletion
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Escape>', lambda e: self.cancel_edit())
        self.tree.bind('<Delete>', self.handle_delete)  # Add Delete key binding
        
        # Create entry widget for cell editing
        self.cell_editor = ttk.Entry(self.tree)
        self.cell_editor.bind('<Return>', lambda e: self.handle_edit_complete(True))
        self.cell_editor.bind('<FocusOut>', lambda e: self.handle_edit_complete(False))
        self.cell_editor.bind('<Escape>', lambda e: self.cancel_edit())
        
        # Initialize editing state variables
        self.editing_item = None
        self.editing_column = None

        # Add entry form (adjust row number since we removed the delete button)
        entry_frame = ttk.Frame(frame)
        entry_frame.grid(row=4, column=0, columnspan=4, pady=10, padx=5, sticky=tk.W)  # Changed from row=5 to row=4

        self.entries = {}
        # Add validation variables
        self.project_var = tk.StringVar()
        self.hours_var = tk.StringVar()
        self.project_var.trace('w', self.validate_required_fields)
        self.hours_var.trace('w', self.validate_required_fields)

        # Replace Project entry with combobox (update to use StringVar)
        ttk.Label(entry_frame, text='Project').grid(row=0, column=0, padx=(0,5))
        project_combo = ttk.Combobox(entry_frame, values=['Indirect - others', 'Indirect - training', 'Indirect - R&D'], 
                                   width=20, textvariable=self.project_var)
        project_combo.grid(row=0, column=1, padx=5)
        project_combo.bind('<Key>', self.handle_project_keypress)
        project_combo.bind('<KeyRelease>', self.handle_project_keypress)
        self.entries['project'] = project_combo

        # Remaining entry fields (update Hours to use StringVar)
        entry_fields = ['System', 'Hours']
        for i, field in enumerate(entry_fields):
            ttk.Label(entry_frame, text=field).grid(row=0, column=(i+1)*2, padx=5)
            if field == 'Hours':
                entry = ttk.Entry(entry_frame, width=8, textvariable=self.hours_var)
            else:
                entry = ttk.Entry(entry_frame, width=8)
            entry.grid(row=0, column=(i+1)*2+1, padx=5)
            self.entries[field.lower()] = entry

        # Add Task dropdown first
        ttk.Label(entry_frame, text='Task').grid(row=0, column=6, padx=5)
        task_combo = ttk.Combobox(entry_frame, values=['Development', 'Support'], width=12)  # Set width for Task
        task_combo.grid(row=0, column=7, padx=5)
        task_combo.bind('<Key>', self.handle_combo_keypress)  # Add this line
        task_combo.bind('<KeyRelease>', self.handle_combo_keypress)
        task_combo.bind('<<ComboboxSelected>>', lambda e: self.validate_required_fields())
        self.entries['task'] = task_combo

        # Add Day dropdown second
        ttk.Label(entry_frame, text='Day').grid(row=0, column=8, padx=5)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_combo = ttk.Combobox(entry_frame, values=days, width=10, state='disabled')  # Set initial state to disabled
        day_combo.grid(row=0, column=9, padx=5)
        day_combo.bind('<Key>', self.handle_combo_keypress)
        day_combo.bind('<KeyRelease>', self.handle_combo_keypress)
        self.entries['day'] = day_combo
        
        # Initialize day based on current state
        today = self.date_utils.get_today_day_of_week()  # Always set initial value to today
        day_combo.set(today)

        # Use today checkbox moves after dropdowns
        self.today_check = ttk.Checkbutton(entry_frame, text="Use today",
                                          variable=self.use_today)
        self.today_check.grid(row=0, column=10, padx=5)

        # Add Notes field with extra spacing
        ttk.Label(entry_frame, text='Notes').grid(row=1, column=0, padx=(0,5), sticky=tk.W, pady=(10,0))
        notes_entry = ttk.Entry(entry_frame, width=50)  # Make it wide enough for notes
        notes_entry.grid(row=1, column=1, columnspan=8, padx=5, sticky=tk.W+tk.E, pady=(10,0))
        notes_entry.bind('<KeyRelease>', lambda e: self.validate_required_fields())
        self.entries['notes'] = notes_entry

        # Move Add Entry button to next row
        self.add_button = ttk.Button(entry_frame, text="Add entry", 
                                   command=self.add_entry, state='disabled')
        self.add_button.grid(row=2, column=0, columnspan=2, pady=10, padx=(0,5), sticky=tk.W)

        ttk.Button(frame, text="Show weekly summary",
                  command=self.show_summary).grid(row=5, column=0, pady=10, sticky=tk.W, padx=5)  # Changed from row=6 to row=5

        # Bind events
        week_combo.bind('<<ComboboxSelected>>', self.on_week_selected)
        self.root.bind('<Return>', lambda e: self.add_entry())

        # Initial refresh to show current week's data
        self.refresh_entries()
        
        # Set initial focus to Project field
        self.entries['project'].focus_set()

    def update_ui_state(self):
        """Update UI elements based on database connection state"""
        state = 'normal' if self.db_manager.is_connected else 'disabled'
        
        # Update status label
        if not self.db_manager.is_connected:
            self.status_label.config(
                text=f"Database not accessible at {self.db_manager.db_path}",
                foreground="red"
            )
        else:
            self.status_label.config(
                text=f"Connected to database",
                foreground="green"
            )

        # Update entry widgets and comboboxes
        for widget in self.entries.values():
            if isinstance(widget, ttk.Combobox):
                if widget == self.entries['day'] and self.use_today.get():
                    widget.config(state='disabled')
                elif widget == self.entries['project']:
                    widget.config(state='normal' if self.db_manager.is_connected else 'disabled')
                else:
                    widget.config(state='readonly' if self.db_manager.is_connected else 'disabled')
            else:
                widget.config(state=state)
        
        # Update checkbox
        self.today_check.config(state=state)
        
        # Refresh data if connected
        if self.db_manager.is_connected:
            self.refresh_entries()

    def add_entry(self):
        if not self.db_manager.is_connected:
            return
        try:
            project = self.entries['project'].get()
            system = self.entries['system'].get().upper()  # Already uppercase, but being explicit
            hours = float(self.entries['hours'].get())
            task = self.entries['task'].get()
            notes = self.entries['notes'].get()  # Get notes value
            
            if self.use_today.get():
                day_of_week = self.date_utils.get_today_day_of_week()
            else:
                day_of_week = self.entries['day'].get()

            week_dates = self.get_selected_week_dates()
            date = self.date_utils.get_date_for_day(week_dates, day_of_week)

            self.db_manager.add_entry(date, day_of_week, project, system, hours, task)
            self.refresh_entries()
            self.clear_entries()
            
            # Set focus back to Project field after adding entry
            self.entries['project'].focus_set()

        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid values")

    def get_selected_week_dates(self):
        week = self.selected_week.get()
        if 'Current Week' in week:
            return self.date_utils.get_current_week_dates()
        else:
            weeks_ago = int(week.split()[0])
            return self.date_utils.get_week_dates(weeks_ago)

    def refresh_entries(self, event=None):
        if not self.db_manager.is_connected:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)

        week_dates = self.get_selected_week_dates()
        entries = self.db_manager.get_entries_for_week(
            week_dates[0].strftime('%Y-%m-%d'),
            week_dates[6].strftime('%Y-%m-%d')
        )

        for entry in entries:
            # Skip the ID (first position) when displaying values
            values = list(entry[1:])
            self.tree.insert('', 'end', values=values, tags=(entry[0],))

    def clear_entries(self):
        for entry in self.entries.values():
            if isinstance(entry, ttk.Combobox):
                if entry == self.entries['day'] and self.use_today.get():
                    # If it's the day field and "Use Today" is selected, set to today
                    entry.set(self.date_utils.get_today_day_of_week())
                else:
                    entry.set('')  # Clear other comboboxes
            else:
                entry.delete(0, tk.END)  # Clear regular entries
        # Validate fields after clearing
        self.validate_required_fields()

    def show_summary(self):
        week_dates = self.get_selected_week_dates()
        data = self.db_manager.get_weekly_summary(
            week_dates[0].strftime('%Y-%m-%d'),
            week_dates[6].strftime('%Y-%m-%d')
        )

        # Create summary window
        summary = tk.Toplevel(self.root)
        summary.title("Weekly Summary")

        # Create treeview for summary
        tree = ttk.Treeview(summary, columns=['Project'] + [d.strftime('%A') for d in week_dates],
                           show='headings')
        tree.pack(padx=10, pady=10)

        # Set up columns
        tree.heading('Project', text='Project')
        for date in week_dates:
            day = date.strftime('%A')
            tree.heading(day, text=day)
            tree.column(day, width=100)

        # Process data
        summary_dict = {}
        for project, day, hours in data:
            if project not in summary_dict:
                summary_dict[project] = {d.strftime('%A'): 0 for d in week_dates}
            summary_dict[project][day] = hours

        # Insert data
        for project, days in summary_dict.items():
            values = [project] + [days[d.strftime('%A')] for d in week_dates]
            tree.insert('', 'end', values=values)

    def on_double_click(self, event):
        """Handle double click on a cell"""
        # Identify the clicked cell
        region = self.tree.identify('region', event.x, event.y)
        if region != 'cell':
            return

        # Get column and item that was clicked
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        
        if not item or not column:
            return

        # Get column name and prevent editing of Date column
        column_name = self.tree.heading(column)['text']
        if column_name == 'Date':
            return
            
        # Get column index (0-based)
        column_idx = int(column[1]) - 1
        
        # If clicking Hours column, verify it's a number
        if self.tree.heading(column)['text'] == 'Hours':
            try:
                float(self.tree.item(item)['values'][column_idx])
            except:
                self.tree.item(item)['values'][column_idx] = 0

        # Position entry widget on top of cell
        bbox = self.tree.bbox(item, column)
        if not bbox:
            return
        
        # Configure entry widget
        self.cell_editor.delete(0, tk.END)
        self.cell_editor.insert(0, self.tree.item(item)['values'][column_idx])
        self.cell_editor.place(x=bbox[0], y=bbox[1],
                             width=bbox[2], height=bbox[3])
        self.cell_editor.focus_set()
        
        # Store editing state
        self.editing_item = item
        self.editing_column = column_idx

    def handle_focus_out(self, event):
        """Handle focus out event more carefully"""
        # Check if we're still within the editing widget
        if self.cell_editor.focus_get() != self.cell_editor:
            self.save_edit(event)

    def handle_edit_complete(self, is_return_key=False):
        """Handle edit completion from either Return or FocusOut"""
        if self.editing_item and self.editing_column is not None:
            if self.cell_editor.winfo_ismapped():
                self.save_edit()
                if is_return_key:
                    # Prevent the Return key from triggering another event
                    return 'break'

    def save_edit(self):
        """Save the edited cell value"""
        if not self.editing_item or self.editing_column is None:
            return
            
        try:
            new_value = self.cell_editor.get()
            current_values = list(self.tree.item(self.editing_item)['values'])
            
            # Validate based on column
            column_name = self.tree.heading(f'#{self.editing_column + 1}')['text']
            if column_name == 'Hours':
                try:
                    hours_val = float(new_value)
                    # Validate hours is a multiple of 0.25
                    if hours_val % 0.25 != 0:
                        messagebox.showerror("Error", "Hours must be a multiple of 0.25")
                        return
                    new_value = hours_val
                except ValueError:
                    messagebox.showerror("Error", "Hours must be a number")
                    return
            elif column_name == 'Task' and new_value not in ['Development', 'Support']:
                messagebox.showerror("Error", "Task must be either Development or Support")
                return
            elif column_name == 'Day' and new_value not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                messagebox.showerror("Error", "Invalid day of week")
                return
            elif column_name == 'System':
                new_value = new_value.upper()
                
            current_values[self.editing_column] = new_value
            
            # If Day was changed, update the Date
            if column_name == 'Day':
                week_dates = self.get_selected_week_dates()
                new_date = self.date_utils.get_date_for_day(week_dates, new_value)
                current_values[5] = new_date  # Update date column
            
            # Always ensure hours is float for database
            hours_val = float(current_values[2])
            
            # Update database with reordered values
            entry_id = self.tree.item(self.editing_item)['tags'][0]
            self.db_manager.update_entry(
                entry_id,
                current_values[5],  # date
                current_values[4],  # day
                current_values[0],  # project
                current_values[1],  # system
                hours_val,          # hours
                current_values[3]   # task
            )
            
            # Update tree display
            self.tree.item(self.editing_item, values=current_values)
            
        finally:
            self.cancel_edit()

    def cancel_edit(self):
        """Cancel the cell editing"""
        self.cell_editor.place_forget()
        self.editing_item = None
        self.editing_column = None
        self.is_saving = False  # Reset saving flag
        self.tree.focus_set()

    def on_week_selected(self, event=None):
        """Handle week selection, including checkbox state"""
        week = self.selected_week.get()
        # Set checkbox based on whether current week is selected
        self.use_today.set('Current Week' in week)
        # Refresh entries as before
        self.refresh_entries(event)

    def handle_combo_keypress(self, event):
        """Handle keyboard input in combo boxes"""
        # Ignore KeyRelease events for special keys
        if hasattr(event, 'keysym') and event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down'):
            return

        # Only process KeyPress events
        if event.type != tk.EventType.KeyPress:
            return

        combo = event.widget
        
        # Use the typed character directly
        if not event.char:
            return
            
        typed = event.char.lower()

        # Get the values from the combobox
        values = combo['values']
        if not values:
            return

        # Find first match (case-insensitive)
        for value in values:
            if value.lower().startswith(typed):
                # Only set if different to avoid triggering unnecessary events
                if combo.get() != value:
                    combo.set(value)
                break

    def handle_project_keypress(self, event):
        """Special handling for Project combobox"""
        # Ignore KeyRelease events for special keys
        if hasattr(event, 'keysym') and event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down'):
            return

        # Only process KeyPress events
        if event.type != tk.EventType.KeyPress:
            return

        combo = event.widget
        current_text = combo.get()
        
        # Use the typed character directly
        if not event.char:
            return
            
        typed = event.char.lower()

        # Special handling for Indirect prefix
        if current_text.lower().startswith('indirect'):
            if typed == 'o':
                combo.delete(0, tk.END)
                combo.insert(0, 'Indirect - others')
            elif typed == 't':
                combo.delete(0, tk.END)
                combo.insert(0, 'Indirect - training')
            elif typed == 'r':
                combo.delete(0, tk.END)
                combo.insert(0, 'Indirect - R&D')
        else:
            # Regular prefix matching for initial letter
            if typed == 'i':
                combo.delete(0, tk.END)
                combo.insert(0, 'Indirect - others')
            # Allow free typing for other values
        
        return 'break'  # Prevent default character insertion

    def configure_database(self, initial=False):
        """Open dialog to configure database path"""
        message = "Please select the database file location" if initial else "Select Database Location"
        initial_dir = os.path.dirname(os.path.expandvars(self.db_manager.db_path)) if self.db_manager.db_path else os.path.expanduser("~")
        
        new_path = filedialog.askopenfilename(
            title=message,
            initialdir=initial_dir,
            filetypes=[("SQLite Database", "*.db")],
        )
        
        if new_path:
            # Convert to absolute path
            new_path = os.path.abspath(new_path)
            # Save to config and reconnect
            self.db_manager.save_config(new_path)
            self.db_manager.try_connect()
            self.update_ui_state()
        elif initial:  # If no database selected on initial setup, exit application
            messagebox.showerror("Error", "No database selected. Application will exit.")
            self.root.quit()

    def on_use_today_changed(self, *args):
        """Handle changes to Use Today checkbox"""
        day_combo = self.entries['day']
        if self.use_today.get():
            today = self.date_utils.get_today_day_of_week()
            day_combo.set(today)
            day_combo.config(state='disabled')
        else:
            day_combo.set('')  # Clear the day field
            day_combo.config(state='readonly')
        
        # Validate fields after changing Use Today
        self.validate_required_fields()

    def handle_delete(self, event=None):
        """Handle deletion of selected rows via Delete key"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select a row to delete")
            return
            
        if messagebox.askyesno("Confirm Delete", 
                             "Are you sure you want to delete the selected row(s)?",
                             icon='warning'):
            for item in selected_items:
                entry_id = self.tree.item(item)['tags'][0]
                self.db_manager.delete_entry(entry_id)
            self.refresh_entries()

    def validate_required_fields(self, *args):
        """Enable/disable Add Entry button based on required fields"""
        project = self.project_var.get().strip()
        hours = self.hours_var.get().strip()
        day = self.entries['day'].get().strip()
        task = self.entries['task'].get().strip()
        notes = self.entries['notes'].get().strip()

        # Enable button only if required fields are filled and either Task or Notes has content
        if project and hours and (day or self.use_today.get()) and (task or notes):
            try:
                hours_val = float(hours)  # Validate hours is a number
                # Check if hours is a multiple of 0.25
                if hours_val % 0.25 != 0:
                    self.add_button.config(state='disabled')
                    return
                self.add_button.config(state='normal')
            except ValueError:
                self.add_button.config(state='disabled')
        else:
            self.add_button.config(state='disabled')

    def save_edit(self):
        """Save the edited cell value"""
        if not self.editing_item or self.editing_column is None:
            return
            
        try:
            new_value = self.cell_editor.get()
            current_values = list(self.tree.item(self.editing_item)['values'])
            
            # Validate based on column
            column_name = self.tree.heading(f'#{self.editing_column + 1}')['text']
            if column_name == 'Hours':
                try:
                    hours_val = float(new_value)
                    # Validate hours is a multiple of 0.25
                    if hours_val % 0.25 != 0:
                        messagebox.showerror("Error", "Hours must be a multiple of 0.25")
                        return
                    new_value = hours_val
                except ValueError:
                    messagebox.showerror("Error", "Hours must be a number")
                    return
            elif column_name == 'Task' and new_value not in ['Development', 'Support']:
                messagebox.showerror("Error", "Task must be either Development or Support")
                return
            elif column_name == 'Day' and new_value not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                messagebox.showerror("Error", "Invalid day of week")
                return
            elif column_name == 'System':
                new_value = new_value.upper()
                
            current_values[self.editing_column] = new_value
            
            # If Day was changed, update the Date
            if column_name == 'Day':
                week_dates = self.get_selected_week_dates()
                new_date = self.date_utils.get_date_for_day(week_dates, new_value)
                current_values[5] = new_date  # Update date column
            
            # Always ensure hours is float for database
            hours_val = float(current_values[2])
            
            # Update database with reordered values
            entry_id = self.tree.item(self.editing_item)['tags'][0]
            self.db_manager.update_entry(
                entry_id,
                current_values[5],  # date
                current_values[4],  # day
                current_values[0],  # project
                current_values[1],  # system
                hours_val,          # hours
                current_values[3]   # task
            )
            
            # Update tree display
            self.tree.item(self.editing_item, values=current_values)
            
        finally:
            self.cancel_edit()

    def run(self):
        self.root.mainloop()
