# google sheet class
from typing import Dict
import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv


from pathlib import Path
from dotenv import load_dotenv
import os 
import pandas as pd
from datetime import datetime, date, time

# user modules
from utilities.workshift_data import *
from classes.shiftClass import WorkShift

SCRIPTS_DIR = Path(__file__).parent.parent






class GoogleSheetManager:
    def __init__(self, sheet_name: str):
        self._sheet_name = sheet_name
        self._sheet = self.__initialize()
        
        
    @property
    def sheet_name(self):
        return self._sheet_name

    @property
    def sheet(self):
        return self._sheet

        
        
        
        
        
    def __initialize(self):
        print(f"Initializing Google Sheet \'{self.sheet_name}\"")
        print(f"The home dir is {SCRIPTS_DIR}")
        print()

        try: 
            env_path = SCRIPTS_DIR / ".env"
            load_dotenv(dotenv_path=env_path)  # automatically looks for .env in the scripts directory

            creds_path = SCRIPTS_DIR / os.getenv("GOOGLE_SHEETS_CREDS_FILE")
            
            # Define the scopes
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Authorize
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            client = gspread.authorize(creds)

            # -----------------------------
            # Open sheet by name or URL
            sheet = client.open(self.sheet_name).sheet1

            print(f"Successfully connected to sheet \"{self.sheet_name}\".")
            print(f"Number of rows: {len(sheet.get_all_values())}")

            return sheet


        except Exception as e: 
            print(f"There was error setting up the sheet: {e}")
            return None





        

    def get_dataframe_of_sheet(self) -> pd.DataFrame:
        """
        Create DataFrame using first row as header
        This works with the 'cached' sheet, NOT the live sheet online.
        """
        
        if not self.sheet:
            print(f"The sheet was not loaded in\n")
            return None

        # turn in to a DataFrame
        data = self.sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df = self.__label_years(df=df)

        
        df['DATE'] = df['DATE'].apply(self.__parse_date_flexible)
        df['IN'] = df['IN'].apply(self.__parse_time_flexible)
        df['LUNCH IN'] = df['LUNCH IN'].apply(self.__parse_time_flexible)
        df['LUNCH OUT'] = df['LUNCH OUT'].apply(self.__parse_time_flexible)
        df['OUT'] = df['OUT'].apply(self.__parse_time_flexible)
        df['time'] = df['time'].apply(self.__parse_time_flexible)
        df['hours'] = df['hours'].apply(self.__parse_float_flexible)

        return df






    def __parse_float_flexible(self, x):
        """
        Turns a string float like 4.2 into a float value.
        """
        if pd.isna(x) or x == '':
            return pd.NA
        
        if isinstance(x, float):
            # print(f"x is already correct format")
            return x

        if isinstance(x, str):
            return float(x)
        
        return pd.NA


    def __parse_time_flexible(self, x):
        """
        Turns a string time like 4:30 PM into a datetime.time object of time(16, 30, 00)
        """
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


    def __parse_date_flexible(self, x):
        """
        Turns a string date like Sat Jul 26 into a datetime.date object of date(2025, 7, 26)
        """
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
    
    
    
    
    
    
    def __label_years(self, df: pd.DataFrame, currentYear: str='2025', yearDivider: str='YEAR SELECTOR') -> pd.DataFrame:

        ## Label 2023 and 2024 data
        lastRowOf2024 = len(df)
        firstRowOf2024 = len(df)
        
        
        if currentYear == '2024':
            # Find the last row of 2024
            for idx, cell in df[yearDivider].items():

                if cell == '2024  ⬆️':
                    lastRowOf2024 = idx


        elif currentYear == '2025':
            # Find the first row of 2024
            for idx, cell in df[yearDivider].items():

                if cell == '2024 ⬇️':
                    firstRowOf2024 = idx
            
            
        ## Convert to correct date format
        if currentYear == '2024':
            df['DATE'].iloc[0:lastRowOf2024] = pd.to_datetime(df['DATE'].iloc[0:lastRowOf2024] + ' ' + currentYear, errors='coerce').dt.date
            df['DATE'].iloc[lastRowOf2024:len(df)] = pd.to_datetime(df['DATE'].iloc[lastRowOf2024:len(df)] + ' 2023', errors='coerce').dt.date


        elif currentYear == '2025': 
            df.loc[0:firstRowOf2024-1, 'DATE'] = pd.to_datetime(
                df.loc[0:firstRowOf2024, 'DATE'].astype(str) + f' {currentYear}',
                format='%a %b %d %Y',
                errors='coerce'
            ).dt.date
            df.loc[firstRowOf2024:len(df), 'DATE'] = pd.to_datetime(
                df.loc[firstRowOf2024:len(df), 'DATE'].astype(str) + f' 2024',
                format='%a %b %d %Y', 
                errors='coerce'
                ).dt.date

        return df



    
    
    
    def __map_cols_of_google_sheet(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Find the positions of the important columns 
        """

        colMap = {}

        for idx, col in enumerate(df.columns):
            # print(f"The col \"{col}\" has the index: {idx}")

            if col in GOOGLE_SHEET_COL_TYPES:
                colMap.update({col : idx + 1})

        print(f"\nThe important columns are as follows:")
        print(colMap)
        print()
        return colMap






    def __find_next_empty_row(self, colMap: Dict[str, int], df: pd.DataFrame) -> int:
        """
        Find the next safe row in the google sheet to update
        """

        nextEmptyGoogleSheetRow = [] # this will always be saved as the row
                                    # indexing system used by Google Sheets:
                                    # So the range or rows is [2, len(sheet)]

        inColName = WORKSHIFT_TO_SHEET_COLS['clock_in']
        outColName = WORKSHIFT_TO_SHEET_COLS['clock_out']


        for col in [inColName, outColName]: 
            rowIndex = 0
            cell = df[col].iloc[rowIndex]

            while pd.isna(cell): 
                rowIndex += 1
                cell = df[col].iloc[rowIndex]
                if not pd.isna(cell): 
                    nextEmptyGoogleSheetRow.append(rowIndex + 2)

            

        # if the google sheet is not formatted right, pick the lowest row number --> this overwrites the out-of-place punch
        # else if the the sheet is ordered right pick the row before the first clock in clock out
        if len(set(nextEmptyGoogleSheetRow)) > 1:
            nextEmptyGoogleSheetRow = min(nextEmptyGoogleSheetRow)
        else: 
            nextEmptyGoogleSheetRow = min(nextEmptyGoogleSheetRow) - 1
                    
        print(f"So let's place a new row at row {nextEmptyGoogleSheetRow}.\n")
        return nextEmptyGoogleSheetRow






    def __format_shift_value(self, value: str | date | time) -> str:
        
        if isinstance(value, time):
            if value == time(1):
                return ""
            return value.strftime("%-I:%M %p")

        elif isinstance(value, date):
            return value.strftime("%a %b %d")

        return value






    def __update_sheet_cell(self, sheet, row, col_index, value, colMap, col):
        numberLetterMap = {
            # Not necessary, for display only.
            5: 'E',
            6: 'F',
            7: 'G',
            8: 'H',
            9: 'I',
            19: 'S',
        }

        col_letter = numberLetterMap[colMap[col]]
        print(f"Updating: \t{col_letter}{row}. \t{value}")
        return sheet.update_cell(row, col_index, value)






    def add_new_shift_to_sheet(self, newShift: WorkShift) -> None: 
        df = self.get_dataframe_of_sheet()
        
        # find the corresponding column numbers        
        colMap = self.__map_cols_of_google_sheet(df)
        nextEmptyGoogleSheetRow = self.__find_next_empty_row(colMap, df)
        
        # UPDATE THE GOOGLE SHEET
        feedback = []
        for col in colMap:
            # get the WorkShift class attribute corresponding with the Google Sheet col
            shiftAttribute = SHEET_TO_WORKSHIFT_COLS[col]
            if not shiftAttribute:
                continue  # skip if mapping is None

            shiftValue = getattr(newShift, shiftAttribute)
            formattedValue = self.__format_shift_value(shiftValue)

            feedback.append(
                self.__update_sheet_cell(
                    self.sheet, 
                    nextEmptyGoogleSheetRow, 
                    colMap[col],
                    formattedValue, 
                    colMap, 
                    col
                )
            )

        print(f"\nSuccessfully saved to sheet!\n")
        print(f"The reponses from Google Sheets:")
        for item in feedback: 
            print(f"{item}")
