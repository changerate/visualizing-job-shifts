import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import pandas as pd


load_dotenv()  # automatically looks for .env in the current directory

creds_path = os.getenv("GOOGLE_SHEETS_CREDS_FILE")


# Define the scopes
# scopes = ["https://www.googleapis.com/auth/spreadsheets"]
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
client = gspread.authorize(creds)

# Authorize
creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
client = gspread.authorize(creds)

# Open sheet by name or URL
sheet = client.open("Staples Finances 2025").sheet1  # or .worksheet("Sheet2")

# Example: Read all data
data = sheet.get_all_values()
print(pd.DataFrame(data))