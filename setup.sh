#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== INICJALIZACJA ŚRODOWISKA LOKALNEGO PYTHONA ==="

# 1. Sprawdzenie czy python3 jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "❌ Błąd: Python3 nie jest zainstalowany w systemie."
    echo "   Zainstaluj go komendą: sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi

# 2. Tworzenie wirtualnego środowiska venv
if [ ! -d "venv" ]; then
    echo "1. Tworzenie środowiska wirtualnego 'venv'..."
    python3 -m venv venv || {
        echo "❌ Błąd: Nie udało się utworzyć venv. Prawdopodobnie brakuje pakietu python3-venv."
        echo "   Zainstaluj go komendą: sudo apt update && sudo apt install -y python3-venv"
        exit 1
    }
    echo "   ✅ Środowisko venv utworzone."
else
    echo "1. Środowisko wirtualnego 'venv' już istnieje. Pomijam tworzenie."
fi

# 3. Aktywacja środowiska i instalacja pip oraz zależności
echo "2. Aktywacja środowiska venv..."
source venv/bin/activate

echo "3. Aktualizacja pip..."
python3 -m ensurepip --upgrade || true
python3 -m pip install --upgrade pip || true

if [ -f "requirements.txt" ]; then
    echo "4. Instalacja bibliotek z requirements.txt..."
    python3 -m pip install -r requirements.txt
    echo "   ✅ Biblioteki zainstalowane pomyślnie."
else
    echo "⚠️  Ostrzeżenie: Brak pliku requirements.txt!"
fi

# 5. Kopiowanie pliku .env (jeśli nie istnieje)
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "5. Kopiowanie .env.example do .env..."
        cp .env.example .env
        echo "   ✅ Plik .env został utworzony. Uzupełnij go."
    else
        echo "5. Tworzenie czystego pliku .env..."
        cat << 'ENV' > .env
GOOGLE_DRIVE_FOLDER_ID=1CLcyXsU1elN7t08SaiDWgIkJxSA1YTxu
GOOGLE_SPREADSHEET_ID=1nyNnj-JOi_17nPCs11Fodx82d07w6i0z6bFZ7iFJwE8
CREDENTIALS_FILE=credentials.json
RUN_INTERVAL_HOURS=24
ENV
        echo "   ✅ Utworzono plik .env."
    fi
else
    echo "5. Plik .env już istnieje. Pomijam tworzenie."
fi

echo ""
echo "🎉 GOTOWE! Środowisko lokalne zostało skonfigurowane."
echo "--------------------------------------------------------"
echo "Aby rozpocząć pracę:"
echo "1. Aktywuj środowisko wirtualne:"
echo "   source venv/bin/activate"
echo "2. Uruchom test połączenia z Google API:"
echo "   python3 tests/verify_connection.py"
echo "--------------------------------------------------------"
