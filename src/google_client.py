import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

class GoogleClient:
    def __init__(self, credentials_path: str, folder_id: str, spreadsheet_id: str):
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.spreadsheet_id = spreadsheet_id
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self._drive_service = None
        self._sheets_service = None

    def _get_credentials(self):
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}")
        return service_account.Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes
        )

    @property
    def drive_service(self):
        if not self._drive_service:
            creds = self._get_credentials()
            self._drive_service = build('drive', 'v3', credentials=creds)
        return self._drive_service

    @property
    def sheets_service(self):
        if not self._sheets_service:
            creds = self._get_credentials()
            self._sheets_service = build('sheets', 'v4', credentials=creds)
        return self._sheets_service

    def find_files_by_name(self, name_contains: str) -> list:
        """
        Finds files in the configured folder whose name contains the specified string.
        """
        query = f"'{self.folder_id}' in parents and name contains '{name_contains}' and trashed = false"
        results = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id: str) -> str:
        """
        Downloads file content by file_id and returns it as a string.
        """
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue().decode('utf-8', errors='ignore')

    def append_or_update_rows(self, sheet_name: str, records: list):
        """
        Appends or updates rows in Google Sheet based on 'Data opercji' column.
        """
        if not records:
            return

        # Fetch current sheets structure
        sheet_range = f"'{sheet_name}'!A:E"
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range
            ).execute()
        except Exception as e:
            # If sheet get fails, re-raise
            raise e

        rows = result.get('values', [])
        headers = ["Data opercji", "Opis", "Kategoria", "Kwota"]

        if not rows:
            # Sheet is empty, write headers first
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:D1",
                valueInputOption="USER_ENTERED",
                body={"values": [headers]}
            ).execute()
            rows = [headers]

        header_row = rows[0]
        col_indices = {}
        header_updated = False
        
        for h in headers:
            if h in header_row:
                col_indices[h] = header_row.index(h)
            else:
                col_indices[h] = len(header_row)
                header_row.append(h)
                header_updated = True

        if header_updated:
            # Update header row in sheet
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:{chr(65 + len(header_row) - 1)}1",
                valueInputOption="USER_ENTERED",
                body={"values": [header_row]}
            ).execute()

        data_operacji_idx = col_indices["Data opercji"]
        opis_idx = col_indices["Opis"]
        kategoria_idx = col_indices["Kategoria"]
        kwota_idx = col_indices["Kwota"]

        # Map existing Data opercji to row number (1-based index)
        data_map = {}
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) > data_operacji_idx:
                key = row[data_operacji_idx].strip()
                if key:
                    data_map[key] = idx

        for record in records:
            key = record["Data opercji"]
            row_data = ["" for _ in range(max(col_indices.values()) + 1)]
            row_data[data_operacji_idx] = record["Data opercji"]
            row_data[opis_idx] = record["Opis"]
            row_data[kategoria_idx] = record["Kategoria"]
            row_data[kwota_idx] = record["Kwota"]

            if key in data_map:
                # Update existing row
                row_num = data_map[key]
                update_range = f"'{sheet_name}'!A{row_num}"
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=update_range,
                    valueInputOption="USER_ENTERED",
                    body={"values": [row_data]}
                ).execute()
            else:
                # Append new row
                append_range = f"'{sheet_name}'!A:A"
                self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=append_range,
                    valueInputOption="USER_ENTERED",
                    body={"values": [row_data]}
                ).execute()
                # To prevent duplicate appends in the same run, update map
                new_idx = len(rows) + 1
                data_map[key] = new_idx
                rows.append(row_data)

    def _ensure_sheet_exists(self, sheet_name: str):
        """
        Sprawdza czy zakładka o podanej nazwie istnieje w arkuszu.
        Jeśli nie, tworzy ją.
        """
        spreadsheet = self.sheets_service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_titles = [s.get('properties', {}).get('title') for s in sheets]
        
        if sheet_name not in sheet_titles:
            body = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }
                ]
            }
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()

    def get_linkedin_profiles(self, sheet_name: str) -> list:
        """
        Wczytuje profile z zakładki 'Profile' (kolumny 'Nazwa' i 'LinkedIn Username').
        Zwraca listę słowników: [{"name": nazwa, "username": username}, ...]
        """
        sheet_range = f"'{sheet_name}'!A:E"
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range
            ).execute()
        except Exception as e:
            raise e

        rows = result.get('values', [])
        if not rows:
            return []

        headers = [h.strip() for h in rows[0]]
        
        try:
            nazwa_idx = headers.index('Nazwa')
        except ValueError:
            nazwa_idx = 0
        
        try:
            username_idx = headers.index('LinkedIn Username')
        except ValueError:
            username_idx = 1

        profiles = []
        for row in rows[1:]:
            name = row[nazwa_idx].strip() if len(row) > nazwa_idx else ""
            username = row[username_idx].strip() if len(row) > username_idx else ""
            if name or username:
                profiles.append({
                    "name": name,
                    "username": username
                })
        return profiles

    def append_linkedin_followers(self, sheet_name: str, records: list):
        """
        Zapisuje pomiary do zakładki 'LinkedIn_Followers' (kolumny 'Data pomiaru', 'Nazwa profilu', 'Obserwujący').
        """
        if not records:
            return

        self._ensure_sheet_exists(sheet_name)

        sheet_range = f"'{sheet_name}'!A:E"
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=sheet_range
            ).execute()
        except Exception as e:
            raise e

        rows = result.get('values', [])
        headers = ["Data pomiaru", "Nazwa profilu", "Obserwujący"]

        if not rows:
            # Sheet is empty, write headers first
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:C1",
                valueInputOption="USER_ENTERED",
                body={"values": [headers]}
            ).execute()
            rows = [headers]

        header_row = rows[0]
        col_indices = {}
        header_updated = False
        
        for h in headers:
            if h in header_row:
                col_indices[h] = header_row.index(h)
            else:
                col_indices[h] = len(header_row)
                header_row.append(h)
                header_updated = True

        if header_updated:
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:{chr(65 + len(header_row) - 1)}1",
                valueInputOption="USER_ENTERED",
                body={"values": [header_row]}
            ).execute()

        data_idx = col_indices["Data pomiaru"]
        nazwa_idx = col_indices["Nazwa profilu"]
        obserwujacy_idx = col_indices["Obserwujący"]

        values_to_append = []
        for record in records:
            row_data = ["" for _ in range(max(col_indices.values()) + 1)]
            row_data[data_idx] = record["Data pomiaru"]
            row_data[nazwa_idx] = record["Nazwa profilu"]
            row_data[obserwujacy_idx] = record["Obserwujący"]
            values_to_append.append(row_data)

        if values_to_append:
            append_range = f"'{sheet_name}'!A:A"
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=append_range,
                valueInputOption="USER_ENTERED",
                body={"values": values_to_append}
            ).execute()
