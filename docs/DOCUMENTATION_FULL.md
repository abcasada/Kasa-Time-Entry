# Technical Documentation

## Architecture

The application uses a Model-View-Controller-like pattern split across several Python modules:

### Core Components

1. `main.py`: Application entry point
   - Initializes core components
   - Launches the GUI

2. `database_manager.py`: Data layer
   - Handles SQLite database operations
   - Manages database connection and configuration
   - Implements CRUD operations for time entries

3. `gui_manager.py`: Presentation layer
   - Implements the tkinter-based user interface
   - Handles user input and event management
   - Manages data display and editing

4. `date_utils.py`: Utility functions
   - Handles date calculations and formatting
   - Provides week management utilities

### Database Schema

```sql
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    day_of_week TEXT NOT NULL,
    project TEXT NOT NULL,
    system TEXT NOT NULL,
    hours REAL NOT NULL,
    task TEXT NOT NULL
)
```

### Configuration

The application uses `config.json` to store settings:
```json
{
    "database_path": "path/to/database.db"
}
```

## Key Features Implementation

### 1. Week Management

- Uses `DateUtils` class to handle week calculations
- Weeks start on Monday
- Supports viewing up to 52 weeks in the past
- Automatically calculates date ranges for queries

### 2. Data Entry Form

Key components:
- Text entries for Project, System, and Hours
- Comboboxes for Task and Day selection
- "Use Today" checkbox for quick entry
- Validation for hours (must be numeric)
- System field auto-uppercase conversion

### 3. Data Display

Main table features:
- In-place cell editing via double-click
- Vertical scrollbar for many entries
- Column order: Project, System, Hours, Task, Day, Date

### 4. Weekly Summary

Implements a pivoted view of the data:
- Rows represent unique projects
- Columns show days of the week
- Cells contain sum of hours
- Query uses SQLite GROUP BY

### 5. Data Validation

Entry validation includes:
- Hours must be numeric
- Task must be 'Development' or 'Support'
- Day must be valid day of week
- System is converted to uppercase
- Date is auto-calculated from week/day

### 6. Event Handling

The application handles several types of events:
- Double-click for cell editing
- Return key for form submission
- Key events for dropdown navigation
- Focus events for edit completion
- Combo box key events for quick selection

## Custom UI Components

### 1. Editable Table (Treeview)

Implementation details:
- Uses ttk.Treeview as base
- Adds floating Entry widget for editing
- Handles cell position calculations
- Manages edit state and validation

### 2. Smart Dropdowns

Features:
- Type-ahead selection
- Case-insensitive matching
- Keyboard navigation
- Auto-completion

## Error Handling

The application implements several layers of error handling:
1. Database connection errors
2. Data validation errors
3. Input validation
4. SQLite operation errors

## Future Enhancement Areas

Potential improvements:
1. Export functionality
2. Project/System management
3. Multi-user support
4. Data backup features
5. Advanced reporting

## Testing

Manual testing procedures:
1. Data entry validation
2. Date calculations
3. Summary calculations
4. Database operations
5. UI responsiveness

## Dependencies

- Python 3.x
- tkinter (included in standard Python)
- sqlite3 (included in standard Python)

## Performance Considerations

- Uses SQLite for efficient data storage
- Implements lazy loading for weekly data
- Minimizes database operations