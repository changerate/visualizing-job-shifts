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
from utilities.workshift_data import WORKSHIFT_NAMES, GOOGLE_SHEET_COL_NAMES
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
    
    # newShift = WorkShift(
    #     clock_in=datetime(2025, 7, 25, 16), 
    #     clock_out=datetime(2025, 7, 25, 20), 
    #     notes="ANOTHER FREAKING SHIFT???"
    # )
    
    newShift = parsePunchesIntoOneShift()
    
    sheetManager.addNewShiftToSheet(newShift)
    
    
    


















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
            clockIn = allTimePunches[0]
            clockOut = allTimePunches[1]
            newShift = WorkShift(clock_in=clockIn, clock_out=clockOut,)
            allTimePunches = newShift
            
        elif len(allTimePunches) != 4: 
            print(f"Invalid number of punches for a shift! Punches: {len(allTimePunches)}")
            return None
        

    except Exception as e: 
        print(f"Error getting and seperating the punch times: {e}")
        return None

    return allTimePunches











def pullLastUpdatedWorkingSheet(workingSheetsCloset='sheet-closet/working-sheets/', originalSheetsCloset='sheet-closet/original-sheets/'):

    excluded = {"secret.key", "config.key", ".keep"}

    # Get the name of the last updated csv file in the working sheet closet 
    files = [os.path.join(workingSheetsCloset, f) for f in os.listdir(workingSheetsCloset)]
    files = [f for f in files if os.path.isfile(f) and os.path.basename(f) not in excluded]

    if not files: 
        print(f"Notice: No working sheets stored. Pulling from the original's closet.")
        # pull from original sheets instead and update working sheets
        # Get the name of the last updated csv file in the ORIGINALS sheet closet 
        origFiles = [os.path.join(originalSheetsCloset, f) for f in os.listdir(originalSheetsCloset)]
        origFiles = [f for f in origFiles if os.path.isfile(f) and os.path.basename(f) not in excluded]
        
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
    









def clearNaNCols(df, threshold=0.30, yearDivider='YEAR SELECTOR'):     
    """
    Remove columns that are over 'threshold' percent NaN
    """
    try: 
    
        # first deal with the '' left in the cells by Google
        try: 
            df.drop('', axis=1, inplace=True)
        except:
            pass
        try: 
            df.replace('', np.nan, inplace=True)
        except:
            pass

        colsToCheck = list(df.columns)
        
        for col in colsToCheck: 
            numNaN = df[col].isna().sum()
            percentEmpty = numNaN / len(df)

            if percentEmpty > threshold and col != yearDivider: 
                df.drop(col, axis=1, inplace=True)


    except Exception as e: 
        print(f"Something went wrong when cleaning the NaN rows: {e}")
    
    return df









def addNewShift(shifts: list[WorkShift], punchTimes):
    if len(punchTimes) == 0: 
        return shifts

    inTime = punchTimes[0].clock_in.time()
    newDate = punchTimes[0].clock_in.date()
    lunchIn = datetime(1, 1, 1, 1)
    lunchOut = datetime(1, 1, 1, 1)

    if len(punchTimes) == 2: 
        outTime = punchTimes[1].time()

    elif len(punchTimes) == 4:
        lunchIn = punchTimes[1].time()
        lunchOut = punchTimes[2].time()
        outTime = punchTimes[3].time()
    
    else: 
        print(f"Error. Invalid number of punches in a day: {len(punchTimes)}")
        return shifts

    newShift = WorkShift(
        clock_in=inTime,
        lunch_in=lunchIn,
        lunch_out=lunchOut,
        clock_out=outTime,
    )
        
    return shifts.append(newShift)


    
    
    
    
    
    
    


