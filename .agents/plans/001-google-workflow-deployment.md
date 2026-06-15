# [SEQ-PRO] Plan 001: Wdrożenie Automatyzacji Google Workflow z n8n jako usługa Docker na VPS

## 📋 1. Analiza Wejściowa (Google Workflow.json)
Oryginalna automatyzacja n8n wykonuje następujące zadania:
1. **Schedule Trigger**: Wyzwolenie codziennie o godzinie 09:00.
2. **Switch**: Rozgałęzienie na dwie ścieżki (warunek pusty, więc obie ścieżki są uruchamiane równolegle).
3. **Ścieżka A (Search files and folders1)**:
   - Wyszukuje pliki zawierające frazę `'lista'` w katalogu Google Drive o ID `1CLcyXsU1elN7t08SaiDWgIkJxSA1YTxu`.
   - Pobiera znaleziony plik (**Download file**).
   - Wyodrębnia dane z pliku (**Extract from File**) jako CSV: średnik `;` jako separator, pominięcie pierwszych 26 linii (start od linii 27).
4. **Ścieżka B (Search files and folders)**:
   - Wyszukuje pliki zawierające frazę `'Testowy'` w katalogu Google Drive o ID `1CLcyXsU1elN7t08SaiDWgIkJxSA1YTxu`.
5. **Merge**: Łączy wyniki obu ścieżek (obie ścieżki muszą się zakończyć powodzeniem).
6. **Append or update row in sheet**:
   - Dodaje lub aktualizuje wiersze w arkuszu `Pierwsza` w Google Spreadsheet o ID `1nyNnj-JOi_17nPCs11Fodx82d07w6i0z6bFZ7iFJwE8`.
   - Mapowanie kolumn:
     - `Data opercji` (klucz dopasowania/matching): `row['0']` (kolumna A z CSV)
     - `Opis`: `row['1']` (kolumna B z CSV)
     - `Kategoria`: `row['3']` (kolumna D z CSV)
     - `Kwota`: `row['4']` (kolumna E z CSV)

---

## 🛠️ 2. Fazy Implementacji i Wdrożenia

### 1. Faza: Przygotowanie Środowiska i Poświadczeń (Local Setup)
- Utworzenie projektu w Google Cloud Console.
- Włączenie interfejsów API: **Google Drive API** oraz **Google Sheets API**.
- Utworzenie konta usługowego (Service Account) i pobranie pliku klucza JSON (`credentials.json`).
- Udostępnienie folderu Google Drive (`1CLcyXsU1elN7t08SaiDWgIkJxSA1YTxu`) oraz arkusza kalkulacyjnego (`1nyNnj-JOi_17nPCs11Fodx82d07w6i0z6bFZ7iFJwE8`) na adres email konta usługowego (dostęp odpowiednio: odczyt dla Drive, edycja dla Sheets).

### 2. Faza: Tworzenie Kodu Źródłowego (Builder Task)
- Technologia: **Python 3.11** z użyciem oficjalnych bibliotek `google-api-python-client` oraz `google-auth`.
- Struktura katalogów w `/src`:
  - `src/automation.py` - główny skrypt uruchamiający pobieranie, przetwarzanie CSV oraz zapis do Sheets.
  - `src/config.py` - konfiguracja i wczytywanie zmiennych środowiskowych z `.env`.
  - `src/google_client.py` - obsługa połączenia z API Google Drive i Google Sheets.
  - `src/parser.py` - logika przetwarzania pliku CSV (pomijanie 26 linii, separator `;`, walidacja danych).
- Harmonogram (Cron):
  - Wersja kontenerowa będzie uruchamiana cyklicznie przez systemowy `cron` wewnątrz kontenera lub za pomocą biblioteki `schedule` w nieskończonej pętli Pythona (zalecane rozwiązanie: pętla z biblioteką `schedule` w celu łatwego logowania i monitorowania).

