# Visualizing the shifts that I've worked at Staples
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import datetime, date, time
import argparse
import numpy as np
import os
import copy 
import sqlite3

import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# user made files 
from utilities.workshift_data import SHEET_TO_WORKSHIFT_COLS, GOOGLE_SHEET_COL_TYPES
from classes.shiftClass import WorkShift
from classes.googleSheetClass import GoogleSheetManager
from utilities.necessary_data import NECESSARY_DATA
from utilities.ut_functions import *









SCRIPTS_DIR = Path(__file__).parent

parser = argparse.ArgumentParser(description="Visualize Staples shifts.")
parser.add_argument('--csv', type=str, default=SCRIPTS_DIR / 'sheet-closet/original-sheets/Staples Finances 2025.csv', help='CSV file name')
parser.add_argument('--year', type=str, default='2025', help='Year of data (2024 or 2025)')
parser.add_argument('--punchTimes', type=str, default='', help='Punch times (Date Time or Time) seperated by new line character.')
parser.add_argument('--pullSheetsFirst', type=str, default=False, help='First pull from Google Sheets.')
parser.add_argument('--sheetName', type=str, default="Staples Finances 2025", help='Name of the Google Sheet.')
args = parser.parse_args()


CSV_NAME = args.csv
CURRENT_YEAR = args.year
PUNCH_TIMES = args.punchTimes
PULL_SHEETS_FIRST = args.pullSheetsFirst
SHIFTS_SQL_DB_NAME = 'databases/shifts.db'
SHEET_NAME = args.sheetName










# ==============================================================================
#            MAIN FUNCTION
# ==============================================================================



def main():
    if not checkYear():
        exit()

    sheetManager = GoogleSheetManager(sheet_name=SHEET_NAME)

    # get shifts from sheets
    df = sheetManager.get_dataframe_of_sheet()

    shifts = []
    if PUNCH_TIMES:    
        newShift = parsePunchesIntoOneShift()    
        sheetManager.add_new_shift_to_sheet(newShift)
        shifts = [newShift]
    else: 
        print(f"\nNo new shifts to parse")
    
    
    # Save to SQL DB 
    shifts += collectShiftsFromDataFrame(df)
    saveShiftsToDB(shifts)

    plot(shifts)
    
    









def parsePunchesIntoOneShift() -> WorkShift: 
    """
    Capture the time punches entered from the command line
    Returns: empty list or a list of the punch dates and times in the WorkShift format 

    This also keeps track of the number of punches on the same day.
    """

    if not PUNCH_TIMES: 
        # punch times from the command line 
        print(f"Warning: No punch times entered.")
        return None

    
    allTimePunches = set()
    try: 
        
        # convert the punch to a WorkShift object
        punchTimes = PUNCH_TIMES.split('\n')
        for punchTime in punchTimes:
            if punchTime:
                allTimePunches.add(datetime.strptime(punchTime, "%b %d, %Y at %I:%M %p"))

        allTimePunches = sorted(allTimePunches)

        # Check if there's the correct number of punches
        if len(allTimePunches) == 2:
            newShift = WorkShift(
                date=allTimePunches[0].date(),
                clock_in=allTimePunches[0].time(),
                clock_out=allTimePunches[1].time(),
            )
            allTimePunches = newShift
            
        elif len(allTimePunches) != 4: 
            print(f"Invalid number of punches for a shift! Punches: {len(allTimePunches)}")
            return None
        

    except Exception as e: 
        print(f"Error getting and seperating the punch times: {e}")
        return None

    return allTimePunches










def cleanEmptyColumns(df, threshold=0.30):     
    """
    Remove columns that are over 'threshold' percent empty
    """
    try: 
    
        # first, drop columns that don't have a name
        try: 
            df.drop('', axis=1, inplace=True)
        except:
            pass

        colsToCheck = list(df.columns)
        
        for col in colsToCheck: 
            numEmpty = (df[col] == '').sum()
            percentEmpty = numEmpty / len(df)

            notesCol = next(k for k, v in SHEET_TO_WORKSHIFT_COLS.items() if v == 'notes')
            if percentEmpty > threshold and col != notesCol: 
                df.drop(col, axis=1, inplace=True)


    except Exception as e: 
        print(f"Something went wrong when cleaning the empty columns: {e}")
    
    return df





    
    
    
    
    
    


