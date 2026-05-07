# IT-Ticketsystem

Ein einfaches, stabiles IT-Ticketsystem auf Basis von **Django 5**.
User können sich mit Benutzername + Passwort anmelden und Tickets eröffnen.
Admins sehen alle Tickets, können sie bearbeiten, zuweisen, kommentieren und
den Status ändern.

## Features

- Login per Benutzername + Passwort (Accounts werden vom Admin erstellt)
- Tickets: Titel, Beschreibung, Priorität, Kategorie, Datei-Anhänge
- Status-Workflow: Offen → In Arbeit → Gelöst → Geschlossen
- Kommentare zwischen User & Admin
- Ticket-Zuweisung an Admins
- E-Mail-Benachrichtigungen (Konsole oder SMTP)
- Filter & Suche
- Eingebautes Django-Admin-Panel unter `/admin/`
- **Bootstrap-Admin**: beim ersten Setup wird automatisch ein Admin angelegt
- Produktions-tauglich: WhiteNoise (Static-Files), HSTS, sichere Cookies bei `DEBUG=False`

---

## Schnellstart auf dem VPS

```bash
git clone <repo-url> ticket-system
cd ticket-system
cp .env.example .env
nano .env                      # Domain, Secret-Key, ggf. Admin-Passwort anpassen
./deploy.sh                    # installiert alles und legt Bootstrap-Admin an
```

Beim ersten Lauf wird ein Admin-Account angelegt (Default: `admin` / `admin`,
sofern in `.env` nicht überschrieben). Das ausgegebene Passwort steht im Output
von `deploy.sh`.

**Sofort nach dem ersten Login** unter `/admin/` → **Users** → `admin`:
- Passwort ändern **oder**
- den Account löschen, nachdem du dir einen eigenen Admin angelegt hast.

Server starten:
```bash
source .venv/bin/activate
gunicorn --workers 3 --bind 0.0.0.0:8000 ticketsystem.wsgi:application
```

Für Produktion: `deploy/ticketsystem.service` (systemd) und `deploy/nginx.conf`
in das System kopieren — siehe [Produktions-Setup](#produktions-setup).

---

## Lokale Entwicklung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./deploy.sh
python manage.py runserver
```

Browser: <http://127.0.0.1:8000/>
Login: `admin` / `admin`

---

## User verwalten

### Variante A: über `/admin/` (empfohlen für wenige User)

**Users** → *Add user*. Häkchen bei **Staff status** = Admin-Rechte fürs Ticket-System.

### Variante B: über `users.json` (empfohlen für viele User)

```bash
cp users.example.json users.json
nano users.json                       # User eintragen
chmod 600 users.json
python manage.py sync_users           # User in DB übernehmen
python manage.py sync_users --prune   # nicht-gelistete User deaktivieren
```

`users.json` ist gitignored (enthält Klartext-Passwörter).

---

## Konfiguration (`.env`)

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `DJANGO_SECRET_KEY` | dev-Key | **In Produktion zwingend setzen** |
| `DJANGO_DEBUG` | `True` | In Produktion auf `False` |
| `DJANGO_ALLOWED_HOSTS` | `*` | z. B. `tickets.deinedomain.de` |
| `CSRF_TRUSTED_ORIGINS` | – | z. B. `https://tickets.deinedomain.de` |
| `BOOTSTRAP_ADMIN_USERNAME` | `admin` | Auto-Admin Username |
| `BOOTSTRAP_ADMIN_PASSWORD` | `admin` | Auto-Admin Passwort |
| `BOOTSTRAP_ADMIN_EMAIL` | `admin@example.com` | Auto-Admin E-Mail |
| `BOOTSTRAP_ADMIN_DISABLED` | – | Auf `1` setzen, um Bootstrap zu deaktivieren |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | – | SMTP-Konfiguration |
| `DEFAULT_FROM_EMAIL` | `ticketsystem@example.com` | Absender |

---

## Produktions-Setup

### 1. Mit `deploy.sh` aufsetzen
```bash
./deploy.sh
```

### 2. systemd-Service installieren
```bash
sudo cp deploy/ticketsystem.service /etc/systemd/system/
sudo nano /etc/systemd/system/ticketsystem.service   # Pfade/User anpassen
sudo systemctl daemon-reload
sudo systemctl enable --now ticketsystem
sudo systemctl status ticketsystem
```

### 3. Nginx als Reverse-Proxy
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/ticketsystem
sudo nano /etc/nginx/sites-available/ticketsystem    # Domain anpassen
sudo ln -s /etc/nginx/sites-available/ticketsystem /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 4. HTTPS mit Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tickets.deinedomain.de
```

### 5. Update einspielen
```bash
git pull
./deploy.sh
sudo systemctl restart ticketsystem
```

---

## Backup

```cron
# Täglich 03:00 Uhr DB + Uploads sichern, alte Backups löschen
0 3 * * * tar czf ~/backup-$(date +\%F).tgz -C ~/ticket-system db.sqlite3 media/
0 4 * * 0 find ~ -maxdepth 1 -name 'backup-*.tgz' -mtime +30 -delete
```

---

## Tests

```bash
python manage.py test
```
