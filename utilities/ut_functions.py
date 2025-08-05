import pandas as pd
from datetime import datetime, date, time
import numpy as np
import os
from pathlib import Path
import sqlite3

from classes.shiftClass import WorkShift
from utilities.necessary_data import NECESSARY_DATA
from utilities.workshift_data import *
from utilities.ut_functions import *

SCRIPTS_DIR = Path(__file__).parent.parent
SHIFTS_SQL_DB_NAME = 'database.db'





# =====================================================================
#            UTILITY FUNCTIONS
# =====================================================================



























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

    


















def printTypes(df):
    """
    Simply prints the datatypes of the most important columns. 
    DATE, IN, LUNCH IN, LUNCH OUT, time, hours, notes
    """

    print()
    print(f"==============================================================================")
    print(f"Testing the types: ")
    for col in df.columns:
        for cell in df[col]:
            if col not in GOOGLE_SHEET_COL_TYPES:
                continue
            print(f"Column {col}, \"{cell}\" cell is of type: {type(cell)}")
    print(f"==============================================================================")
    print()
    
    
    
    













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
