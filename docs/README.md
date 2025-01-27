# Time Entry Application

A simple desktop application for tracking work hours with project-based time entries.

## Features

- Track time entries by project, system, and task
- Automatic date handling based on selected week
- Weekly summary view
- In-place editing of entries
- Configurable database location

## Quick Start

1. Launch the application
2. Enter your time entries using the form at the bottom:
   - Project: Your project name
   - System: System identifier (automatically converted to uppercase)
   - Hours: Number of hours worked
   - Task: Choose between 'Development' or 'Support'
   - Day: Select the day of the week (or use "Use Today" checkbox)

3. Click "Add Entry" or press Enter to save the entry

## Navigation

- Use the week selector at the top to view different weeks
- Double-click any cell in the table to edit it
- Use the "Show Weekly Summary" button to see hours totaled by project and day

## Tips

- Use the "Use Today" checkbox to automatically fill in today's date
- Type the first letter of a day or task to quickly select from dropdowns
- Press ESC to cancel any edit in progress
- Database location can be changed via File → Configure Database

## Data Storage

Your time entries are stored in a SQLite database. The default location is in your Documents folder, but this can be changed through the File menu.