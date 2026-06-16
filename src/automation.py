import sys
import time
import logging
from datetime import datetime
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

def run_csv_automation(client):
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

def run_linkedin_automation(client):
    logger.info("Starting LinkedIn followers monitoring...")
    from src.linkedin_client import LinkedInClient
    
    if not config.LINKEDIN_API_KEY:
        logger.error("LINKEDIN_API_KEY is not set. Skipping LinkedIn automation.")
        return

    linkedin_client = LinkedInClient(api_key=config.LINKEDIN_API_KEY)
    
    logger.info(f"Fetching profiles from sheet '{config.LINKEDIN_SHEET_SOURCE}'...")
    profiles = client.get_linkedin_profiles(config.LINKEDIN_SHEET_SOURCE)
    logger.info(f"Found {len(profiles)} profile(s) to monitor.")
    
    if not profiles:
        logger.info("No profiles found to process.")
        return

    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    records_to_append = []
    for profile in profiles:
        name = profile.get("name")
        username = profile.get("username")
        if not username:
            logger.warning(f"Profile '{name}' has no LinkedIn Username, skipping.")
            continue
        
        logger.info(f"Fetching followers for '{name}' ({username})...")
        try:
            follower_count = linkedin_client.get_follower_count(username)
            logger.info(f"Profile '{name}' has {follower_count} followers.")
            records_to_append.append({
                "Data pomiaru": today_str,
                "Nazwa profilu": name,
                "Obserwujący": str(follower_count)
            })
        except Exception as e:
            logger.error(f"Failed to fetch followers for username '{username}': {e}")
            continue

    if records_to_append:
        logger.info(f"Appending {len(records_to_append)} measurement(s) to '{config.LINKEDIN_SHEET_DEST}'...")
        client.append_linkedin_followers(config.LINKEDIN_SHEET_DEST, records_to_append)
        logger.info("LinkedIn followers updated successfully.")
    else:
        logger.info("No new measurements to write.")

def run_once():
    logger.info("Starting automation cycle...")
    mode = config.AUTOMATION_MODE.lower()
    logger.info(f"Automation mode: {mode}")
    try:
        client = GoogleClient(
            credentials_path=config.CREDENTIALS_FILE,
            folder_id=config.GOOGLE_DRIVE_FOLDER_ID,
            spreadsheet_id=config.GOOGLE_SPREADSHEET_ID
        )

        if mode == 'csv':
            run_csv_automation(client)
        elif mode == 'linkedin':
            run_linkedin_automation(client)
        elif mode == 'both':
            run_csv_automation(client)
            run_linkedin_automation(client)
        else:
            logger.error(f"Unknown AUTOMATION_MODE: '{mode}'. Expected 'csv', 'linkedin', or 'both'.")
            
        logger.info("Automation cycle completed successfully.")
    except Exception as e:
        logger.error(f"Error during automation cycle: {e}", exc_info=True)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        run_once()
        return

    logger.info("Starting automation daemon (running every 24 hours)...")
    
    try:
        import schedule
        schedule.every(24).hours.do(run_once)
        run_once()
        while True:
            schedule.run_pending()
            time.sleep(1)
    except ImportError:
        logger.info("Library 'schedule' not found. Using standard time.sleep loop.")
        run_once()
        while True:
            time.sleep(config.RUN_INTERVAL_HOURS * 3600)
            run_once()

if __name__ == "__main__":
    main()
