import sys
import os

# Ensure the root directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src import config
from src.google_client import GoogleClient

def run_diagnostics():
    print("=== DIAGNOSTYKA POŁĄCZENIA GOOGLE API ===")
    
    # 1. Sprawdzenie pliku poświadczeń
    creds_path = config.CREDENTIALS_FILE
    print(f"1. Sprawdzanie pliku poświadczeń: '{creds_path}'...")
    if not os.path.exists(creds_path):
        print(f"❌ BŁĄD: Plik poświadczeń '{creds_path}' nie istnieje w katalogu głównym!")
        print("   👉 Pobierz plik JSON klucza Service Account z Google Cloud Console i zapisz go jako 'credentials.json'.")
        sys.exit(1)
    print("   ✅ Plik poświadczeń odnaleziony.")

    # 2. Sprawdzenie zmiennych środowiskowych
    print(f"2. Weryfikacja parametrów konfiguracyjnych:")
    print(f"   - Folder ID: {config.GOOGLE_DRIVE_FOLDER_ID}")
    print(f"   - Spreadsheet ID: {config.GOOGLE_SPREADSHEET_ID}")
    
    try:
        client = GoogleClient(
            credentials_path=creds_path,
            folder_id=config.GOOGLE_DRIVE_FOLDER_ID,
            spreadsheet_id=config.GOOGLE_SPREADSHEET_ID
        )
    except Exception as e:
        print(f"❌ BŁĄD: Nie można zainicjalizować GoogleClient: {e}")
        sys.exit(1)

    # 3. Test połączenia z Google Drive API
    print("3. Testowanie Google Drive API (odczyt folderu)...")
    try:
        # Próba pobrania listy plików w folderze (nazwa zawiera cokolwiek)
        files = client.find_files_by_name("")
        print(f"   ✅ Sukces: Połączono z Google Drive API. Znaleziono {len(files)} plików w folderze.")
        for f in files[:3]:
            print(f"      - {f['name']} (ID: {f['id']})")
        if len(files) > 3:
            print("      - ...")
    except Exception as e:
        print(f"❌ BŁĄD: Połączenie z Google Drive API nie powiodło się!")
        print(f"   Szczegóły błędu: {e}")
        print("   👉 Upewnij się, że:")
        print("      - Włączyłeś 'Google Drive API' w Google Cloud Console dla swojego projektu.")
        print("      - Udostępniłeś folder w Google Drive dla adresu e-mail konta usługowego (Service Account) z prawem do odczytu.")
        sys.exit(1)

    # 4. Test połączenia z Google Sheets API
    print("4. Testowanie Google Sheets API (odczyt arkusza)...")
    try:
        # Próba odczytu arkusza
        sheet_metadata = client.sheets_service.spreadsheets().get(
            spreadsheetId=client.spreadsheet_id
        ).execute()
        sheets = [s['properties']['title'] for s in sheet_metadata.get('sheets', [])]
        print(f"   ✅ Sukces: Połączono z Google Sheets API. Nazwa arkusza: '{sheet_metadata['properties']['title']}'")
        print(f"      Dostępne zakładki: {sheets}")
        
        if "Pierwsza" not in sheets:
            print("   ⚠️ OSTRZEŻENIE: Brak zakładki o nazwie 'Pierwsza' w spreadsheet!")
            print("      👉 Utwórz zakładkę 'Pierwsza' w pliku Google Sheets lub zmień konfigurację.")
    except Exception as e:
        print(f"❌ BŁĄD: Połączenie z Google Sheets API nie powiodło się!")
        print(f"   Szczegóły błędu: {e}")
        print("   👉 Upewnij się, że:")
        print("      - Włączyłeś 'Google Sheets API' w Google Cloud Console dla swojego projektu.")
        print("      - Udostępniłeś plik Google Spreadsheet dla adresu e-mail konta usługowego z prawem do edycji.")
        sys.exit(1)

    print("\n🎉 Sukces! Połączenie z Google API jest w pełni autoryzowane i skonfigurowane poprawnie.")

if __name__ == "__main__":
    run_diagnostics()
