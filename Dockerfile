FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System-Pakete (für ggf. SQLite/SSL/Healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Statische Dateien zur Build-Zeit sammeln (DATA_DIR wird zur Laufzeit gesetzt)
RUN SECRET_KEY=build-only DJANGO_DEBUG=False \
    python manage.py collectstatic --noinput

RUN chmod +x docker-entrypoint.sh

# /data wird vom Host gemountet (DB + Medien liegen außerhalb des Containers)
ENV DATA_DIR=/data
VOLUME ["/data"]

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8001/login/ >/dev/null || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
