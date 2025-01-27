from database_manager import DatabaseManager
from gui_manager import TimeTrackerGUI
from date_utils import DateUtils
import os
import sys

def main():
    db_manager = DatabaseManager()
    date_utils = DateUtils()
    gui = TimeTrackerGUI(db_manager, date_utils)
    gui.run()

if __name__ == "__main__":
    main()
