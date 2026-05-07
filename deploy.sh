#!/usr/bin/env bash
# Deploy- / Update-Skript für das Ticketsystem.
# Benutzung:  ./deploy.sh            (erstes Setup oder Update)
# Funktioniert auf jedem Linux-Server mit Python 3.10+.
#
# Beim ersten Lauf wird automatisch ein Admin-Account erzeugt:
#     Benutzername: admin
#     Passwort:     admin
# Nach dem ersten Login SOFORT unter /admin/ Passwort ändern oder Account löschen!

set -euo pipefail

cd "$(dirname "$0")"

echo "▶ Virtualenv vorbereiten…"
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

echo "▶ Abhängigkeiten installieren…"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# .env laden, wenn vorhanden
if [ -f .env ]; then
    set -a
    # shellcheck source=/dev/null
    source .env
    set +a
fi

echo "▶ Datenbank migrieren (legt ggf. Bootstrap-Admin an)…"
python manage.py migrate --noinput

echo "▶ Static-Files sammeln…"
python manage.py collectstatic --noinput >/dev/null

echo
echo "✅ Fertig. Server starten mit:"
echo "     source .venv/bin/activate"
echo "     gunicorn --workers 3 --bind 0.0.0.0:8000 ticketsystem.wsgi:application"
echo
echo "   oder im Entwicklungsmodus:"
echo "     python manage.py runserver 0.0.0.0:8000"
