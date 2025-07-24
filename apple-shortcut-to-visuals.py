# Visualizing the shifts that I've worked at Staples
# This comes from my Google Sheets
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import datetime, date, time
import argparse
import numpy as np
import os
import copy 

import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# user made files 
from classes.shiftClass import WorkShift
from utilities.necessary_data import NECESSARY_DATA
from utilities.ut_functions import *


import sqlite3








SCRIPTS_DIR = Path(__file__).parent

parser = argparse.ArgumentParser(description="Visualize Staples shifts.")
parser.add_argument('--csv', type=str, default=SCRIPTS_DIR / 'sheet-closet/original-sheets/Staples Finances 2025.csv', help='CSV file name')
parser.add_argument('--year', type=str, default='2025', help='Year of data (2024 or 2025)')
parser.add_argument('--punchTimes', type=str, default='', help='Punch times (Date Time or Time) seperated by new line character.')
parser.add_argument('--pullSheetsFirst', type=str, default=False, help='First pull from Google Sheets.')
args = parser.parse_args()


CSV_NAME = args.csv
CURRENT_YEAR = args.year
PUNCH_TIMES = args.punchTimes
PULL_SHEETS_FIRST = args.pullSheetsFirst











def loadFromGoogleSheets(sheetName="Staples Finances 2025"): 
    """
    URGENT: UPDATE THIS TO SAVE INTO THE ORIGINALS DIR.
    """

    try: 
        env_path = SCRIPTS_DIR / ".env"
        load_dotenv(dotenv_path=env_path)  # automatically looks for .env in the scripts directory

        creds_path = SCRIPTS_DIR / os.getenv("GOOGLE_SHEETS_CREDS_FILE")
        
        # Define the scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)

        # Authorize
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)

        # Open sheet by name or URL
        sheet = client.open(sheetName).sheet1
        data = sheet.get_all_values()

        # Create DataFrame using first row as header
        df = pd.DataFrame(data[1:], columns=data[0])

        return df


    except Exception as e: 
        print(f"{e}")
        return pd.DataFrame([])










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








def parsePunches(): 
    """
    Capture the time punches entered from the command line
    Returns: empty list or a list of the punch dates and times in the datetime object format

    This also keeps track of the number of punches on the same day.
    """

    if not PUNCH_TIMES: 
        print(f"Warning: No punch times entered.")
        return []

    
    allTimePunches = set()
    try: 
        
        # convert the punch to a datetime object
        punchTimes = PUNCH_TIMES.split('\n')
        for punchTime in punchTimes:
            if punchTime:   
                allTimePunches.add(datetime.strptime(punchTime, "%b %d, %Y at %I:%M %p"))

        
        # Count the number of punches in the day 
        # punchTimes = sorted(allTimePunches)
        # lastDay = 100
        # punchNums = []
        # punchNum = 0
        # for punchTime in punchTimes:
            
        #     if not punchTime: 
        #         continue
            
        #     if punchTime.day == lastDay:
        #         # either update the number of punches on the date...
        #         punchNum += 1
        #         punchNums.append(punchNum)
        #     else: 
        #         # or reset back to one punch for a new day 
        #         lastDay = punchTime.day
        #         punchNum = 1 
        #         punchNums.append(punchNum)

        # punchTimes = sorted(zip(punchTimes, punchNums))
        
        
        # Check if there's the correct number of punches
        if len(punchTimes) != 2 and len(punchTimes) != 4: 
            print(f"Invalid number of punches for a shift! Punches: {len(punchTimes)}")
            return []
        

    except Exception as e: 
        print(f"Error getting and seperating the punch times: {e}")
        return []

    return sorted(punchTimes)








def addNewShift(shifts: list[WorkShift], punchTimes):
    if len(punchTimes) == 0: 
        return shifts

    inTime = punchTimes[0].time()
    newDate = punchTimes[0].date()
    lunchIn = datetime(1, 1, 1, 1)
    lunchOut = datetime(1, 1, 1, 1)

    if len(punchTimes) == 2: 
        outTime = punchTimes[1].time()

    elif len(punchTimes) == 4:
        lunchIn = punchTimes[1].time()
        lunchOut = punchTimes[2].time()
        outTime = punchTimes[3].time()
    
    else: 
        print(f"Error. Invalid number of punches in a day.")
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











def plot(df): 
    """
    PLOTTING
    """
        
    fig, ax = plt.subplots(figsize=(20, 6))


    for _, row in df.iterrows():
        if pd.isna(row['DATE']) or pd.isna(row['IN']) or pd.isna(row['OUT']):
            continue
        if row['DATE'] == '' or row['IN'] == '' or row['OUT'] == '':
            continue
        
        duration = to24HrFloat(row['OUT']) - to24HrFloat(row['IN'])
            
        # label full shifts light green
        color = 'skyblue'
        if duration >= 8:
            color='lightgreen'
        
        ax.bar(x=row['DATE'],
            height=duration,
            bottom=to24HrFloat(row['IN']),
            label='shift',
            width=0.93,
            color=color)


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
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=round(len(df) / 18)))


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






def labelYears(df, yearDivider='YEAR SELECTOR'):

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







def saveShiftsToDB(shifts, dbPath=SCRIPTS_DIR / 'databases/shifts.db'):
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS shifts")
    cur.execute("""
        CREATE TABLE shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clock_in TEXT,
            clock_out TEXT,
            lunch_in TEXT,
            lunch_out TEXT,
            rate_type TEXT,
            notes TEXT
        )
    """)


    for shift in shifts:
        cur.execute(
            """
            INSERT INTO shifts (
                clock_in, clock_out, lunch_in, lunch_out, rate_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, 
            (
                shift.clock_in.isoformat(), 
                shift.clock_out.isoformat(),
                shift.lunch_in.isoformat(),
                shift.lunch_out.isoformat(),
                shift.rate_type.format(),
                shift.notes.format()
            )
        )


    conn.commit()
    conn.close()







def loadShifts(dbPath=SCRIPTS_DIR / 'databases/shifts.db'):
    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()

    cur.execute("""
        SELECT clock_in, clock_out, lunch_in, lunch_out, rate_type, notes 
        FROM shifts
    """) 

    shifts = [WorkShift.from_row(row) for row in cur.fetchall()]
    conn.close()
    return shifts





















# =====================================================================
#            MAIN FUNCTION
# =====================================================================


if __name__ == '__main__':
    
    if not checkYear():
        exit()
    
    
    punchTimes = parsePunches()
    
    
    if PULL_SHEETS_FIRST: 
        # Pull directly from Google Sheets
        df = loadFromGoogleSheets()

        df.to_csv(CSV_NAME, index=False, float_format="%.2f")

        if df.empty:
            exit()
        df = labelYears(df)


    else: 
        # Pull from the existing sheet closet 
        df = pullLastUpdatedWorkingSheet()
        if df.empty:
            exit()

    shifts = collectShiftsFromDataFrame(df)

    if not shifts: 
        exit()
    
    shifts = addNewShift(shifts, punchTimes)

    saveShiftsToDB(shifts)
    shifts = []
    shifts = loadShifts()
    printShifts(shifts)
    # plot(df)