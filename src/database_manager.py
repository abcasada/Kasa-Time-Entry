import sqlite3
from datetime import datetime
import os
import json

class DatabaseManager:
    def __init__(self):
        self.load_config()
        self.conn = None
        self.is_connected = False
        self.try_connect()

    def load_config(self):
        """Load database path from config file"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            # Expand environment variables in path
            self.db_path = os.path.expandvars(config['database_path'])
        except:
            # Set to None if no config exists
            self.db_path = None

    def save_config(self, new_path):
        """Save new database path to config"""
        # Convert to Windows-style path and use environment variable
        new_path = new_path.replace('\\', '/')  # Normalize slashes
        if new_path.startswith(os.path.expanduser("~")):
            new_path = new_path.replace(os.path.expanduser("~"), "%USERPROFILE%")
        
        config = {'database_path': new_path}
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        self.db_path = os.path.expandvars(new_path)

    def try_connect(self):
        """Attempt to connect to database"""
        try:
            # First close any existing connection
            if self.conn:
                self.conn.close()
                self.conn = None
            
            if not self.db_path or not os.path.exists(self.db_path):
                self.is_connected = False
                return False
            
            # Create new connection
            self.conn = sqlite3.connect(self.db_path)
            
            # Create tables immediately after successful connection
            cursor = self.conn.cursor()
            
            # First create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS time_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    day_of_week TEXT NOT NULL,
                    project TEXT NOT NULL,
                    system TEXT NOT NULL,
                    hours REAL NOT NULL,
                    task TEXT NOT NULL
                )
            ''')
            
            # Check if notes column exists, add if it doesn't
            cursor.execute("PRAGMA table_info(time_entries)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'notes' not in columns:
                cursor.execute('ALTER TABLE time_entries ADD COLUMN notes TEXT')
            
            self.conn.commit()
            self.is_connected = True
            return True
            
        except Exception as e:
            if self.conn:
                self.conn.close()
                self.conn = None
            self.is_connected = False
            return False

    def create_tables(self):
        """Removed as table creation is now handled in try_connect"""
        pass

    def add_entry(self, date, day_of_week, project, system, hours, task, notes=""):
        if not self.is_connected:
            return False
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO time_entries (date, day_of_week, project, system, hours, task, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date, day_of_week, project, system, hours, task, notes))
        self.conn.commit()

    def get_entries_for_week(self, start_date, end_date):
        if not self.is_connected:
            return []
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, project, system, hours, task, day_of_week, date,
                   COALESCE(notes, '') as notes
            FROM time_entries
            WHERE date BETWEEN ? AND ?
            ORDER BY date
        ''', (start_date, end_date))
        return cursor.fetchall()

    def get_weekly_summary(self, start_date, end_date):
        if not self.is_connected:
            return []
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT project, day_of_week, SUM(hours)
            FROM time_entries
            WHERE date BETWEEN ? AND ?
            GROUP BY project, day_of_week
        ''', (start_date, end_date))
        return cursor.fetchall()

    def update_entry(self, entry_id, date, day_of_week, project, system, hours, task, notes=""):
        if not self.is_connected:
            return False
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE time_entries
            SET date=?, day_of_week=?, project=?, system=?, hours=?, task=?, notes=?
            WHERE id=?
        ''', (date, day_of_week, project, system, hours, task, notes, entry_id))
        self.conn.commit()

    def delete_entry(self, entry_id):
        if not self.is_connected:
            return False
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM time_entries WHERE id=?', (entry_id,))
        self.conn.commit()
