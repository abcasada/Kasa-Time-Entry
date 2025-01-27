# Time Entry Application - Technical Summary

## Core Components

1. **Main Application** (`main.py`)
   - Entry point and component initialization

2. **Database Layer** (`database_manager.py`)
   - SQLite database with single table `time_entries`
   - CRUD operations for time entries
   - Config file management

3. **GUI Layer** (`gui_manager.py`)
   - Tkinter-based interface
   - Data entry form
   - Editable data grid
   - Weekly summary view

4. **Date Utilities** (`date_utils.py`)
   - Week calculations
   - Date formatting
   - Day-of-week handling

## Key Features

1. **Data Management**
   - SQLite storage
   - Configurable database location
   - Automatic date calculations
   - Input validation

2. **User Interface**
   - In-place cell editing
   - Dropdown selections with type-ahead
   - Vertical scrolling for large datasets
   - Weekly data view

3. **Data Entry**
   - Project tracking
   - System tracking (auto-uppercase)
   - Hours logging
   - Task categorization (Development/Support)

4. **Date Handling**
   - Week-based navigation
   - Auto-date calculation
   - "Use Today" quick entry
   - 52-week history

## Configuration

- Uses `config.json` for settings
- Default location: User's Documents folder
- Supports environment variables in paths

## Database Schema

```sql
time_entries (
    id          INTEGER PRIMARY KEY,
    date        TEXT,
    day_of_week TEXT,
    project     TEXT,
    system      TEXT,
    hours       REAL,
    task        TEXT
)
```

## Dependencies
- Python 3.x
- Standard library only (tkinter, sqlite3)