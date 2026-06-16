import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1CLcyXsU1elN7t08SaiDWgIkJxSA1YTxu")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "1nyNnj-JOi_17nPCs11Fodx82d07w6i0z6bFZ7iFJwE8")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")
RUN_INTERVAL_HOURS = int(os.getenv("RUN_INTERVAL_HOURS", "24"))

LINKEDIN_API_KEY = os.getenv('LINKEDIN_API_KEY', '')
LINKEDIN_SHEET_SOURCE = 'Profile'
LINKEDIN_SHEET_DEST = 'LinkedIn_Followers'
AUTOMATION_MODE = os.getenv('AUTOMATION_MODE', 'csv')
