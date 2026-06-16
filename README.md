# 🤖 Google Workflow Automation (like-n8n)

Projekt stanowi migrację i automatyzację przepływu pracy z n8n (`raw_notes/Google Workflow.json`) do niezależnej usługi napisanej w języku Python 3.11, uruchamianej w kontenerze Docker na VPS (Hostinger) lub jako lokalny demon.

Aplikacja cyklicznie pobiera pliki CSV z Google Drive, parsuje ich zawartość i synchronizuje wiersze (wstawia lub aktualizuje) z Google Sheets na podstawie kolumny klucza `Data opercji`, a także opcjonalnie monitoruje liczbę obserwujących (followers) profili LinkedIn przy użyciu LinkdAPI.

---

## 🚀 Szybki Start (Local Setup)

Aby uruchomić i skonfigurować projekt lokalnie na nowym komputerze, wykonaj następujące kroki:

### 1. Pobranie i instalacja środowiska
Uruchom skrypt instalacyjny, który automatycznie utworzy wirtualne środowisko `venv` i pobierze zależności:
```bash
./setup.sh
```
*Uwaga: W przypadku braku pakietu `python3-venv` zainstaluj go wcześniej komendą `sudo apt update && sudo apt install -y python3-venv`.*

### 2. Konfiguracja poświadczeń i zmiennych
1. Utwórz plik `.env` w katalogu głównym na podstawie szablonu `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Umieść plik klucza JSON konta usługowego Google (**Service Account**) w katalogu głównym pod nazwą `credentials.json`.
3. Udostępnij folder w Google Drive (rola **Viewer**) oraz plik Google Sheets (rola **Editor**) na adres e-mail konta usługowego.

### 3. Weryfikacja połączenia
Uruchom skrypt diagnostyczny, aby potwierdzić poprawność uprawnień do Google API:
```bash
source venv/bin/activate
python3 tests/verify_connection.py
```

### 4. Uruchomienie demona automatyzacji
```bash
python3 src/automation.py
```

---

## ⚙️ Zmienne Środowiskowe (`.env`)

Konfiguracja aplikacji zarządzana jest za pomocą pliku `.env`:

| Zmienna | Opis | Domyślna wartość |
|---------|------|------------------|
| `GOOGLE_DRIVE_FOLDER_ID` | ID folderu źródłowego na Google Drive | `1CLcyXsU1elN7t08SaiDWgIkJxSA1YTxu` |
| `GOOGLE_SPREADSHEET_ID` | ID arkusza Google Sheets | `1nyNnj-JOi_17nPCs11Fodx82d07w6i0z6bFZ7iFJwE8` |
| `CREDENTIALS_FILE` | Ścieżka do pliku klucza Service Account | `credentials.json` |
| `RUN_INTERVAL_HOURS` | Częstotliwość uruchamiania pętli (w godzinach) | `24` |
| `LINKEDIN_API_KEY` | Klucz API do serwisu LinkdAPI | (brak) |
| `AUTOMATION_MODE` | Tryb działania: `csv`, `linkedin` lub `both` | `csv` |

---

## 📂 Struktura Projektu

```
├── .agents/                    # Reguły, instrukcje i plany AGENTS-OS
│   └── plans/                  # Plany wdrożeń i architektury
├── src/                        # Kod źródłowy aplikacji
│   ├── __init__.py
│   ├── automation.py           # Główny koordynator / Demon
│   ├── config.py               # Konfiguracja środowiskowa
│   ├── google_client.py        # Klient API Google Drive i Sheets
│   ├── linkedin_client.py      # Klient LinkdAPI do odpytywania profili
│   └── parser.py               # Parser i mapowanie plików CSV
├── tests/                      # Testy i diagnostyka
│   ├── test_automation.py      # Testy jednostkowe z mockami dla CSV
│   ├── test_linkedin.py        # Testy jednostkowe dla LinkedIn
│   └── verify_connection.py    # Narzędzie diagnostyczne połączenia API
├── Dockerfile                  # Budowa bezpiecznego obrazu Docker
├── docker-compose.yml          # Konfiguracja kontenera produkcyjnego
├── setup.sh                    # Skrypt instalacji środowiska lokalnego
└── README.md                   # Niniejsza dokumentacja
```

---

## 🛠️ Opis Modułów

### 1. Koordynator (`src/automation.py`)
Główny punkt wejścia. Może być uruchomiony jako:
* **Jednorazowy przebieg**: `python3 src/automation.py --once`
* **Demon (pętla ciągła)**: `python3 src/automation.py` (sprawdza zmiany co interwał określony w `RUN_INTERVAL_HOURS`). Wykorzystuje bibliotekę `schedule` (lub fallback do `time.sleep`).

W zależności od zmiennej `AUTOMATION_MODE`:
* `csv` - pobiera i parsuje tylko pliki z dysku Google Drive.
* `linkedin` - odpytuje o profile i zapisuje liczbę obserwujących w Google Sheets.
* `both` - uruchamia obie pętle automatyzacji po kolei.

### 2. Integracja Google API (`src/google_client.py`)
Klasa `GoogleClient` realizuje całą bezpośrednią komunikację:
* `find_files_by_name(name_contains)`: Wyszukuje pliki w wyznaczonym folderze Drive.
* `download_file(file_id)`: Pobiera binarną zawartość pliku z Drive i dekoduje ją do UTF-8.
* `append_or_update_rows(sheet_name, records)`: Wszczepia dane o transakcjach na podstawie klucza `Data opercji`.
* `get_linkedin_profiles(sheet_name)`: Pobiera listę profili (kolumny `Nazwa` oraz `LinkedIn Username`) z zakładki `Profile`.
* `append_linkedin_followers(sheet_name, records)`: Zapisuje pomiary obserwujących w zakładce `LinkedIn_Followers`.

### 3. Klient LinkedIn (`src/linkedin_client.py`)
Klasa `LinkedInClient` komunikuje się z `api.linkdapi.com`:
* Pobiera dane profilu z endpointu `/v1/profile/{username}` przy użyciu nagłówka `X-API-Key`.
* Parsuje i zwraca pole `followerCount`.

### 4. Parser CSV (`src/parser.py`)
Funkcja `parse_csv(csv_content)` przetwarza pobrane pliki:
* Separator: średnik `;`
* Pomija pierwsze **26 linii nagłówka** (dane zaczynają się od linii 27).
* Mapuje kolumny według indeksów:
  * `0` -> `Data opercji`
  * `1` -> `Opis`
  * `3` -> `Kategoria`
  * `4` -> `Kwota`

---

## 🧪 Testowanie i Diagnostyka

### Testy Jednostkowe (Mock API)
Testy są całkowicie niezależne od połączenia sieciowego i bezpiecznie mockują zapytania HTTP do Google i LinkdAPI:
```bash
python3 -m unittest discover -s tests
```

### Diagnostyka Połączenia (Live Test)
Skrypt `tests/verify_connection.py` sprawdza kolejno:
1. Istnienie i strukturę pliku poświadczeń (`credentials.json`).
2. Poprawność uprawnień do odczytu folderu Google Drive.
3. Dostęp do zapisu w docelowym Google Sheets.

---

## 🐳 Konteneryzacja i VPS

Aplikacja jest przystosowana do pracy w chmurze i na serwerach VPS (np. Hostinger).

### Lokalny build i uruchomienie Docker:
```bash
docker compose up -d --build
```
Sprawdzenie stanu i logów:
```bash
docker compose ps
docker compose logs -f
```

---

## 🔒 Bezpieczeństwo i Zasady Kontroli Wersji
* **Brak sekretów w Git**: Pliki `credentials.json` oraz `.env` są wpisane do `.gitignore`. Nigdy nie wrzucaj ich do publicznych repozytoriów.
* **Zasada Minimalnych Uprawnień**: Konto usługowe Google nie potrzebuje żadnych ról IAM na poziomie projektu w chmurze Google. Uprawnienia przydziela się wyłącznie do pojedynczych zasobów na poziomie interfejsu Google Drive i Sheets.
