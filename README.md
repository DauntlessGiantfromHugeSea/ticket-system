# IT-Ticketsystem · FB Engineering

Django-basiertes IT-Ticketsystem (Branding `#92c57a` + FBE-Logo, Freshdesk-Stil).
Läuft auf dem VPS als Docker-Container hinter Caddy.

- **URL:** <https://ticket.rss-fb.com>
- **Admin-Panel:** <https://ticket.rss-fb.com/admin/>
- **Container:** `tickets` (intern Port `8001`)
- **Repo-Pfad auf dem VPS:** `/opt/fbe-tools/tool-b`
- **Persistenter Datenordner:** `/opt/fbe-tools/ticket-data` (enthält `db.sqlite3` + `media/`)

## Features

- Login per Benutzername+Passwort, Accounts werden vom Admin angelegt
- User sehen nur eigene Tickets, Admins sehen alles
- Tickets: Titel, Beschreibung, Priorität, Kategorie, Datei-Anhänge
- Status-Workflow: Offen → In Arbeit → Gelöst → Geschlossen, mit **Archiv**
- Großer **Schließen-Button** für Admins (mit „Wieder öffnen" im Archiv)
- **Aufwandserfassung** pro Ticket (Datum, km, Std., Material, Tätigkeit) mit Summenzeile
- Kommentare/Conversation im Freshdesk-Stil (mit Avataren, Admin farblich hervorgehoben)
- Prominente Ersteller-Box oben (Name, E-Mail, Datum)
- E-Mail-Benachrichtigungen (asynchron, blockiert nicht den Save)
- Bootstrap-Admin beim ersten Start automatisch (`admin` / `admin`)
- WhiteNoise für stabile Static-Files
- HSTS + sichere Cookies bei `DEBUG=False`

---

## Erstes Aufsetzen auf dem VPS

### 1. Repo klonen

```bash
mkdir -p /opt/fbe-tools/ticket-data
cd /opt/fbe-tools
git clone https://github.com/DauntlessGiantfromHugeSea/ticket-system.git tool-b
```

### 2. Service in `docker-compose.yml` eintragen

Inhalt aus `tool-b/deploy/docker-compose.snippet.yml` in
`/opt/fbe-tools/docker-compose.yml` unter `services:` einfügen.
**Wichtig:** `DJANGO_SECRET_KEY` durch einen langen Zufallsstring ersetzen
(z. B. `openssl rand -base64 50`).

### 3. Caddy-Block einfügen

Inhalt aus `tool-b/deploy/Caddyfile.snippet` in `/opt/fbe-tools/Caddyfile` einfügen.

### 4. DNS prüfen

```bash
dig +short ticket.rss-fb.com    # → 202.61.227.170
```

### 5. Starten

```bash
cd /opt/fbe-tools
docker compose up -d --build tickets
docker compose restart fbe-caddy
```

### 6. Login

<https://ticket.rss-fb.com/login/> — mit `admin` / `admin` einloggen, dann
**sofort** unter `/admin/` Passwort ändern oder Account löschen.

---

## Update einspielen

```bash
cd /opt/fbe-tools/tool-b
git fetch origin
git reset --hard origin/main
git clean -fd

cd /opt/fbe-tools
docker compose up -d --build tickets
docker compose logs --tail=100 tickets
```

Datenbank (`/opt/fbe-tools/ticket-data/db.sqlite3`) bleibt erhalten —
liegt außerhalb des Containers/Repos. Migrationen laufen automatisch beim Start.

---

## Backups

```cron
0 3 * * * tar czf /opt/fbe-tools/backups/ticket-$(date +\%F).tgz -C /opt/fbe-tools ticket-data
0 4 * * 0 find /opt/fbe-tools/backups -name 'ticket-*.tgz' -mtime +30 -delete
```

```bash
mkdir -p /opt/fbe-tools/backups
```

---

## User verwalten

### Variante A — über `/admin/` (empfohlen für wenige User)
**Users → Add user**, danach für Admin-Rechte das Häkchen bei **Staff status** (und ggf. **Superuser status**) setzen.

### Variante B — über `users.json` (für viele User)

```bash
cd /opt/fbe-tools/tool-b
cp users.example.json /opt/fbe-tools/ticket-data/users.json
nano /opt/fbe-tools/ticket-data/users.json
chmod 600 /opt/fbe-tools/ticket-data/users.json

docker compose exec tickets python manage.py sync_users \
    --file /data/users.json
```

`users.json` ist gitignored und wird im persistenten Datenordner abgelegt.

---

## Konfiguration (Container-Env-Variablen)

| Variable | Default | Bedeutung |
|---|---|---|
| `DATA_DIR` | `/data` | Persistenter Ordner für DB + Media |
| `DJANGO_SECRET_KEY` | – | **Zwingend selbst setzen** |
| `DJANGO_DEBUG` | `True` | In Produktion `False` |
| `DJANGO_ALLOWED_HOSTS` | `*` | `ticket.rss-fb.com` |
| `CSRF_TRUSTED_ORIGINS` | – | `https://ticket.rss-fb.com` |
| `BOOTSTRAP_ADMIN_USERNAME` / `_PASSWORD` / `_EMAIL` | `admin` / `admin` / … | Auto-Admin beim ersten Start |
| `BOOTSTRAP_ADMIN_DISABLED` | – | Auf `1` zum Deaktivieren |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | – | SMTP (sonst Console-Backend) |
| `GUNICORN_WORKERS` | `3` | Anzahl Worker-Prozesse |

---

## Lokale Entwicklung (ohne Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

→ <http://127.0.0.1:8000/> · Login `admin` / `admin`

## Tests

```bash
python manage.py test
```

oder im Container:

```bash
docker compose exec tickets python manage.py test
```

---

## Wichtig

> ⚠ **Niemals löschen:** `/opt/fbe-tools/ticket-data/db.sqlite3`
> Enthält alle User, Tickets, Kommentare und WorkLogs.
