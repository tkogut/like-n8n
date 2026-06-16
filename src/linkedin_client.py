import urllib.request
import urllib.error
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

class LinkedInClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://linkdapi.com/api/v1/profile/full'

    def get_follower_count(self, username: str) -> int:
        """
        Pobiera liczbę obserwujących dla podanego profilu z LinkdAPI.
        """
        if not self.api_key:
            raise ValueError("Brak klucza API dla LinkedIn (LINKEDIN_API_KEY).")
        
        if not username:
            raise ValueError("Nazwa użytkownika LinkedIn nie może być pusta.")

        url = f"{self.base_url}?username={urllib.parse.quote(username)}"
        req = urllib.request.Request(url)
        req.add_header("X-linkdapi-apikey", self.api_key)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.getcode()
                if status == 200:
                    res_json = json.loads(response.read().decode("utf-8"))
                    profile_data = res_json.get("data")
                    if not profile_data or not isinstance(profile_data, dict):
                        raise ValueError(f"Brak sekcji 'data' w odpowiedzi dla profilu {username}.")
                    follower_count = profile_data.get("followerCount")
                    if follower_count is None:
                        raise ValueError(f"Brak pola 'followerCount' w sekcji 'data' dla profilu {username}.")
                    return int(follower_count)
                else:
                    raise Exception(f"Nieoczekiwany status HTTP: {status}")
        except urllib.error.HTTPError as e:
            logger.error(f"Błąd HTTP podczas pobierania profilu {username}: {e.code} - {e.reason}")
            raise e
        except urllib.error.URLError as e:
            logger.error(f"Błąd sieci podczas pobierania profilu {username}: {e.reason}")
            raise e
        except Exception as e:
            logger.error(f"Błąd podczas pobierania profilu {username}: {str(e)}")
            raise e
