import sqlite3 as sql
import gspread
from oauth2client.service_account import ServiceAccountCredentials

global wsheet
global cnxn

################################################################################
# Define connection variables for accessing google sheets
################################################################################

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'Data/DB_Access.json', scope)  # Your json file here

gc = gspread.authorize(credentials)

# Connect to google sheets
wsheet = gc.open("DB_Project")

cnxn = sql.connect("Data/ProjectDB.db")
