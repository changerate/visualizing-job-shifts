import pandas as pd
from datetime import datetime, date, time
import numpy as np
import os
from pathlib import Path
import sqlite3

from classes.shiftClass import WorkShift
from utilities.necessary_data import NECESSARY_DATA
from utilities.ut_functions import *

SCRIPTS_DIR = Path(__file__).parent.parent
SHIFTS_SQL_DB_NAME = 'databases/shifts.db'





# =====================================================================
#            UTILITY FUNCTIONS
# =====================================================================



def parse_time_flexible(x):
    if pd.isna(x) or x == '':
        return pd.NaT
    
    if isinstance(x, time):
        # print(f"x is already correct format")
        return x

    for fmt in ("%H:%M:%S", "%I:%M %p", "%H:%M"):  # supports 24hr, 12hr, with/without seconds
        try:
            stdFormat = datetime.strptime(x, fmt).time()
            return stdFormat
        except ValueError:
            continue
    return pd.NaT  # if none match






def parse_date_flexible(x):
    if pd.isna(x) or x == '':
        return pd.NaT
    
    if isinstance(x, date):
        # print(f"x is already correct format")
        return x

    for fmt in ("%Y-%m-%d", "%a %b %d"):  # supports YYYY-MM-DD, Fri Jul 25
        try:
            stdFormat = datetime.strptime(x, fmt).date()
            return stdFormat
        except ValueError:
            continue
    return pd.NaT  # if none match


def standardize(df): 
    """
    From strings to datetime objecs 
    """
    
    df['IN'] = df['IN'].apply(parse_time_flexible)
    df['OUT'] = df['OUT'].apply(parse_time_flexible)
    df['time'] = df['time'].apply(parse_time_flexible)
    df['DATE'] = df['DATE'].apply(parse_date_flexible)

    return df
















def saveShiftsToDB(shifts, dbPath=SCRIPTS_DIR / SHIFTS_SQL_DB_NAME):
    # Ensure the directory exists (in case the path is nested)
    os.makedirs(dbPath.parent, exist_ok=True)


    # Create the table only if it doesn't already exist
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()
    
    # Add UNIQUE constraint to avoid duplicates
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clock_in TEXT,
            clock_out TEXT,
            lunch_in TEXT,
            lunch_out TEXT,
            rate_type TEXT,
            notes TEXT,
            UNIQUE(clock_in, clock_out)
        )
    """)


    for shift in shifts:
        cur.execute(
            """
            INSERT OR IGNORE INTO shifts (
                clock_in, clock_out, lunch_in, lunch_out, rate_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, 
            (
                shift.clock_in.isoformat() if shift.clock_in else None, 
                shift.clock_out.isoformat() if shift.clock_in else None,
                shift.lunch_in.isoformat() if shift.clock_in else None,
                shift.lunch_out.isoformat() if shift.clock_in else None,
                shift.rate_type.format() if shift.clock_in else None,
                shift.notes.format() if shift.clock_in else None
            )
        )


    conn.commit()
    conn.close()
















def pullShiftsFromDB(dbPath=SCRIPTS_DIR / SHIFTS_SQL_DB_NAME):
    """
    Pull from existing SQL Lite DB that stores the converted versions of the 
    WorkShift instances.
    """
    if not os.path.exists(dbPath):
        print(f"Database file does not exist: {dbPath}")
        return []

    try:
        conn = sqlite3.connect(dbPath)
        cur = conn.cursor()

        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='shifts'
        """)

        if not cur.fetchone():
            print("Table 'shifts' does not exist in the database.")
            return []

        cur.execute("""
            SELECT clock_in, clock_out, lunch_in, lunch_out, rate_type, notes 
            FROM shifts
        """) 

        rows = cur.fetchall()
        shifts = [WorkShift.from_row(row) for row in rows]


    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []


    finally:
        if 'conn' in locals():
            conn.close()


    return shifts







def dateToString(dt, format_str="%Y-%m-%d"):
    """
    Convert various date/time objects to date string
    
    Args:
        dt: string, datetime.date, datetime.time, or datetime object
        format_str: output format (default: "YYYY-MM-DD")
    
    Returns:
        String representation of the date
    """
    
    if isinstance(dt, str):
        return dt  # Already a string, return as-is
    
    elif isinstance(dt, datetime):
        return dt.strftime(format_str)
    
    elif isinstance(dt, date):
        return dt.strftime(format_str)
    
    elif isinstance(dt, time):
        # Time objects don't have date info, use today's date
        today = date.today()
        return today.strftime(format_str)
    
    else:
        raise TypeError(f"Unsupported type: {type(dt)}")

    





def to24HrFloat(theTime):
    """
    Takes a time like 4:30 PM and returns a time like 16.5
    """

    if pd.isna(theTime) or theTime == '':
        return pd.NaT

    
    if isinstance(theTime, str):
        for fmt in ("%I:%M %p", "%H:%M", "%H:%M:%S"):
            try:
                timeObj = datetime.strptime(theTime.strip(), fmt).time()
                return timeObj.hour + timeObj.minute / 60
            except (ValueError, TypeError):
                continue

        raise ValueError(f"Unrecognized format: {theTime}")


    elif isinstance(theTime, datetime):
        return theTime.time().hour + theTime.time().minute / 60 + theTime.time().second / 3600


    elif isinstance(theTime, time):
        return theTime.hour + theTime.minute / 60 + theTime.second / 3600


    else:
        raise TypeError("Unsupported input type")












def printTypes(df):
    """
    Simply prints the datatypes of the most important columns. IN, OUT, DATE, time
    """

    print()
    print(f"=========================================")
    print(f"Testing the types: ")
    for col in df.columns:
        for cell in df[col]:
            if col != 'IN' and col != 'OUT' and col != 'time' and col != 'DATE':
                continue
            print(f"The {cell}\tcell is of type:\t{type(cell)}")
    print(f"=========================================")
    print()





def isValidData(row: tuple, columns: list[str]) -> bool:

    for idx, cell in enumerate(row[1:]):  # skip the Index at position 0
        if columns[idx] in NECESSARY_DATA and (cell is None or (isinstance(cell, float) and np.isnan(cell)) or pd.isna(cell)):
            # print(f"FOUND CELL: \t\"{columns[idx]}\" is \"{cell}\"")
            return False

    return True










def printShifts(shifts: list[WorkShift]):
    print(f"\n======================================================")
    print(f"======================================================")
    print(f"The shifts are\n")

    for shift in shifts: 
        print()
        shift.view

    print(f"\n======================================================")
    print(f"======================================================")





