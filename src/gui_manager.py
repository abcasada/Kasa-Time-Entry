import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import tkinter.font as tkFont  # Import tkinter.font

class TimeTrackerGUI:
    def __init__(self, db_manager, date_utils):
        self.root = tk.Tk()
        self.root.title("Time Tracker")
        self.db_manager = db_manager
        self.date_utils = date_utils
        
        # Add font scaling with reliable default font size
        self.current_scale = 1.0
        default_font = tkFont.nametofont("TkDefaultFont")
        self.default_font_size = default_font.cget("size")
        if self.default_font_size <= 0:
            self.default_font_size = 9  # fallback default
        
        # Configure Treeview style
        style = ttk.Style()
        style.configure("Treeview", rowheight=22)
        style.configure("Treeview.Heading", font=('TkDefaultFont', 9, 'bold'))  # Make headers bold
        style.map('Treeview', background=[('selected', '#0078D7')])
        
        # Configure alternating row colors
        self.tree_odd_color = "white"    # White for odd rows
        self.tree_even_color = "#f0f0f0" # Light gray for even rows
        
        # Initialize all StringVar variables
        self.selected_week = tk.StringVar()
        self.use_today = tk.BooleanVar(value=True)
        self.project_var = tk.StringVar()
        self.hours_var = tk.StringVar()
        
        # Add traces for validation (update operation names)
        self.project_var.trace_add('write', self.validate_required_fields)
        self.hours_var.trace_add('write', self.validate_required_fields)
        self.use_today.trace_add('write', self.on_use_today_changed)

        self.is_saving = False
        self.setup_gui()
        self.update_ui_state()
        if not self.db_manager.is_connected:
            self.configure_database(initial=True)

    def setup_gui(self):
        # Setup main window and menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change DB location", command=self.configure_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=lambda: self.change_font_scale(1.2))
        view_menu.add_command(label="Zoom Out", command=lambda: self.change_font_scale(1/1.2))
        
        # Remove scale button code and continue with rest of setup
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Week selector section
        self._setup_week_selector(frame)

        # Table section
        self._setup_table(frame)

        # Entry form section
        self._setup_entry_form(frame)

        # Initial setup
        self.refresh_entries()
        self.entries['project'].focus_set()

    def _setup_week_selector(self, frame):
        ttk.Label(frame, text="Select week:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        weeks = [self.date_utils.format_week_label(i) for i in range(53)]
        week_combo = ttk.Combobox(frame, textvariable=self.selected_week, values=weeks,
                                 width=24, state='readonly')
        week_combo.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        week_combo.set(weeks[0])
        week_combo.bind('<<ComboboxSelected>>', self.on_week_selected)

        self.status_label = ttk.Label(frame, text="", foreground="red")
        self.status_label.grid(row=2, column=0, pady=5, sticky=tk.W, padx=5)

    def _setup_table(self, frame):
        table_frame = ttk.Frame(frame, height=700)  # Set fixed height
        table_frame.grid(row=3, column=0, columnspan=4, pady=5, padx=5, sticky='nsew')
        table_frame.grid_propagate(False)  # Prevent frame from shrinking to contents

        self.tree = ttk.Treeview(table_frame,
                                columns=('Project', 'System', 'Hours', 'Task', 'Day', 'Date', 'Notes'),
                                show='headings',
                                style="Treeview")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Add borders to columns
        for col in ('Project', 'System', 'Hours', 'Task', 'Day', 'Date', 'Notes'):
            self.tree.heading(col, text=col, anchor=tk.W)  # Left align header
            self.tree.column(col, width=200 if col == 'Notes' else 100, stretch=True, anchor=tk.W)  # Left align content
            self.tree.tag_configure(col, background='white')  # Ensure background is white

        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Table bindings and editor setup
        self._setup_table_editor()

    def _setup_table_editor(self):
        self.tree.bind('<Double-1>', self.on_double_click)
        self.tree.bind('<Delete>', self.handle_delete)
        self.tree.bind('<Escape>', lambda e: self.cancel_edit())
        
        self.cell_editor = ttk.Entry(self.tree)
        self.cell_editor.bind('<Return>', lambda e: self.handle_edit_complete(True))
        self.cell_editor.bind('<FocusOut>', lambda e: self.handle_edit_complete(False))
        self.cell_editor.bind('<Escape>', lambda e: self.cancel_edit())

        self.editing_item = None
        self.editing_column = None

    def _setup_entry_form(self, frame):
        entry_frame = ttk.Frame(frame)
        entry_frame.grid(row=4, column=0, columnspan=4, pady=5, padx=5, sticky=tk.W)

        # Initialize entries dictionary and variables
        self.entries = {}
        self._setup_form_fields(entry_frame)
        
        # Show weekly summary button
        ttk.Button(frame, text="Show weekly summary",
                  command=self.show_summary).grid(row=5, column=0, pady=5, sticky=tk.W, padx=5)

    def _setup_form_fields(self, entry_frame):
        # Project field with label
        ttk.Label(entry_frame, text='Project').grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        # Modified project field setup with better autocomplete
        project_cb = ttk.Combobox(entry_frame, textvariable=self.project_var, width=20)
        project_cb.grid(row=0, column=1, padx=5, pady=5)
        project_cb['values'] = ['Indirect - others', 'Indirect - training', 'Indirect - R&D']
        
        # Configure project combobox behavior
        project_cb.bind('<FocusIn>', self.on_project_focus)
        project_cb.bind('<KeyRelease>', self.on_project_keyrelease)
        project_cb.bind('<<ComboboxSelected>>', lambda e: self.validate_required_fields())
        # Add these new bindings
        project_cb.bind('<Down>', self.on_project_arrow)
        project_cb.bind('<Up>', self.on_project_arrow)
        project_cb.bind('<Return>', lambda e: self.add_entry() if self.validate_required_fields() else None)
        
        self.entries['project'] = project_cb

        # System and Hours fields with labels
        ttk.Label(entry_frame, text='System').grid(row=0, column=2, padx=5, pady=5)
        self._add_form_field(entry_frame, 'System', 2, width=8)
        
        ttk.Label(entry_frame, text='Hours').grid(row=0, column=4, padx=5, pady=5)
        self._add_form_field(entry_frame, 'Hours', 4, width=8, textvariable=self.hours_var)

        # Task field with label
        ttk.Label(entry_frame, text='Task').grid(row=0, column=6, padx=5, pady=5)
        task_cb = ttk.Combobox(entry_frame, width=12)
        task_cb.grid(row=0, column=7, padx=5, pady=5)
        task_cb['values'] = ['', 'Development', 'Support']
        
        # Configure task combobox behavior
        task_cb.bind('<FocusIn>', self.on_task_focus)
        task_cb.bind('<KeyRelease>', self.on_task_keyrelease)
        task_cb.bind('<<ComboboxSelected>>', lambda e: self.validate_required_fields())
        task_cb.bind('<Down>', self.on_task_arrow)
        task_cb.bind('<Up>', self.on_task_arrow)
        task_cb.bind('<Return>', lambda e: self.add_entry() if self.validate_required_fields() else None)
        
        self.entries['task'] = task_cb

        # Day field with label
        ttk.Label(entry_frame, text='Day').grid(row=0, column=8, padx=5, pady=5)
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self._add_form_field(entry_frame, 'Day', 8, combobox=True,
                            values=[''] + days_of_week,
                            width=10, state='disabled')

        # Use today checkbox with Return key binding
        self.today_check = ttk.Checkbutton(entry_frame, text="Use today",
                                          variable=self.use_today)
        self.today_check.grid(row=0, column=10, padx=5)
        self.today_check.bind('<Return>', lambda e: self.add_entry() if self.validate_required_fields() else None)

        # Notes field with label
        ttk.Label(entry_frame, text='Notes').grid(row=1, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self._add_form_field(entry_frame, 'Notes', 0, row=1, width=50, columnspan=8, sticky=tk.W+tk.E)

        # Set initial day value
        self.entries['day'].set(self.date_utils.get_today_day_of_week())

    def _add_form_field(self, parent, label, col, row=0, combobox=False, **kwargs):
        # Extract grid-specific parameters
        grid_kwargs = {}
        for grid_param in ['columnspan', 'sticky']:
            if grid_param in kwargs:
                grid_kwargs[grid_param] = kwargs.pop(grid_param)
        
        if combobox:
            widget = ttk.Combobox(parent, **kwargs)
            widget.bind('<<ComboboxSelected>>', lambda e: self.validate_required_fields())
        else:
            widget = ttk.Entry(parent, **kwargs)
            widget.bind('<KeyRelease>', lambda e: self.validate_required_fields())

        # Apply grid with separated parameters
        grid_kwargs.update({'row': row, 'column': col+1, 'padx': 5, 'pady': 5})
        widget.grid(**grid_kwargs)
        widget.bind('<Return>', lambda e: self.add_entry() if self.validate_required_fields() else None)

        self.entries[label.lower()] = widget

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
                elif widget == self.entries['project'] or widget == self.entries['task']:
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
            system = self.entries['system'].get().upper()
            hours = float(self.entries['hours'].get())
            task = self.entries['task'].get()
            notes = self.entries['notes'].get()
            
            if self.use_today.get():
                day_of_week = self.date_utils.get_today_day_of_week()
            else:
                day_of_week = self.entries['day'].get()

            week_dates = self.get_selected_week_dates()
            date = self.date_utils.get_date_for_day(week_dates, day_of_week)

            self.db_manager.add_entry(date, day_of_week, project, system, hours, task, notes)
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

        # Configure row tags if they don't exist
        self.tree.tag_configure('oddrow', background=self.tree_odd_color)
        self.tree.tag_configure('evenrow', background=self.tree_even_color)

        week_dates = self.get_selected_week_dates()
        entries = self.db_manager.get_entries_for_week(
            week_dates[0].strftime('%Y-%m-%d'),
            week_dates[6].strftime('%Y-%m-%d')
        )

        for i, entry in enumerate(entries):
            values = list(entry[1:])
            tag = ('oddrow' if i % 2 else 'evenrow',)  # Alternate row colors
            self.tree.insert('', 'end', values=values, tags=(entry[0], *tag))

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
        tree = ttk.Treeview(summary,
                           columns=['Project'] + [d.strftime('%A') for d in week_dates],
                           show='headings',
                           style="Treeview")
        # Add border to frame
        tree.master.configure(relief='solid', borderwidth=1)
        tree.pack(padx=10, pady=10)

        # Configure row tags
        tree.tag_configure('oddrow', background=self.tree_odd_color)
        tree.tag_configure('evenrow', background=self.tree_even_color)

        # Set up columns
        tree.heading('Project', text='Project', anchor=tk.W)  # Left align header
        tree.column('Project', anchor=tk.W)  # Left align content
        for date in week_dates:
            day = date.strftime('%A')
            tree.heading(day, text=day, anchor=tk.W)  # Left align header
            tree.column(day, width=100, anchor=tk.W)  # Left align content

        # Process data
        summary_dict = {}
        for project, day, hours in data:
            if project not in summary_dict:
                summary_dict[project] = {d.strftime('%A'): 0 for d in week_dates}
            summary_dict[project][day] = hours

        # Insert data with empty strings for zero values and alternating colors
        for i, (project, days) in enumerate(summary_dict.items()):
            values = [project] + ['' if days[d.strftime('%A')] == 0 else days[d.strftime('%A')]
                                for d in week_dates]
            tree.insert('', 'end', values=values, tags=('oddrow' if i % 2 else 'evenrow'))

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
            elif column_name == 'Task' and new_value not in ['', 'Development', 'Support']:
                messagebox.showerror("Error", "Task must be either Development, Support, or empty")
                return
            elif column_name == 'Day' and new_value and new_value not in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
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
            notes = current_values[6] if len(current_values) > 6 else ""  # Get notes from values
            
            self.db_manager.update_entry(
                entry_id,
                current_values[5],  # date
                current_values[4],  # day
                current_values[0],  # project
                current_values[1],  # system
                hours_val,          # hours
                current_values[3],  # task
                notes               # notes
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
        """Enable/disable entry based on required fields, returns True if valid"""
        project = self.project_var.get().strip()
        hours = self.hours_var.get().strip()
        day = self.entries['day'].get().strip()
        task = self.entries['task'].get().strip()
        notes = self.entries['notes'].get().strip()

        # Check if required fields are filled and either Task or Notes has content
        if project and hours and (task or notes):
            try:
                hours_val = float(hours)  # Validate hours is a number
                # Check if hours is a multiple of 0.25
                if hours_val % 0.25 == 0:
                    return True
            except ValueError:
                pass
        return False

    def change_font_scale(self, factor):
        """Change font scale by the given factor"""
        self.current_scale *= factor
        new_size = int(self.default_font_size * self.current_scale)

        # Update font sizes
        style = ttk.Style()
        style.configure(".", font=('TkDefaultFont', new_size))
        style.configure("Treeview", font=('TkDefaultFont', new_size))
        style.configure("Treeview.Heading", font=('TkDefaultFont', new_size))

        # Update combobox fonts
        self.root.option_add('*TCombobox*Listbox.font', ('TkDefaultFont', new_size))
        for widget in self.entries.values():
            if isinstance(widget, ttk.Combobox):
                widget.configure(font=('TkDefaultFont', new_size))
            elif isinstance(widget, ttk.Entry):
                widget.configure(font=('TkDefaultFont', new_size))

        # Update tree column widths
        if hasattr(self, 'tree'):
            for col in self.tree.cget('columns'):
                current_width = self.tree.column(col, 'width')
                self.tree.column(col, width=int(current_width * factor))

    def run(self):
        self.root.mainloop()

    def on_project_focus(self, event):
        """When project field gets focus, select all text"""
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        
    def on_project_keyrelease(self, event):
        """Handle autocomplete for project field"""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return']:
            return
            
        value = event.widget.get()
        all_values = ['Indirect - others', 'Indirect - training', 'Indirect - R&D']
        
        # Special handling for backspace
        if event.keysym == 'BackSpace':
            # Remove one more character if there's a selection
            if event.widget.selection_present():
                event.widget.delete(event.widget.index("insert")-1)
            event.widget['values'] = [x for x in all_values if x.lower().startswith(value.lower())]
            return
            
        # Quick selection after typing 'i'
        if len(value) == 2 and value.lower().startswith('i'):
            second_char = value[-1].lower()
            if second_char == 'o':
                event.widget.set('Indirect - others')
                event.widget.selection_range(len(value), len('Indirect - others'))
                event.widget.icursor(len(value))
                return
            elif second_char == 't':
                event.widget.set('Indirect - training')
                event.widget.selection_range(len(value), len('Indirect - training'))
                event.widget.icursor(len(value))
                return
            elif second_char == 'r':
                event.widget.set('Indirect - R&D')
                event.widget.selection_range(len(value), len('Indirect - R&D'))
                event.widget.icursor(len(value))
                return
        
        if value:
            # Find first match that starts with current value (case insensitive)
            match = next((x for x in all_values if x.lower().startswith(value.lower())), None)
            if match:
                # Only set if we have something to autocomplete
                if len(match) > len(value):
                    event.widget.set(match)
                    event.widget.selection_range(len(value), len(match))
                    event.widget.icursor(len(value))
            
            # Update dropdown list with all matching values
            matches = [x for x in all_values if x.lower().startswith(value.lower())]
            event.widget['values'] = matches if matches else all_values
        else:
            event.widget['values'] = all_values

    def on_project_arrow(self, event):
        """Handle arrow keys in project combobox"""
        event.widget.event_generate('<Down>' if event.keysym == 'Down' else '<Up>')
        return 'break'

    def on_task_focus(self, event):
        """When task field gets focus, select all text"""
        event.widget.select_range(0, tk.END)
        event.widget.icursor(tk.END)
        
    def on_task_keyrelease(self, event):
        """Handle autocomplete for task field"""
        if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return']:
            return

        value = event.widget.get()
        all_values = ['', 'Development', 'Support']
        
        # Special handling for backspace
        if event.keysym == 'BackSpace':
            if event.widget.selection_present():
                event.widget.delete(event.widget.index("insert")-1)
            event.widget['values'] = [x for x in all_values if x.lower().startswith(value.lower())]
            return
            
        if value:
            # Find first match that starts with current value (case insensitive)
            match = next((x for x in all_values if x.lower().startswith(value.lower())), None)
            if match:
                # Only set if we have something to autocomplete
                if len(match) > len(value):
                    event.widget.set(match)
                    event.widget.selection_range(len(value), len(match))
                    event.widget.icursor(len(value))
            
            # Update dropdown list with all matching values
            matches = [x for x in all_values if x.lower().startswith(value.lower())]
            event.widget['values'] = matches if matches else all_values
        else:
            event.widget['values'] = all_values

    def on_task_arrow(self, event):
        """Handle arrow keys in task combobox"""
        event.widget.event_generate('<Down>' if event.keysym == 'Down' else '<Up>')
        return 'break'

