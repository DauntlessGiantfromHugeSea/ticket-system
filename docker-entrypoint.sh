#!/usr/bin/env bash
set -e

echo "▶ DATA_DIR=${DATA_DIR:-/data}"
mkdir -p "${DATA_DIR:-/data}/media"

echo "▶ Datenbank migrieren…"
python manage.py migrate --noinput

echo "▶ Starte Gunicorn auf :8001"
exec gunicorn ticketsystem.wsgi:application \
    --bind 0.0.0.0:8001 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
