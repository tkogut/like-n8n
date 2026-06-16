import sys
from unittest.mock import MagicMock, patch

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
import urllib.error
from src.linkedin_client import LinkedInClient
from src.google_client import GoogleClient
from src.automation import run_linkedin_automation
from src import config

class TestLinkedInClient(unittest.TestCase):
    @patch('urllib.request.urlopen')
    def test_get_follower_count_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'{"data": {"followerCount": 1234}}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = LinkedInClient(api_key="test_key")
        followers = client.get_follower_count("test_user")
        self.assertEqual(followers, 1234)

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        # urllib.request.Request headers are capitalized, so "X-linkdapi-apikey" will be returned
        self.assertEqual(req.get_header("X-linkdapi-apikey"), "test_key")
        self.assertEqual(req.get_full_url(), "https://linkdapi.com/api/v1/profile/full?username=test_user")

    @patch('urllib.request.urlopen')
    def test_get_follower_count_missing_field(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'{"data": {"invalid": "data"}}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        client = LinkedInClient(api_key="test_key")
        with self.assertRaises(ValueError):
            client.get_follower_count("test_user")

    @patch('urllib.request.urlopen')
    def test_get_follower_count_http_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://linkdapi.com/api/v1/profile/full?username=test_user",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None
        )

        client = LinkedInClient(api_key="test_key")
        with self.assertRaises(urllib.error.HTTPError):
            client.get_follower_count("test_user")

    @patch('urllib.request.urlopen')
    def test_get_follower_count_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

        client = LinkedInClient(api_key="test_key")
        with self.assertRaises(urllib.error.URLError):
            client.get_follower_count("test_user")


class TestGoogleClientLinkedIn(unittest.TestCase):
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

    def test_get_linkedin_profiles(self):
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            "values": [
                ["Nazwa", "LinkedIn Username", "Other Column"],
                ["Profile 1", "user1", "x"],
                ["Profile 2", "user2", "y"]
            ]
        }
        self.mock_sheets.spreadsheets().values().get.return_value = mock_get

        profiles = self.client.get_linkedin_profiles("Profile")
        self.assertEqual(len(profiles), 2)
        self.assertEqual(profiles[0]["name"], "Profile 1")
        self.assertEqual(profiles[0]["username"], "user1")
        self.assertEqual(profiles[1]["name"], "Profile 2")
        self.assertEqual(profiles[1]["username"], "user2")

    def test_get_linkedin_profiles_empty(self):
        mock_get = MagicMock()
        mock_get.execute.return_value = {}
        self.mock_sheets.spreadsheets().values().get.return_value = mock_get

        profiles = self.client.get_linkedin_profiles("Profile")
        self.assertEqual(profiles, [])

    def test_append_linkedin_followers_empty_sheet(self):
        mock_get = MagicMock()
        mock_get.execute.return_value = {}  # Empty sheet
        self.mock_sheets.spreadsheets().values().get.return_value = mock_get

        mock_update = MagicMock()
        mock_update.execute.return_value = {}
        self.mock_sheets.spreadsheets().values().update.return_value = mock_update

        mock_append = MagicMock()
        mock_append.execute.return_value = {}
        self.mock_sheets.spreadsheets().values().append.return_value = mock_append

        records = [
            {"Data pomiaru": "2026-06-16", "Nazwa profilu": "Profile 1", "Obserwujący": "100"}
        ]
        self.client.append_linkedin_followers("LinkedIn_Followers", records)

        # Should write headers first
        self.mock_sheets.spreadsheets().values().update.assert_called_once()
        update_args, update_kwargs = self.mock_sheets.spreadsheets().values().update.call_args
        self.assertEqual(update_kwargs["range"], "'LinkedIn_Followers'!A1:C1")
        self.assertEqual(update_kwargs["body"]["values"][0], ["Data pomiaru", "Nazwa profilu", "Obserwujący"])

        # Then append records
        self.mock_sheets.spreadsheets().values().append.assert_called_once()
        append_args, append_kwargs = self.mock_sheets.spreadsheets().values().append.call_args
        self.assertEqual(append_kwargs["range"], "'LinkedIn_Followers'!A:A")
        self.assertEqual(append_kwargs["body"]["values"][0], ["2026-06-16", "Profile 1", "100"])


class TestLinkedInAutomation(unittest.TestCase):
    @patch('src.automation.GoogleClient')
    @patch('src.linkedin_client.LinkedInClient.get_follower_count')
    def test_run_linkedin_automation(self, mock_get_follower, mock_google_client_cls):
        mock_client = MagicMock()
        mock_client.get_linkedin_profiles.return_value = [
            {"name": "Profile 1", "username": "user1"},
            {"name": "Profile 2", "username": "user2"}
        ]
        mock_google_client_cls.return_value = mock_client

        # Mock follower count
        mock_get_follower.side_effect = [500, 1000]

        # Temporarily set API key
        old_key = config.LINKEDIN_API_KEY
        config.LINKEDIN_API_KEY = "dummy_key"

        try:
            run_linkedin_automation(mock_client)
        finally:
            config.LINKEDIN_API_KEY = old_key

        # Verify Google Client functions called
        mock_client.get_linkedin_profiles.assert_called_once_with("Profile")
        mock_client.append_linkedin_followers.assert_called_once()
        args, kwargs = mock_client.append_linkedin_followers.call_args
        self.assertEqual(args[0], "LinkedIn_Followers")
        records = args[1]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["Nazwa profilu"], "Profile 1")
        self.assertEqual(records[0]["Obserwujący"], "500")
        self.assertEqual(records[1]["Nazwa profilu"], "Profile 2")
        self.assertEqual(records[1]["Obserwujący"], "1000")


if __name__ == '__main__':
    unittest.main()
