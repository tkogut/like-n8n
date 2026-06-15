# 🏠 Instrukcja konfiguracji projektu na nowym komputerze (Home Setup)

Przenosząc się na inny komputer, musisz odtworzyć środowisko uruchomieniowe oraz przenieść pliki konfiguracyjne i klucze, które nie są śledzone przez Git ze względów bezpieczeństwa.

---

## 🛠️ 1. Co musisz przenieść (Pliki Wrażliwe)
Te dwa pliki są ignorowane w `.gitignore` i **musisz je skopiować na nowy komputer** (np. za pomocą pendrive'a, SCP lub innego bezpiecznego sposobu):
1. `.env` – plik ze zmiennymi środowiskowymi (zawiera identyfikatory folderów i arkuszy).
2. `credentials.json` – plik klucza JSON konta usługowego Google (Service Account).

---

## 🚀 2. Krok po kroku na nowym komputerze

### Krok A: Pobranie kodu
Sklonuj repozytorium na nowym komputerze:
```bash
git clone <URL_TWOJEGO_REPOZYTORIUM>
cd like-n8n
```

### Krok B: Umieszczenie plików wrażliwych
Skopiuj przeniesione pliki `.env` oraz `credentials.json` bezpośrednio do głównego katalogu projektu (`like-n8n/`).

### Krok C: Automatyczna instalacja środowiska
Uruchom przygotowany skrypt instalacyjny. Skrypt automatycznie utworzy izolowane środowisko `venv`, zaktualizuje `pip` i pobierze wszystkie wymagane biblioteki z `requirements.txt`:
```bash
./setup.sh
```
*(Uwaga: Jeśli system poinformuje o braku pakietu `python3-venv`, zainstaluj go komendą: `sudo apt update && sudo apt install -y python3-venv`, a następnie uruchom `./setup.sh` ponownie).*

### Krok D: Aktywacja i Test Połączenia
Aktywuj wirtualne środowisko i uruchom nasz test diagnostyczny, aby potwierdzić, że autoryzacja z Google API działa poprawnie na nowym sprzęcie:
```bash
source venv/bin/activate
python3 tests/verify_connection.py
```

---

## 🏃 3. Uruchamianie automatyzacji

### Opcja 1: Uruchomienie lokalne (w pythonie)
Po aktywacji środowiska (`source venv/bin/activate`), możesz uruchomić skrypt automatyzacji, który będzie działał w pętli i odpytywał Google API zgodnie z zadanym interwałem:
```bash
python3 src/automation.py
```

### Opcja 2: Uruchomienie w Dockerze (rekomendowane, jeśli zainstalujesz Dockera)
Jeśli na nowym komputerze zainstalujesz Dockera, możesz uruchomić usługę za pomocą komendy:
```bash
docker compose up -d --build
```
Logi kontenera sprawdzisz przez: `docker compose logs -f`.

---

## 💬 4. Odczytanie historii tej rozmowy
W katalogu `tmp/` znajduje się wyeksportowany plik z pełną historią naszej rozmowy:
* **[conversation_history.md](file:///home/tkogut/projects/like-n8n/tmp/conversation_history.md)**

Możesz go otworzyć w dowolnym edytorze Markdown (lub na GitHubie), aby prześledzić dyskusję, podjęte decyzje oraz komendy wykonane podczas tworzenia tej automatyzacji.

---

> [!IMPORTANT]
> **Bezpieczeństwo**: Never delete `credentials.json` or `.env` entries from `.gitignore`. This prevents accidentally publishing your access keys to GitHub.
