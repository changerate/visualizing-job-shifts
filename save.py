SHEET_NAME = "Copy of Staples Finances 2025"
CURRENT_YEAR = '2025'

from classes.googleSheetClass import GoogleSheetManager
from classes.shiftClass import WorkShift
from utilities.ut_functions import *
from utilities.workshift_data import *


def main():
    if not checkYear():
        exit()
    
    sheetManager = GoogleSheetManager(sheet_name=SHEET_NAME)
    # sheetManager.add_new_shift_to_sheet(newShift)
    df = sheetManager.get_dataframe_of_sheet()
    shifts = collect_shifts_from_dataframeFromDataFrame(df)
    print_shifts(shifts)
    
    


    # newShift = WorkShift(
    #     date=date(2025, 7, 25),
    #     clock_in=time(16), 
    #     lunch_in=time(18),
    #     lunch_out=time(18, 30),
    #     clock_out=time(20), 
    #     notes="ANOTHER FREAKING SHIFT???"
    # )

    
    # # newShift = parse_punches_IntoOneShift()    
    
    
    
    # # Save to SQL DB 
    
    
    # saveShiftsToDB([newShift] + shifts)
    
    
    
    


def collect_shifts_from_dataframeFromDataFrame(df):

    df = clean_data(df)
    shifts = []

    print()
    print(f"Checking the validity of the rows: ")
    for _, row in df.iterrows():
        
        if not is_valid_shift_row(row, df.columns):
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



def clean_empty_cols(df, threshold=0.30):     
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





    
    
    
    
    
    


def clean_data(df, winterBreak=False):
    """
    Cleaning a dataframe for proper use.

    Cleaning steps: 
    - clear NaN cols
    - convert to proper time objects 
    - convert to proper date objects 
    - remove skip lunch column
    """
    
    df = clean_empty_cols(df)

    ## Remove skip lunch column lol
    try: 
        df.drop('skip lunch', axis=1, inplace=True)
    except: 
        print(f"Column 'skip lunch' not found")

    return df





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




    

main()