#!/usr/bin/env bash
# One-Shot-Installer für das Ticketsystem auf dem FBE-VPS.
#
# Was er macht (idempotent — kann beliebig oft laufen):
#   1. Holt aktuellen Code aus origin/main
#   2. Legt /opt/fbe-tools/ticket-data an, falls nicht vorhanden
#   3. Generiert /opt/fbe-tools/ticket.env mit zufälligem SECRET_KEY (nur beim ersten Mal)
#   4. Trägt den 'tickets'-Service in docker-compose.yml ein (falls noch nicht vorhanden)
#   5. Trägt den Caddy-Block für ticket.rss-fb.com ein (falls noch nicht vorhanden)
#   6. Baut den Container und startet ihn neu
#
# Aufruf:
#   ssh root@202.61.227.170
#   cd /opt/fbe-tools/tool-b
#   git fetch origin && git reset --hard origin/main
#   bash vps-install.sh

set -euo pipefail

STACK="/opt/fbe-tools"
REPO="$STACK/tool-b"
DATA="$STACK/ticket-data"
ENV_FILE="$STACK/ticket.env"
COMPOSE="$STACK/docker-compose.yml"
CADDY="$STACK/Caddyfile"

DOMAIN="ticket.rss-fb.com"

bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
info() { printf '  → %s\n' "$*"; }
warn() { printf '  ⚠ %s\n' "$*" >&2; }

bold "1/6  Code aktualisieren"
cd "$REPO"
git fetch origin
git reset --hard origin/main
git clean -fd
info "Aktueller Stand: $(git log -1 --oneline)"

bold "2/6  Datenordner sicherstellen"
mkdir -p "$DATA"
info "$DATA"

bold "3/6  Env-Datei prüfen"
if [ ! -f "$ENV_FILE" ]; then
    SECRET="$(openssl rand -base64 64 | tr -d '\n=+/' | head -c 64)"
    cat > "$ENV_FILE" <<EOF
# Auto-generiert von vps-install.sh – bei Bedarf anpassen.
DATA_DIR=/data
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=$SECRET
DJANGO_ALLOWED_HOSTS=$DOMAIN
CSRF_TRUSTED_ORIGINS=https://$DOMAIN

# Bootstrap-Admin (legt Account 'admin'/'admin' an, wenn noch keiner existiert)
BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=admin
BOOTSTRAP_ADMIN_EMAIL=admin@fb-eng.de

# E-Mail (optional – sonst landen Mails im Container-Log)
# EMAIL_HOST=smtp.deinprovider.de
# EMAIL_PORT=587
# EMAIL_HOST_USER=ticketsystem@fb-eng.de
# EMAIL_HOST_PASSWORD=geheim
# EMAIL_USE_TLS=True
# DEFAULT_FROM_EMAIL=ticketsystem@fb-eng.de
EOF
    chmod 600 "$ENV_FILE"
    info "Neu erstellt mit zufälligem SECRET_KEY: $ENV_FILE"
else
    info "Vorhanden – wird nicht überschrieben: $ENV_FILE"
fi

bold "4/6  docker-compose.yml prüfen"
if [ ! -f "$COMPOSE" ]; then
    warn "Kein docker-compose.yml gefunden! Lege Minimal-Datei an."
    cat > "$COMPOSE" <<'EOF'
services:
EOF
fi

if grep -qE '^  tickets:' "$COMPOSE"; then
    info "'tickets'-Service ist bereits eingetragen – nicht angefasst."
else
    info "'tickets'-Service wird angehängt."
    cat >> "$COMPOSE" <<'EOF'

  tickets:
    container_name: tickets
    build:
      context: ./tool-b
    restart: unless-stopped
    expose:
      - "8001"
    volumes:
      - ./ticket-data:/data
    env_file:
      - ./ticket.env
EOF
fi

bold "5/6  Caddyfile prüfen"
if [ ! -f "$CADDY" ]; then
    touch "$CADDY"
fi
if grep -q "$DOMAIN" "$CADDY"; then
    info "$DOMAIN-Block ist bereits in Caddyfile – nicht angefasst."
else
    info "Caddy-Block wird angehängt."
    cat >> "$CADDY" <<EOF

$DOMAIN {
    encode zstd gzip
    reverse_proxy tickets:8001 {
        header_up X-Forwarded-Proto {scheme}
        header_up X-Real-IP {remote}
    }
    request_body {
        max_size 25MB
    }
}
EOF
fi

bold "6/6  Container bauen & starten"
cd "$STACK"
docker compose up -d --build tickets
docker compose restart fbe-caddy >/dev/null 2>&1 || warn "Caddy konnte nicht neu gestartet werden – prüfe 'docker compose ps'"

bold "Fertig!"
echo
docker compose ps tickets fbe-caddy 2>/dev/null || docker compose ps
echo
echo "  Logs anzeigen:    docker compose logs --tail=50 -f tickets"
echo "  Login:            https://$DOMAIN/login/"
echo "  Bootstrap-Login:  admin / admin   (sofort unter /admin/ ändern!)"
echo
