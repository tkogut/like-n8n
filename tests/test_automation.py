import sys
from unittest.mock import MagicMock

# Mock out Google client library modules before importing the client
mock_oauth2 = MagicMock()
mock_service_account = MagicMock()
mock_oauth2.service_account = mock_service_account

mock_discovery = MagicMock()
mock_build = MagicMock()
mock_discovery.build = mock_build

mock_http = MagicMock()
mock_media = MagicMock()
mock_http.MediaIoBaseDownload = mock_media

sys.modules['google'] = MagicMock()
sys.modules['google.oauth2'] = mock_oauth2
sys.modules['google.oauth2.service_account'] = mock_service_account
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = mock_discovery
sys.modules['googleapiclient.http'] = mock_http

import unittest
from unittest.mock import patch
from src.parser import parse_csv
from src.google_client import GoogleClient

class TestCSVParser(unittest.TestCase):
    def test_empty_csv(self):
        content = ""
        results = parse_csv(content)
        self.assertEqual(results, [])

    def test_short_csv(self):
        content = "\n".join([f"line {i}" for i in range(20)])
        results = parse_csv(content)
        self.assertEqual(results, [])

    def test_correct_csv_parsing(self):
        lines = [f"Header {i}" for i in range(26)]
        lines.append("2026-06-15;Zakupy spożywcze;Faktura 123;Jedzenie;-150.50")
        lines.append("2026-06-16;Wynagrodzenie;Przelew;Praca;5000.00")
        lines.append("2026-06-17;Kino;Bilet;Rozrywka;-30.00;extra_column")
        lines.append("invalid_row_short;only_two_cols")

        csv_content = "\n".join(lines)
        results = parse_csv(csv_content)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["Data opercji"], "2026-06-15")
        self.assertEqual(results[0]["Opis"], "Zakupy spożywcze")
        self.assertEqual(results[0]["Kategoria"], "Jedzenie")
        self.assertEqual(results[0]["Kwota"], "-150.50")

        self.assertEqual(results[1]["Data opercji"], "2026-06-16")
        self.assertEqual(results[1]["Opis"], "Wynagrodzenie")
        self.assertEqual(results[1]["Kategoria"], "Praca")
        self.assertEqual(results[1]["Kwota"], "5000.00")

        self.assertEqual(results[2]["Data opercji"], "2026-06-17")
        self.assertEqual(results[2]["Opis"], "Kino")
        self.assertEqual(results[2]["Kategoria"], "Rozrywka")
        self.assertEqual(results[2]["Kwota"], "-30.00")


class TestGoogleClient(unittest.TestCase):
    def setUp(self):
        self.mock_drive = MagicMock()
        self.mock_sheets = MagicMock()
        
        # Patch build
        self.build_patcher = patch('src.google_client.build')
        self.mock_build = self.build_patcher.start()
        self.addCleanup(self.build_patcher.stop)
        
        # Patch _get_credentials
        self.creds_patcher = patch('src.google_client.GoogleClient._get_credentials')
        self.mock_get_creds = self.creds_patcher.start()
        self.addCleanup(self.creds_patcher.stop)
        
        # Configure side effect for build
        def build_side_effect(serviceName, version, **kwargs):
            if serviceName == 'drive':
                return self.mock_drive
            elif serviceName == 'sheets':
                return self.mock_sheets
            return MagicMock()
            
        self.mock_build.side_effect = build_side_effect
        self.mock_get_creds.return_value = MagicMock()

        self.client = GoogleClient(
            credentials_path="dummy_creds.json",
            folder_id="dummy_folder",
            spreadsheet_id="dummy_sheet"
        )

    def test_find_files_by_name(self):
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            "files": [{"id": "1", "name": "lista_test.csv"}]
        }
        self.mock_drive.files().list.return_value = mock_list

        files = self.client.find_files_by_name("lista")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["id"], "1")
        self.assertEqual(files[0]["name"], "lista_test.csv")

    @patch('src.google_client.MediaIoBaseDownload')
    def test_download_file(self, mock_downloader_cls):
        mock_downloader = MagicMock()
        mock_downloader.next_chunk.return_value = (None, True)
        
        def dummy_init(fd, request):
            fd.write(b"file content")
            return mock_downloader
        mock_downloader_cls.side_effect = dummy_init

        self.mock_drive.files().get_media.return_value = MagicMock()

        content = self.client.download_file("123")
        self.assertEqual(content, "file content")

    def test_append_or_update_rows_new_row(self):
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "values": [["Data opercji", "Opis", "Kategoria", "Kwota"]]
        }
        self.mock_sheets.spreadsheets().values().get.return_value = mock_get

        mock_append = MagicMock()
        mock_append.execute.return_value = {}
        self.mock_sheets.spreadsheets().values().append.return_value = mock_append

        records = [{
            "Data opercji": "2026-06-15",
            "Opis": "Zakupy",
            "Kategoria": "Jedzenie",
            "Kwota": "-10.00"
        }]

        self.client.append_or_update_rows("Pierwsza", records)

        self.mock_sheets.spreadsheets().values().append.assert_called_once()
        args, kwargs = self.mock_sheets.spreadsheets().values().append.call_args
        self.assertEqual(kwargs["range"], "'Pierwsza'!A:A")
        self.assertEqual(kwargs["body"]["values"][0], ["2026-06-15", "Zakupy", "Jedzenie", "-10.00"])

    def test_append_or_update_rows_existing_row(self):
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "values": [
                ["Data opercji", "Opis", "Kategoria", "Kwota"],
                ["2026-06-15", "Old Description", "Jedzenie", "-5.00"]
            ]
        }
        self.mock_sheets.spreadsheets().values().get.return_value = mock_get

        mock_update = MagicMock()
        mock_update.execute.return_value = {}
        self.mock_sheets.spreadsheets().values().update.return_value = mock_update

        records = [{
            "Data opercji": "2026-06-15",
            "Opis": "New Description",
            "Kategoria": "Jedzenie",
            "Kwota": "-10.00"
        }]

        self.client.append_or_update_rows("Pierwsza", records)

        self.mock_sheets.spreadsheets().values().update.assert_called_once()
        args, kwargs = self.mock_sheets.spreadsheets().values().update.call_args
        self.assertEqual(kwargs["range"], "'Pierwsza'!A2")
        self.assertEqual(kwargs["body"]["values"][0], ["2026-06-15", "New Description", "Jedzenie", "-10.00"])

if __name__ == '__main__':
    unittest.main()