def cleanData(df, winterBreak=False):
    """
    Cleaning a dataframe for proper use.

    Cleaning steps: 
    - clear NaN cols
    - convert to proper time objects 
    - convert to proper date objects 
    - remove skip lunch column
    """
    
    df = cleanEmptyColumns(df)

    ## Remove skip lunch column lol
    try: 
        df.drop('skip lunch', axis=1, inplace=True)
    except: 
        print(f"Column 'skip lunch' not found")

    return df















def plot(shifts: list[WorkShift], minDate=date(2025, 2, 1), maxDate=date(9999, 1, 1)): 
    """
    PLOTTING
    """
        
    fig, ax = plt.subplots(figsize=(20, 6))
    numShifts = 0
    

    for shift in shifts: 
        if shift.date <= minDate or shift.date >= maxDate:
            continue

        numShifts += 1

        # label full shifts light green
        color = 'skyblue'
        if shift.hours_worked() >= 8:
            color='lightgreen'

        ax.bar(
            x=shift.date,
            height=shift.hours_worked(),
            bottom=to24HrFloat(shift.clock_in),
            label='shift',
            width=0.93,
            color=color
        )


    # title 
    if CURRENT_YEAR == '2025':
        ax.set_title("2025 Summer Break Shifts at Staples")
    else: 
        ax.set_title("2023-24 Shifts at Staples")


    # format y axis
    ax.set_ylabel("Time of Day (24hr)")
    ax.set_yticks(range(8, 22, 2))
    ax.set_yticklabels([f"{h}:00" for h in range(8, 22, 2)])
    ax.yaxis.grid(True, which='major', color="#EBEBEB")


    # format x axis 
    ax.set_xlabel("Day")
    ax.tick_params(axis='x', rotation=45)


    if CURRENT_YEAR == '2025':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    else: 
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %Y'))
    
    print(f"The number of shifts: {numShifts}")

    interv = max(1, -(-numShifts // 18))  # ensures interval ≥ 1
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interv))


    # custom legend entries
    legend_elements = [
        Patch(facecolor='skyblue', label='Part Time Shift (<8h)'),
        Patch(facecolor='lightgreen', label='Full Shift (≥8h)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', title='Shift Length')

    plt.show()












def collectShiftsFromDataFrame(df):

    df = cleanData(df)
    shifts = []

    print()
    print(f"Checking the validity of the rows: ")
    for _, row in df.iterrows():
        
        if not isValidShiftRow(row, df.columns):
            continue
        
        # This data is essentially allowed to be blank
        lunchIn  = row[WORKSHIFT_TO_SHEET_COLS['lunch_in']]  if not pd.isna(row[WORKSHIFT_TO_SHEET_COLS['lunch_in']])  else time(1)
        lunchOut = row[WORKSHIFT_TO_SHEET_COLS['lunch_out']] if not pd.isna(row[WORKSHIFT_TO_SHEET_COLS['lunch_out']]) else time(1)
        
        newShift = WorkShift(
            date=row[WORKSHIFT_TO_SHEET_COLS['date']],
            clock_in=row[WORKSHIFT_TO_SHEET_COLS['clock_in']],
            clock_out=row[WORKSHIFT_TO_SHEET_COLS['clock_out']],
            lunch_in=lunchIn,
            lunch_out=lunchOut,
            rate_type='staples copy center',
            notes=row[WORKSHIFT_TO_SHEET_COLS['notes']],
        )

        shifts.append(newShift)

    return shifts











# =====================================================================
#           MORE UTILITY FUNCTIONS
# =====================================================================


def checkYear():
    try: 
        # year checking
        if 2022 >= int(CURRENT_YEAR) or int(CURRENT_YEAR) > 2025: # This needs to be updated to the 'current' year 
            print(f"Error. Incorrect parameters entered: {CURRENT_YEAR}")
            return False
            
    except Exception as e: 
        print(f"Error. Incorrect parameters entered: \n{e}")
        return False

    return True























if __name__ == '__main__':
    main()
