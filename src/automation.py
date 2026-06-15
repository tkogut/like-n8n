import sys
import time
import logging
from src import config
from src.parser import parse_csv
from src.google_client import GoogleClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_once():
    logger.info("Starting automation cycle...")
    try:
        client = GoogleClient(
            credentials_path=config.CREDENTIALS_FILE,
            folder_id=config.GOOGLE_DRIVE_FOLDER_ID,
            spreadsheet_id=config.GOOGLE_SPREADSHEET_ID
        )

        logger.info("Searching for 'lista' files...")
        lista_files = client.find_files_by_name("lista")
        logger.info(f"Found {len(lista_files)} file(s) matching 'lista'")

        logger.info("Searching for 'Testowy' files...")
        testowy_files = client.find_files_by_name("Testowy")
        logger.info(f"Found {len(testowy_files)} file(s) matching 'Testowy'")

        if not lista_files:
            logger.info("No 'lista' files found to process.")
            return

        for f in lista_files:
            file_id = f['id']
            file_name = f['name']
            logger.info(f"Processing file: {file_name} (ID: {file_id})")
            
            # Download file content
            csv_content = client.download_file(file_id)
            
            # Parse CSV
            records = parse_csv(csv_content)
            logger.info(f"Parsed {len(records)} records from CSV.")
            
            if records:
                # Update/Append sheet rows
                logger.info("Updating spreadsheet 'Pierwsza'...")
                client.append_or_update_rows("Pierwsza", records)
                logger.info("Spreadsheet updated successfully.")
            else:
                logger.warning("No valid records found in CSV.")
                
        logger.info("Automation cycle completed successfully.")
    except Exception as e:
        logger.error(f"Error during automation cycle: {e}", exc_info=True)

def main():
    # If run with '--once', execute once and exit
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        run_once()
        return

    logger.info("Starting automation daemon (running every 24 hours)...")
    
    # Try using schedule library
    try:
        import schedule
        schedule.every(24).hours.do(run_once)
        
        # Run immediately on start
        run_once()
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    except ImportError:
        logger.info("Library 'schedule' not found. Using standard time.sleep loop.")
        # Run immediately on start
        run_once()
        while True:
            time.sleep(config.RUN_INTERVAL_HOURS * 3600)
            run_once()

if __name__ == "__main__":
    main()