def cleanData(df, winterBreak=False):
    """
    Cleaning a dataframe for proper use.

    Cleaning steps: 
    1. convert to proper time objects 
    2. Add correct year to data like "Fri Jul 25"
        NOTE: Perhaps instead of relying on stupid hardcoding, just calculate 
        whether each date could possibly exist. For example, Fri Jul 25 
        is impossible in 2024!
    3. convert to proper date objects 
    4. remove any periods that are not interesting 
    5. remove skip lunch column
    """
            
    ## Remove any periods that are not interesting 
    if not winterBreak: 
        ## Remove shifts during winter break (2025)
        if CURRENT_YEAR == '2025':
            # print(f"Date type is: {type(df['DATE'])}")
            # print(f"Date is: {df['DATE']}")
            df = df[df['DATE'] >= date(2025, 5, 1)]

    ## Remove skip lunch column lol
    try: 
        df.drop('skip lunch', axis=1, inplace=True)
    except: 
        print(f"Column 'skip lunch' not found")

    return df






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






def saveToCloset(df, workingSheetsCloset='sheet-closet/working-sheets/'):
    dfCopy = copy.deepcopy(df)

    # Ensure target directory exists
    Path(workingSheetsCloset).mkdir(parents=True, exist_ok=True)

    dfCopy = toStringCSV(dfCopy)

    # Create a timestamped filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    filename = f'my-sheet-{timestamp}.csv'
    filepath = Path(workingSheetsCloset) / filename

    # Save the DataFrame
    dfCopy.to_csv(filepath, index=False)
    print(f'\n\nSaved to: {filepath}')











def plot(shifts, minDate, maxDate): 
    """
    PLOTTING
    """
        
    fig, ax = plt.subplots(figsize=(20, 6))
    numShifts = 0
    

    for shift in shifts: 
        if shift.clock_in <= minDate or shift.clock_in >= maxDate:
            continue

        numShifts += 1

        # label full shifts light green
        color = 'skyblue'
        if shift.hours_worked() >= 8:
            color='lightgreen'

        ax.bar(
            x=shift.clock_in.date(),
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

    df = standardize(df)

    shifts = []


    for row in df.itertuples():
        if not isValidData(row, df.columns):
            continue
        
        date = row.DATE

        newShift = WorkShift(
            clock_in=datetime.combine(date, row.IN),
            clock_out=datetime.combine(date, row.OUT),
            rate_type='staples copy center',
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






def labelYears(df, yearDivider='YEAR SELECTOR') -> pd.DataFrame:

    ## Label 2023 and 2024 data
    lastRowOf2024 = len(df)
    firstRowOf2024 = len(df)
    
    
    if CURRENT_YEAR == '2024':
        # Find the last row of 2024
        for idx, cell in df[yearDivider].items():

            if cell == '2024  ⬆️':
                lastRowOf2024 = idx


    elif CURRENT_YEAR == '2025':
        # Find the first row of 2024
        for idx, cell in df[yearDivider].items():

            if cell == '2024 ⬇️':
                firstRowOf2024 = idx
        
        
    ## Convert to correct date format
    if CURRENT_YEAR == '2024':
        df['DATE'].iloc[0:lastRowOf2024] = pd.to_datetime(df['DATE'].iloc[0:lastRowOf2024] + ' ' + CURRENT_YEAR, errors='coerce').dt.date
        df['DATE'].iloc[lastRowOf2024:len(df)] = pd.to_datetime(df['DATE'].iloc[lastRowOf2024:len(df)] + ' 2023', errors='coerce').dt.date


    elif CURRENT_YEAR == '2025': 
        df.loc[0:firstRowOf2024, 'DATE'] = pd.to_datetime(
            df.loc[0:firstRowOf2024, 'DATE'].astype(str) + f' {CURRENT_YEAR}',
            format='%a %b %d %Y',
            errors='coerce'
        ).dt.date
        df.loc[firstRowOf2024:len(df), 'DATE'] = pd.to_datetime(
            df.loc[firstRowOf2024:len(df), 'DATE'].astype(str) + f' 2024',
            format='%a %b %d %Y', 
            errors='coerce'
            ).dt.date

    return df



















if __name__ == '__main__':
    main()
