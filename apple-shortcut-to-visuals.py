# Visualizing the shifts that I've worked at retail jobs

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
from classes.workShiftClass import WorkShift
from classes.googleSheetClass import GoogleSheetManager
from classes.shiftManagerClass import ShiftManager
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
SHIFTS_SQL_DB_NAME = 'database.db'
SHEET_NAME = args.sheetName










# ==============================================================================
#            MAIN FUNCTION
# ==============================================================================



def main():
    if not checkYear():
        exit()

    sheetManager = GoogleSheetManager(sheet_name=SHEET_NAME)
    shiftManager = ShiftManager()


    # get shifts from sheets
    df = sheetManager.get_dataframe_of_sheet()

    shifts = []
    if PUNCH_TIMES:    
        newShift = shiftManager.parse_punches_into_shift()
        sheetManager.add_new_shift_to_sheet(newShift)
        shifts = [newShift]
    else: 
        print(f"\nNo new shifts to parse")
    
    
    # Save to SQL DB 
    shifts += shiftManager.collect_shifts_from_dataframe(df)
    shiftManager.save_shifts_to_db(shifts)

    shiftManager.plot(shifts)
    
    



# def main():
#     if not checkYear():
#         exit()

#     sheetManager = GoogleSheetManager(sheet_name=SHEET_NAME)
#     shiftManager = ShiftManager()


#     # get shifts from sheets
#     df = sheetManager.get_dataframe_of_sheet()

#     shifts = []
#     if PUNCH_TIMES:    
#         newShift = shiftManager.parse_punches_into_shift()
#         sheetManager.add_new_shift_to_sheet(newShift)
#         shifts = [newShift]
#     else: 
#         print(f"\nNo new shifts to parse")
    
    
#     # Save to SQL DB 
#     shifts += shiftManager.collect_shifts_from_dataframe(df)
#     shiftManager.save_shifts_to_db(shifts)

#     shiftManager.plot(shifts)
    
    

















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
