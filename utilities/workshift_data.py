from datetime import date, time, datetime


GOOGLE_SHEET_COL_NAMES = {
    "DATE": datetime.date,
    "IN": datetime.time,
    "LUNCH IN": datetime.time,
    "LUNCH OUT": datetime.time,
    "OUT": datetime.time,
    "bfr tax est total:": str, # this is a stupid name for the NOTES
}


WORKSHIFT_NAMES = {
    "DATE": 'date',
    "IN": 'clock_in',
    "LUNCH IN": 'lunch_in',
    "LUNCH OUT": 'lunch_out',
    "OUT": 'clock_out',
    "bfr tax est total:": 'notes',
}


# REVERSE_WORKSHIFT_NAMES = {
#     ''
#     'clock_in': "IN",
#     'lunch_in': "LUNCH IN",
#     'lunch_out': "LUNCH OUT",  # Note: both "OUT" and "LUNCH OUT" originally mapped to 'lunch_out'
#     'notes': "bfr tax est total:",
#     None: "DATE"  # Only if you're intentionally keeping this
# }

