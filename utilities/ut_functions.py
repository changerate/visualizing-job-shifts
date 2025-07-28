import pandas as pd
from datetime import datetime, date, time
import numpy as np
import os
from pathlib import Path
import sqlite3

from classes.shiftClass import WorkShift
from utilities.necessary_data import NECESSARY_DATA
from utilities.workshift_data import *
from utilities.ut_functions import *

SCRIPTS_DIR = Path(__file__).parent.parent
SHIFTS_SQL_DB_NAME = 'databases/shifts.db'





# =====================================================================
#            UTILITY FUNCTIONS
# =====================================================================
















def saveShiftsToDB(shifts: list[WorkShift], dbPath: Path=SCRIPTS_DIR / SHIFTS_SQL_DB_NAME):
    print(f"\nSaving {len(shifts)} shifts to database: {dbPath}.")
    # Ensure the directory exists (in case the path is nested)
    os.makedirs(dbPath.parent, exist_ok=True)

    # Create the table only if it doesn't already exist
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()
    
    # Add UNIQUE constraint to avoid duplicates
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            clock_in TEXT,
            clock_out TEXT,
            lunch_in TEXT,
            lunch_out TEXT,
            rate_type TEXT,
            notes TEXT,
            UNIQUE(date, clock_in, notes)
        )
    """)


    for shift in shifts:
        print(f"Saving shift {shift.date} ... ", end='')
        # print(f"Saving shift {shift.date} in format {shift.date.isoformat()}", end='')
        response = cur.execute(
            """
            INSERT OR IGNORE INTO shifts (
                date, clock_in, clock_out, lunch_in, lunch_out, rate_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, 
            (
                shift.date.isoformat(),
                shift.clock_in.isoformat(),
                shift.clock_out.isoformat(),
                shift.lunch_in.isoformat() if shift.lunch_in else None,
                shift.lunch_out.isoformat() if shift.lunch_out else None,
                shift.rate_type.strip() if shift.rate_type else None,
                shift.notes.strip() if shift.notes else None,
            )
        )
        
        print(f"✔︎")


    conn.commit()
    conn.close()
















def pullShiftsFromDB(dbPath=SCRIPTS_DIR / SHIFTS_SQL_DB_NAME):
    """
    Pull from existing SQL Lite DB that stores the converted versions of the 
    WorkShift instances.
    """
    print(f"\nPulling shifts from database: {dbPath}")

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
            SELECT date, clock_in, clock_out, lunch_in, lunch_out, rate_type, notes 
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

    print(f"Found {len(shifts)} shifts in the db.")
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

    





def to24HrFloat(theTime: time | date | str ):
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
    Simply prints the datatypes of the most important columns. 
    DATE, IN, LUNCH IN, LUNCH OUT, time, hours, notes
    """

    print()
    print(f"==============================================================================")
    print(f"Testing the types: ")
    for col in df.columns:
        for cell in df[col]:
            if col not in GOOGLE_SHEET_COL_TYPES:
                continue
            print(f"Column {col}, \"{cell}\" cell is of type: {type(cell)}")
    print(f"==============================================================================")
    print()





def isValidShiftRow(row, columns: list[str]) -> bool:
    """
    Checks on the basis of data like dateCol, inCol, and outCol.
    If that data is present than it is considered a viable shift.
    """
    dateCell = row[WORKSHIFT_TO_SHEET_COLS['date']]
    inCell = row[WORKSHIFT_TO_SHEET_COLS['clock_in']]
    outCell = row[WORKSHIFT_TO_SHEET_COLS['clock_out']]
    
    print(f"Is it valid? : {row['DATE']}", end='')
    # print(f"{row}")


    if pd.isna(dateCell):
        print(f" INVALID ✖︎")
        return False
        
    if pd.isna(inCell):
        print(f" INVALID ✖︎")
        return False

    if pd.isna(outCell):
        print(f" INVALID ✖︎")
        return False

    print(f" kept! ✔︎")
    return True










def printShifts(shifts: list[WorkShift]):
    print(f"\n\n======================================================")
    print(f"======================================================")
    print(f"\tTHE SHIFTS ARE:")

    for shift in shifts: 
        print()
        shift.view

    print(f"\n======================================================")
    print(f"======================================================")









def toStringCSV(df): 
    """
    Format time/date columns as strings
    """
    # printTypes(df)        

    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            if isinstance(sample, time):
                df[col] = df[col].apply(lambda t: t.strftime("%H:%M") if pd.notna(t) else '')
            elif isinstance(sample, date):
                df[col] = df[col].apply(lambda d: d.strftime("%Y-%m-%d") if pd.notna(d) else '')

    return df