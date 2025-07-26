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
from datetime import datetime

# user modules
from utilities.workshift_data import WORKSHIFT_NAMES, GOOGLE_SHEET_COL_NAMES
from classes.shiftClass import WorkShift

SCRIPTS_DIR = Path(__file__).parent.parent
print()
print(f"The home dir is {SCRIPTS_DIR}")
print()




class GoogleSheetManager:
    def __init__(self, sheet_name: str):
        self.sheet_name = sheet_name
        
        


    def DFFromGoogleSheet(self) -> pd.DataFrame: 
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
            data = sheet.get_all_values()

            print(f"Successfully connected to sheet \"{self.sheet_name}\".")
            print(f"Number of rows: {len(data)}")

            # Create DataFrame using first row as header
            df = pd.DataFrame(data[1:], columns=data[0])
            return (df, sheet)

        except Exception as e: 
            print(f"{e}")
            return (pd.DataFrame([]), None)
        
        


    def mapColsOfGoogleSheet(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Find the positions of the important columns 
        """

        colMap = {}

        for idx, col in enumerate(df.columns):
            # print(f"The col \"{col}\" has the index: {idx}")

            if col in GOOGLE_SHEET_COL_NAMES:
                colMap.update({col : idx + 1})

        print(f"\nThe important columns are as follows:")
        print(colMap)
        print()
        return colMap




    def findNextEmptyRow(self, colMap: Dict[str, int], df: pd.DataFrame) -> int:
        """
        Find the next safe row in the google sheet to update
        """

        # first find the next empty row 
        nextEmptyGoogleSheetRow = [] # this will always be saved as the row
                                    # indexing system used by Google Sheets
                                    # So --> [2, len(sheet)]

        for col in colMap: 
            rowIndex = 0
            cell = df[col].iloc[rowIndex]

            while not cell: 
                rowIndex += 1
                cell = df[col].iloc[rowIndex]
                if cell and (col =='IN' or col == 'OUT'): 
                    nextEmptyGoogleSheetRow.append(rowIndex + 2)
                    print(f"The first non-blank cell in {col} is: \t{cell}, \tat index \t{rowIndex+2}")


        # if the google sheet is not formatted right, pick the lowest row number --> this overwrites the out-of-place punch
        # else if the the sheet is ordered right pick the row before the first clock in clock out
        if len(set(nextEmptyGoogleSheetRow)) > 1:
            nextEmptyGoogleSheetRow = min(nextEmptyGoogleSheetRow)
        else: 
            nextEmptyGoogleSheetRow = min(nextEmptyGoogleSheetRow) - 1
                    
        print(f"So let's place a new row at row {nextEmptyGoogleSheetRow}.")
        return nextEmptyGoogleSheetRow




    def addNewShiftToSheet(self, newShift: WorkShift) -> None: 
        df, sheet = self.DFFromGoogleSheet()
        if not sheet:
            print(f"Something went wrong setting up the sheet\n")
            return None
        
        colMap = self.mapColsOfGoogleSheet(df)
        nextEmptyGoogleSheetRow = self.findNextEmptyRow(colMap, df)
        
        # -----------------------
        # update the google sheet
        numberLetterMap = {
            # Not necessary, for display only.
            5: 'E',
            6: 'F',
            7: 'G',
            8: 'H',
            9: 'I',
            19: 'S',
        }

        for col in colMap:
            print(f"The Google Sheet column, {col}, to update is: {numberLetterMap[colMap[col]]}")
        print()


        # Append a new row
        feedback = []
        
        for col in colMap: 
            if WORKSHIFT_NAMES[col] == 'date':
                print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t{newShift.clock_in.strftime("%a %b %d")}")
                feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], newShift.clock_in.strftime("%a %b %d")))

            elif WORKSHIFT_NAMES[col] == 'clock_in':
                print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t{newShift.clock_in.strftime("%-I:%M %p")}")
                feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], newShift.clock_in.strftime("%-I:%M %p")))

            elif WORKSHIFT_NAMES[col] == 'lunch_in':
                if newShift.lunch_in == datetime(1, 1, 1, 1):
                    print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t\"\"")
                    feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], ""))
                else:
                    print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t{newShift.lunch_in.strftime("%-I:%M %p")}")
                    feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], newShift.lunch_in.strftime("%-I:%M %p")))

            elif WORKSHIFT_NAMES[col] == 'lunch_out':
                if newShift.lunch_out == datetime(1, 1, 1, 1):
                    print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t\"\"")
                    feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], ""))
                else:
                    print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t{newShift.lunch_out.strftime("%-I:%M %p")}")
                    feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], newShift.lunch_out.strftime("%-I:%M %p")))

            elif WORKSHIFT_NAMES[col] == 'clock_out':
                print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t{newShift.clock_out.strftime("%-I:%M %p")}")
                feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], newShift.clock_out.strftime("%-I:%M %p")))

            elif WORKSHIFT_NAMES[col] == 'notes':
                print(f"Updating: \t{numberLetterMap[colMap[col]]}{nextEmptyGoogleSheetRow}. \t{newShift.notes}")
                feedback.append(sheet.update_cell(nextEmptyGoogleSheetRow, colMap[col], newShift.notes))

        print(f"\nSuccessfully saved to sheet!\n")
        print(f"The reponses from Google Sheets:")
        for item in feedback: 
            print(f"{item}")
