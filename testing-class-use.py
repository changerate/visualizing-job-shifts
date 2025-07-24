# testing class use
from classes.shiftClass import WorkShift 
from rates import PAY_RATE_TABLE
from datetime import date, time, datetime

shift = WorkShift(
    clock_in=datetime(2025, 7, 23, 8), 
    clock_out=datetime(2025, 7, 23, 16), 
    rate_type='copy center',
    notes='This is a shift!!')

shift.view