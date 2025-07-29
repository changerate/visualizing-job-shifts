# shift manager class 
from utilities.rates import PAY_RATE_TABLE
from datetime import datetime, time, date
from classes import WorkShift
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch





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











def collect_shifts_from_dataframe(df):

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












