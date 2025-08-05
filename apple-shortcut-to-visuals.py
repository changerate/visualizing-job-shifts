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
from classes.shiftClass import WorkShift
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
SHEET_NAME = args.sheetName
SHIFTS_SQL_DB_NAME = 'database.db'










# ==============================================================================
#            MAIN FUNCTION
# ==============================================================================



def main():
    if not checkYear():
        exit()
        
        
    # initialization
    gglSheetManager = GoogleSheetManager(sheet_name=SHEET_NAME)
    shiftMngr = ShiftManager()

    # check if there's shifts to parse from arguments 
    shifts = []
    if PUNCH_TIMES: 
        newShift = shiftMngr.parse_punches_into_shift(PUNCH_TIMES)
        shifts = [newShift]

        # update google sheet
        gglSheetManager.add_new_shift_to_sheet(newShift)
    else: 
        print(f"\nNo new shifts to parse")
    
    
    df = gglSheetManager.get_dataframe_of_sheet() # this does not account for the new shift(s) added
    shifts += shiftMngr.collect_shifts_from_dataframe(df)
    shiftMngr.save_shifts_to_db(shifts)

    shiftMngr.plot(shifts, currentYear=CURRENT_YEAR)


























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
