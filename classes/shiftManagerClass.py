# shift manager class 
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from datetime import datetime, date, time
import os
import sqlite3

from pathlib import Path

# user made files 
from utilities.workshift_data import SHEET_TO_WORKSHIFT_COLS
from classes.workShiftClass import WorkShift
from utilities.ut_functions import *


SCRIPTS_DIR = Path(__file__).parent.parent
SHIFTS_SQL_DB_NAME = 'database.db'





class ShiftManager:
    def __init__(self):
        pass












    def parse_punches_into_shift(self, punchTimes) -> WorkShift:
        """
        Capture the time punches entered from the command line
        Returns: empty list or a list of the punch dates and times in the WorkShift format 

        This also keeps track of the number of punches on the same day.
        """

        if not punchTimes: 
            # punch times from the command line 
            print(f"Warning: No punch times entered.")
            return None

        
        allTimePunches = set()
        try: 
            
            # convert the punch to a WorkShift object
            punchTimes = punchTimes.split('\n')
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











    def collect_shifts_from_dataframe(self, df: pd.DataFrame):

        df = self.clean_data(df)
        shifts = []

        print()
        print(f"Checking the validity of the rows: ")
        for _, row in df.iterrows():
            
            if not self.is_valid_shift_row(row, df.columns):
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








    def plot(self, shifts: list[WorkShift], currentYear='2025', minDate=date(2025, 2, 1), maxDate=date(9999, 1, 1)): 
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
                bottom=self.to_24hr_float(shift.clock_in),
                label='shift',
                width=0.93,
                color=color
            )


        # title 
        if currentYear == '2025':
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


        if currentYear == '2025':
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
















    def save_shifts_to_db(self, shifts: list[WorkShift], dbPath: Path=SCRIPTS_DIR / SHIFTS_SQL_DB_NAME):
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
            
            if cur.rowcount == 1:
                print(f"✔︎")
            else:
                print("✖︎ (likely duplicate).")


        conn.commit()
        conn.close()













    def pull_shifts_from_db(self, dbPath=SCRIPTS_DIR / SHIFTS_SQL_DB_NAME):
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













    def is_valid_shift_row(self, row, columns: list[str]) -> bool:
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





    def print_shifts(self, shifts: list[WorkShift]):
        print(f"\n\n======================================================")
        print(f"======================================================")
        print(f"\tTHE SHIFTS ARE:")

        for shift in shifts: 
            print()
            shift.view

        print(f"\n======================================================")
        print(f"======================================================")
















    def to_24hr_float(self, theTime: time | date | str ):
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









    def clean_data(self, df, winterBreak=False):
        """
        Cleaning a dataframe for proper use.

        Cleaning steps: 
        - clear NaN cols
        - convert to proper time objects 
        - convert to proper date objects 
        - remove skip lunch column
        """
        
        df = self.clean_empty_cols(df)

        ## Remove skip lunch column lol
        try: 
            df.drop('skip lunch', axis=1, inplace=True)
        except: 
            print(f"Column 'skip lunch' not found")

        return df








    def clean_empty_cols(self, df, threshold=0.30):     
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





        
        


