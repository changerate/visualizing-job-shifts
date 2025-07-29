from datetime import date, time, datetime
from classes.workShiftClass import WorkShift


GOOGLE_SHEET_COL_TYPES = {
    # your google sheet column name : the TYPE corresponding with the WorkShift obj
    # note that some do not actually have a representation in the the object. 
    # [change this side] : [do NOT change this side]
    "DATE": datetime.date,
    "IN": datetime.time,
    "OUT": datetime.time,
    "LUNCH IN": datetime.time,
    "LUNCH OUT": datetime.time,
    "bfr tax est total:": str, # this is a stupid name for the notes    
}


SHEET_TO_WORKSHIFT_COLS = {
    # your google sheet column name : the NAME corresponding with the WorkShift obj
    # [change this side] : [do NOT change this side]
    "DATE": 'date',
    "IN": 'clock_in',
    "OUT": 'clock_out',
    "LUNCH IN": 'lunch_in',
    "LUNCH OUT": 'lunch_out',
    "bfr tax est total:": 'notes',
}



# Invert it (value becomes key; key becomes value), skipping None values
WORKSHIFT_TO_SHEET_COLS = {
    v: k for k, v in SHEET_TO_WORKSHIFT_COLS.items() if v is not None
}
