# Visualizing the shifts that I've worked at Staples
# This comes from my Google Sheets
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import date
from datetime import datetime
from pathlib import Path
import argparse
import os


parser = argparse.ArgumentParser(description="Visualize Staples shifts.")
parser.add_argument('--csv', type=str, default='/Users/carlos_1/Documents/GitHub/visualizing-job-shifts/Staples Finances 2025.csv', help='CSV file name')
parser.add_argument('--year', type=str, default='2025', help='Year of data (2024 or 2025)')
parser.add_argument('--punchTimes', type=str, help='Punch times (Date Time or Time) seperated by new line character.')
parser.add_argument('--pullSheetsFirst', type=str, default=False, help='First pull from Google Sheets.')
args = parser.parse_args()



CSV_NAME = args.csv
CURRENT_YEAR = args.year
PUNCH_TIMES = args.punchTimes
PULL_SHEETS_FIRST = args.pullSheetsFirst







def clearNaNCols(df, threshold=0.30, yearDivider='YEAR SELECTOR'):     
    """
    Remove columns that are over 'threshold' NaN
    yearDivider the name of a column containing mostly barren cells. 
    Its purpose is to divide between upper and lower years. 
    The default name of the column is YEAR SELECTOR.
    """
    try: 
        for col in df.columns: 
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
            print(f"Invalid numnber of punches for a shift! Punches: {len(punchTimes)}")
            return False
        

    except Exception as e: 
        print(f"Error getting and seperating the punch times: {e}")
        return []

    return punchTimes








def appendNewTimes(df, punchTimes):

    inTime = punchTimes[0][0].strftime("%H:%M %p")
    date = punchTimes[0][0].strftime("%a %b %d")
    # print(f"date: {date}")

    if len(punchTimes) == 2: 
        outTime = punchTimes[1][0].strftime("%H:%M")
        hours = to24hr(outTime)-to24hr(inTime)
        newRow = {"DATE": date, "IN": inTime, "OUT": outTime, "hours": hours}

    elif len(punchTimes) == 4:
        outTime = punchTimes[3][0].strftime("%H:%M")
        lunchIn = punchTimes[1][0].strftime("%H:%M")
        lunchOut = punchTimes[2][0].strftime("%H:%M")
        hours = to24hr(outTime)-to24hr(inTime)-(to24hr(lunchIn)-to24hr(lunchIn))
        newRow = {
            "DATE": date,
            "IN": inTime,
            "LUNCH IN": lunchIn,
            "LUNCH OUT": lunchOut,
            "OUT": outTime,
            "hours": hours
        }
        
    else: 
        print(f"Error. Invalid number of punches in a day.")

    print(newRow)

    return pd.concat([pd.DataFrame([newRow]), df], ignore_index=True)


    
    
    
    
    
    
    


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

    
    ## Convert to correct time format
    df['IN'] = pd.to_datetime(df['IN'], errors='coerce').dt.time
    df['OUT'] = pd.to_datetime(df['OUT'], errors='coerce').dt.time
        

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
            # format='%a %b %d %Y',
            errors='coerce'
        ).dt.date
        df.loc[firstRowOf2024:len(df), 'DATE'] = pd.to_datetime(
            df.loc[firstRowOf2024:len(df), 'DATE'].astype(str) + f' 2024',
            # format='%a %b %d %Y', 
            errors='coerce'
            ).dt.date


    ## Remove any periods that are not interesting 
    if not winterBreak: 
        ## Remove shifts during winter break (2025)
        if CURRENT_YEAR == '2025':
            df = df[df['DATE'] >= date(2025, 5, 1)]


    ## Remove skip lunch column lol
    try: 
        df.drop('skip lunch', axis=1, inplace=True)
    except: 
        print(f"Column 'skip lunch' not found")

    return df








def saveToCloset(df, workingSheetsCloset='sheet-closet/working-sheets/'): 
    # Ensure target directory exists
    Path(workingSheetsCloset).mkdir(parents=True, exist_ok=True)

    # Create a timestamped filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f'my-sheet-{timestamp}.csv'
    filepath = Path(workingSheetsCloset) / filename

    # Save the DataFrame
    df.to_csv(filepath, index=False)
    print(f'Saved to: {filepath}')    
    










def plot(df): 
    """
    PLOTTING
    """
    fig, ax = plt.subplots(figsize=(20, 6))

    # plot 
    for _, row in df.iterrows():

        if row['DATE'] == 'NaT':
            continue

        duration = (row['OUT'].hour + row['OUT'].minute / 60) - (row['IN'].hour + row['IN'].minute / 60)
        color = 'skyblue'
        if duration >= 8:
            color='lightgreen'
        
        ax.bar(x=row['DATE'],
                height=duration,
                bottom=row['IN'].hour + row['IN'].minute / 60,
                width=0.93,
                label='shift',
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
        # df.to_csv(csvName, index=False)
        return df

    else: 
        csvName = max(files, key=os.path.getmtime)
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





def to24hr(strTime: str):
    """
    Takes a time like 4:30 PM and returns a time like 16.5
    """
    for fmt in ("%I:%M %p", "%H:%M", "%H:%M:%S"):
        try:
            timeObj = datetime.strptime(strTime.strip(), fmt).time()
            return timeObj.hour + timeObj.minute / 60
        except (ValueError, TypeError):
            continue

    raise ValueError(f"Unrecognized format: {strTime}")










# =====================================================================
#            MAIN FUNCTION
# =====================================================================


if __name__ == '__main__':
    
    if not checkYear():
        exit()
    
    punchTimes = parsePunches()
    if not punchTimes: 
        exit() # Invalid number of punches
    
    if PULL_SHEETS_FIRST: 
        pass
        # This needs to be updated!
    else: 
        # Pull from the existing sheet closet 
        df = pullLastUpdatedWorkingSheet()
    
    df = clearNaNCols(df)

    if not df.empty: 
        df = appendNewTimes(df, punchTimes)
        df = cleanData(df)

        print(df)
        # saveToCloset(df)
        # plot(df)