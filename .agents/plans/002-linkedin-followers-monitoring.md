# [SEQ-PRO] Plan 002: Wdrożenie Monitorowania Obserwujących (LinkedIn) z użyciem LinkdAPI i Google Sheets

## 📋 1. Opis Zadania i Założenia
Cel: Integracja nowej automatyzacji w Pythonie, która pobiera listę profili LinkedIn z Google Sheets, odpytuje zewnętrzne API (LinkdAPI) o liczbę obserwujących (followers) i zapisuje wyniki (logi historyczne) do innej zakładki w Google Sheets.

Założenia architektoniczne i kolumny:
1. **Google Sheets**:
   * Zakładka **`Profile`** – zawiera kolumny:
     * `Nazwa`
     * `LinkedIn Username`
   * Zakładka **`LinkedIn_Followers`** – zawiera kolumny:
     * `Data pomiaru`
     * `Nazwa profilu`
     * `Obserwujący`
2. **LinkdAPI**:
   * Punkt końcowy (endpoint): `https://api.linkdapi.com/v1/profile/{username}`
   * Nagłówek autoryzacji: `X-API-Key`
   * Klucz w odpowiedzi JSON: `followerCount`
   * Pobierany z konfiguracji: `LINKEDIN_API_KEY` (zapisany w `.env`).

---

## 🛠️ 2. Fazy Implementacji

### 1. Faza: Konfiguracja Środowiska (Local Setup)
- Dodanie nowej zmiennej do `.env.example` oraz `.env`:
  `LINKEDIN_API_KEY=twoj_klucz_api_linkdapi`
- Upewnienie się, że plik `.env` jest ignorowany w `.gitignore`.

### 2. Faza: Implementacja Kodów (Builder Task)
- **`src/linkedin_client.py`**:
  * Nowy moduł wykonujący bezpośrednie zapytanie HTTP GET do `https://api.linkdapi.com/v1/profile/{username}` z nagłówkiem `X-API-Key`.
  * Parsowanie klucza `followerCount`.
  * Wdrożenie obsługi błędów (np. błędny API key, profil nie istnieje, limit zapytań).
- **`src/config.py`**:
  * Dodanie zmiennej `LINKEDIN_API_KEY` (domyślnie `""`) oraz nazwy zakładki źródłowej ("Profile") i docelowej ("LinkedIn_Followers").
- **`src/automation.py`**:
  * Dodanie nowej logiki (funkcji `run_linkedin_monitoring()`), która:
    1. Pobiera listę profili z zakładki `Profile` w Google Sheets.
    2. Odpytuje LinkdAPI dla każdego użytkownika.
    3. Zapisuje wyniki do zakładki `LinkedIn_Followers` w Google Sheets.
  * Umożliwienie wyboru trybu uruchomienia (np. pobieranie plików CSV vs. monitorowanie LinkedIn) za pomocą zmiennej środowiskowej `AUTOMATION_MODE` (`csv`, `linkedin` lub `both`).

### 3. Faza: Testowanie (Lokalna Weryfikacja)
- **`tests/test_linkedin.py`**:
  * Testy jednostkowe z mockowaniem odpowiedzi z LinkdAPI (udany odczyt, brak profilu, błędy sieciowe).
  * Testy integracyjne z mockowaniem Google Sheets API (zapisywanie wierszy).

---

## 🔒 3. Bezpieczeństwo i Walidacja (Verification Plan)
- **Klucz API**: `LINKEDIN_API_KEY` nigdy nie jest zapisywany w kodzie.
- **Walidacja danych**: Skrypt obsługuje puste lub niepoprawne nazwy użytkowników LinkedIn bez przerywania działania dla pozostałych profili.

---

## 🤝 4. Warunek Handshake (Ukończenie Planu)
Zadanie zostanie uznane za kompletne po:
1. Pomyślnym przebiegu testów jednostkowych dla nowego modułu LinkedIn.
2. Zaktualizowaniu backlogu w `task.md`.
3. "Handshake Verified: Plan-Alignment and Math-Consistency checked. Ready for Coordinator Push."
