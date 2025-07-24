import pandas as pd
from datetime import datetime, date, time
import numpy as np
import os

from classes.shiftClass import WorkShift
from utilities.necessary_data import NECESSARY_DATA
from utilities.ut_functions import *






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





def pullLastUpdatedWorkingSheet(workingSheetsCloset='sheet-closet/working-sheets/', originalSheetsCloset='sheet-closet/original-sheets/'):

    # Get the name of the last updated csv file in the working sheet closet 
    files = [os.path.join(workingSheetsCloset, f) for f in os.listdir(workingSheetsCloset)]
    files = [f for f in files if os.path.isfile(f)]

    if not files: 
        print(f"Notice: No working sheets stored. Pulling from the original's closet.")
        # pull from original sheets instead and update working sheets
        # Get the name of the last updated csv file in the ORIGINALS sheet closet 
        origFiles = [os.path.join(originalSheetsCloset, f) for f in os.listdir(originalSheetsCloset)]
        origFiles = [f for f in origFiles if os.path.isfile(f)]
        
        if not origFiles: 
            print(f"Error: No original sheets stored.")
            return pd.DataFrame([])

        csvName = max(origFiles, key=os.path.getmtime)
        # print(f"Updating the working sheets with {csvName}.")

        df = pd.DataFrame(pd.read_csv(csvName))
        return df

    else: 
        csvName = max(files, key=os.path.getmtime)
        print(f"Pulling working sheet: {csvName}")
        return pd.DataFrame(pd.read_csv(csvName))
    









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





