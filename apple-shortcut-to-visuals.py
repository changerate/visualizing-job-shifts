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




parser = argparse.ArgumentParser(description="Visualize Staples shifts.")
parser.add_argument('--csv', type=str, default='/Users/carlos_1/Documents/GitHub/visualizing-job-shifts/Staples Finances 2025.csv', help='CSV file name')
parser.add_argument('--year', type=str, default='2025', help='Year of data (2024 or 2025)')
parser.add_argument('--punchTimes', type=str, default='', help='Punch times (Date Time or Time) seperated by new line character.')
parser.add_argument('--pullSheetsFirst', type=str, default=False, help='First pull from Google Sheets.')
args = parser.parse_args()



CURRENT_YEAR = args.year
PUNCH_TIMES = args.punchTimes
PULL_SHEETS_FIRST = args.pullSheetsFirst
SCRIPTS_DIR = Path(__file__).parent











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
    yearDivider the name of a column containing mostly barren cells. 
    Its purpose is to divide between upper and lower years. 
    The default name of the column is YEAR SELECTOR.
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

    turns it into a list if tuples: 
    [(datetime.datetime(yr, mm, dd, hr, m), num_punches), (datetime.datetime(yr, mm, dd, hr0,m22), num_punches)]
    """

    if not PUNCH_TIMES: 
        print(f"Warning: No punch times entered.")
        return []
    
    punchTimesSet = set()
    try: 
        
        # convert the timestamp to a datetime object
        punchTimes = PUNCH_TIMES.split('\n')
        for punchTime in punchTimes:
            if punchTime: 
                punchTimesSet.add(datetime.strptime(punchTime, "%b %d, %Y at %I:%M %p"))

        
        # Count the number of punches in the day 
        punchTimes = sorted(punchTimesSet)
        lastDay = 100
        punchNums = []
        punchNum = 0
        for punchTime in punchTimes:
            
            if not punchTime: 
                continue
            
            if punchTime.day == lastDay:
                # either update the number of punches on the date...
                punchNum += 1
                punchNums.append(punchNum)
            else: 
                # or reset back to one punch for a new day 
                lastDay = punchTime.day
                punchNum = 1 
                punchNums.append(punchNum)

        punchTimes = sorted(zip(punchTimes, punchNums))
        
        
        # Check if there's the correct punch times
        if len(punchTimes) != 2 and len(punchTimes) != 4: 
            print(f"Invalid number of punches for a shift! Punches: {len(punchTimes)}")
            return []
        

    except Exception as e: 
        print(f"Error getting and seperating the punch times: {e}")
        return []

    return punchTimes








def appendNewTimes(df, punchTimes):
    if len(punchTimes) == 0: 
        return df

    inTime = punchTimes[0][0].time()
    newDate = punchTimes[0][0].date()

    if len(punchTimes) == 2: 
        outTime = punchTimes[1][0].time()
        hours = to24HrFloat(outTime)-to24HrFloat(inTime)
        newRow = {"DATE": newDate, "IN": inTime, "OUT": outTime, "hours": hours}

    elif len(punchTimes) == 4:
        outTime = punchTimes[3][0].time()
        lunchIn = punchTimes[1][0].time()
        lunchOut = punchTimes[2][0].time()
        hours = to24HrFloat(outTime)-to24HrFloat(inTime)-(to24HrFloat(lunchOut)-to24HrFloat(lunchIn))
        newRow = {
            "DATE": newDate,
            "IN": inTime,
            "LUNCH IN": lunchIn,
            "LUNCH OUT": lunchOut,
            "OUT": outTime,
            "hours": hours
        }
        
    else: 
        print(f"Error. Invalid number of punches in a day.")
        return df

    newRow = pd.DataFrame([newRow])
    return pd.concat([newRow, df], ignore_index=True)


    
    
    
    
    
    
    


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








def labelYears(df):

    ## Label 2023 and 2024 data
    lastRowOf2024 = len(df)
    firstRowOf2024 = len(df)
    if CURRENT_YEAR == '2024':
        # Find the last row of 2024
        for idx, cell in df['YEAR SELECTOR'].items():

            if cell == '2024  ⬆️':
                lastRowOf2024 = idx

    elif CURRENT_YEAR == '2025':
        # Find the first row of 2024
        for idx, cell in df['YEAR SELECTOR'].items():

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

        df.to_csv(SCRIPTS_DIR / "my_data.csv", index=False, float_format="%.2f")

        if df.empty:
            exit()
        df = labelYears(df)
        df = standardize(df)


    else: 
        # Pull from the existing sheet closet 
        df = pullLastUpdatedWorkingSheet()
        if df.empty:
            exit()
        df = standardize(df)
    
    
    df = clearNaNCols(df)
    

    if df.empty: 
        exit()
    

    df = cleanData(df)
    
    if df.empty: 
        exit()
    
    df = appendNewTimes(df, punchTimes)
    saveToCloset(df)
    plot(df)
