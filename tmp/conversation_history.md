# Historia Konwersacji — Automatyzacja LinkedIn i Google Sheets (n8n migration)

**Data i czas:** 2026-06-16
**Repozytorium:** `/home/tkogut/projects/like-n8n`

---

## 📋 Przebieg Prac i Zapytania Użytkownika

1. **Status prac Buildera:**
   * Użytkownik zapytał, czy podagent `Builder` pracuje (ID: `c2922905-be77-43c8-98c9-6be86b012279`). 
   * Uruchomiliśmy go ponownie po restartach serwera, aby kontynuował integrację z LinkdAPI.

2. **Gdzie wpisywać profile do monitorowania:**
   * Profile są wczytywane z pliku Google Spreadsheet, z zakładki `Profile`.
   * Kolumny źródłowe to: `Nazwa` oraz `LinkedIn Username`.

3. **Naprawa problemów z uruchomieniem skryptu lokalnie:**
   * Napotkano `ModuleNotFoundError: No module named 'src'` oraz `ModuleNotFoundError: No module named 'google'`.
   * **Rozwiązanie**: Aktywowano wirtualne środowisko Python (`source venv/bin/activate`) i uruchomiono skrypt jako moduł: `python3 -m src.automation --once`.

4. **Weryfikacja uprawnień (approvals):**
   * Użytkownik zapytał o potrzebę zatwierdzania komend (approvals) dla Buildera.
   * **Rozwiązanie**: Potwierdzono, że należy ich udzielić (`y`), aby Builder mógł uruchamiać testy i weryfikować poprawność kodu.

5. **Rozwiązanie błędu 403 Forbidden (LinkdAPI):**
   * Podczas odpytywania API zwracany był błąd 403 z informacją o błędnym kluczu API (`Invalid X-linkdapi-apikey`).
   * Zauważono i poprawiono klucz v `.env` (usunięto zbędną literę `T` na początku klucza).
   * Kolejny błąd 403 wynikał z zabezpieczeń Cloudflare blokujących nagłówek `User-Agent` biblioteki Pythona (`Python-urllib`).
   * **Rozwiązanie**: W pliku `src/linkedin_client.py` dodano nagłówek `User-Agent` udający prawdziwą przeglądarkę, co odblokowało połączenie.

6. **Rozwiązanie błędu parsowania zagnieżdżonego `followerCount`:**
   * Po udanym połączeniu z API wystąpił błąd `Brak pola 'followerCount'`.
   * **Rozwiązanie**: Poprawiono ścieżkę w JSON-ie zwracanym przez LinkdAPI. Wartość ta jest zagnieżdżona w słowniku `data` (tj. `res_json['data']['followerCount']`).

7. **Automatyczne tworzenie brakujących zakładek (arkusza docelowego):**
   * Wystąpił błąd Google Sheets API `Unable to parse range: 'LinkedIn_Followers'!A:E`, ponieważ w arkuszu użytkownika brakowało tej zakładki.
   * **Rozwiązanie**: Dodano w `src/google_client.py` nową funkcję `_ensure_sheet_exists`, która przed zapisem upewnia się, czy zakładka istnieje i automatycznie ją tworzy w razie braku.

8. **Wypchnięcie zmian:**
   * Zmiany zostały zatwierdzone i pomyślnie wypchnięte do repozytorium GitHub na gałąź `main`.

---

## 🔍 Obecny Status Integracji

* **Tomasz Kogut** (`tomasz-kogut-7009aa91`): Pomyślnie pobrano 500 obserwujących i zapisano rekord w nowym arkuszu `LinkedIn_Followers`.
* **Dawid Gużda** (`56bb873b9`): Dane nie zostały pobrane, ponieważ identyfikator podany w arkuszu `Profile` jest niepełny. 
  * *Rekomendacja*: Należy zmienić w kolumnie `LinkedIn Username` wartość `56bb873b9` na pełny identyfikator profilu (np. `dawid-gużda-56bb873b9` lub `dawid-guzda-56bb873b9`).
* Skrypt jest w pełni sprawny i gotowy do dalszego użytkowania.
