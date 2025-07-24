# necessary data
from datetime import date, time, datetime

"""
this data cannot be null
"""

NECESSARY_DATA = {
    "DATE": datetime.date,
    "IN": datetime.time,
    "LUNCH IN": datetime.time,
    "LUNCH OUT": datetime.time,
    "OUT": datetime.time,
    "time": datetime.time,
    "hours": float,
}