### 3. Faza: Testowanie Lokalne (Kluczowa Faza Przed Wdrożeniem)
Przed wdrożeniem produkcyjnym na VPS należy wykonać pełne testy lokalne:
- **Testy jednostkowe (`tests/`)**:
  - Przetwarzanie przykładowych plików CSV (w tym obsługa błędów, pustych wierszy, niepoprawnych formatów).
  - Testowanie mechanizmu mapowania kolumn.
- **Mockowanie API**:
  - Testowanie kodu przy użyciu `unittest.mock` dla zapytań sieciowych Google Drive i Sheets API, aby upewnić się, że program reaguje poprawnie na błędy API (brak połączenia, limit zapytań).
- **Testy integracyjne (Piaskownica)**:
  - Konfiguracja testowego arkusza Google i testowego folderu na Drive.
  - Uruchomienie skryptu lokalnie z poświadczeniami deweloperskimi i weryfikacja czy wiersze są poprawnie dodawane/aktualizowane.

### 4. Faza: Konteneryzacja (Docker)
- Przygotowanie pliku `Dockerfile`:
  - Bazowanie na bezpiecznym obrazie `python:3.11-slim`.
  - Uruchomienie procesu jako użytkownik bez uprawnień roota (`appuser`).
  - Ustawienie zmiennej środowiskowej `PYTHONUNBUFFERED=1` dla natychmiastowego logowania w Dockerze.
- Przygotowanie pliku `docker-compose.yml`:
  - Zdefiniowanie serwisu `google-workflow-automation`.
  - Przekazanie poświadczeń przez wolumeny (`credentials.json` jako plik tylko do odczytu) lub zmienną środowiskową.
  - Zabezpieczenie kontenera (brak uprawnień roota, limit pamięci, automatyczny restart w przypadku błędu `restart: unless-stopped`).

### 5. Faza: Wdrożenie na VPS Hostinger (Ostatni Krok)
- Po przejściu wszystkich testów i weryfikacji przez Audytora:
  - Nawiązanie połączenia SSH z VPS Hostinger.
  - Instalacja/weryfikacja środowiska Docker i Docker Compose na serwerze.
  - Sklonowanie kodu projektu (lub bezpieczny transfer przez SCP).
  - Skonfigurowanie pliku produkcyjnego `.env` oraz wgranie produkcyjnego `credentials.json`.
  - Uruchomienie usługi: `docker compose up -d --build`.
  - Weryfikacja działania za pomocą logów: `docker compose logs -f`.

---

## 🔒 3. Bezpieczeństwo i Walidacja (Verification Plan)
Zgodnie z wymaganiami bezpieczeństwa `mandatory-secure-web-skills`:
- **Brak zahardkodowanych sekretów**: Plik poświadczeń konta usługowego `credentials.json` oraz klucze nie mogą znajdować się w kodzie źródłowym i są ignorowane w `.gitignore`.
- **Walidacja ścieżek i danych wejściowych**:
  - Nazwy pobieranych plików z Google Drive są ściśle walidowane przed zapisem na dysk lokalny kontenera (brak podatności Path Traversal).
  - Zawartość pliku CSV jest filtrowana i sanitowana przed wysłaniem do Google Sheets API.
- **Zasada minimalnych uprawnień**: Konto usługowe Google posiada wyłącznie uprawnienia do odczytu konkretnego folderu Drive i zapisu do wyznaczonego arkusza (brak globalnych uprawnień administratora Google Workspace).

---

## 🤝 4. Warunek Handshake (Ukończenie Planu)
Zadanie zostanie uznane za kompletne po:
1. Pomyślnym zaliczeniu testów jednostkowych i integracyjnych w środowisku lokalnym.
2. Zbudowaniu i przetestowaniu obrazu Docker na maszynie testowej.
3. Przedstawieniu logów z pierwszego poprawnego uruchomienia testowego.
4. "Handshake Verified: Plan-Alignment and Math-Consistency checked. Ready for Coordinator Push."
