# IT-Ticketsystem

Ein einfaches, stabiles IT-Ticketsystem auf Basis von **Django 5**.
User können sich mit Benutzername + Passwort anmelden und Tickets eröffnen.
Admins (Django-Staff-User) sehen alle Tickets, können sie bearbeiten,
zuweisen, kommentieren und den Status ändern.

## Features

- Login per Benutzername + Passwort (Accounts werden ausschließlich vom Admin erstellt)
- Tickets mit Titel, Beschreibung, Priorität (niedrig/mittel/hoch/kritisch),
  Kategorie (Hardware/Software/Netzwerk/Account/Sonstiges) und Datei-Anhängen
- Status-Workflow: Offen → In Arbeit → Gelöst → Geschlossen
- Kommentare/Antworten zwischen User und Admin
- Tickets können einem Admin zugewiesen werden
- E-Mail-Benachrichtigungen bei: neuem Ticket (an alle Admins), neuen Kommentaren,
  Statusänderung (an den Ersteller)
- Filter & Suche in der Ticketliste
- Eingebautes Django-Admin-Panel unter `/admin/`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 manage.py migrate
python3 manage.py createsuperuser   # Erster Admin
python3 manage.py runserver
```

Aufruf im Browser: <http://127.0.0.1:8000/>

### User per Datei verwalten (empfohlen)

Alle User stehen in `users.json` (eine Vorlage liegt als `users.example.json` bei).
Format:

```json
[
  { "username": "admin", "email": "a@x.de", "password": "Geheim!", "is_admin": true },
  { "username": "max",   "email": "m@x.de", "password": "Start#1",  "is_admin": false }
]
```

Anlegen / Aktualisieren:

```bash
cp users.example.json users.json   # einmalig
nano users.json                    # User eintragen / Passwörter setzen
python3 manage.py sync_users       # User in DB anlegen oder aktualisieren
```

- Felder ändern → erneut `sync_users` ausführen.
- Passwort ändern → in der Datei setzen und `sync_users` ausführen.
- Passwort leer lassen → bestehendes Passwort bleibt unverändert.
- Mit `--prune` werden in der DB vorhandene, aber nicht in der Datei gelistete
  User **deaktiviert** (gelöscht wird nichts, damit Tickets erhalten bleiben).

> ⚠️ `users.json` enthält Klartext-Passwörter und ist in `.gitignore` —
> niemals committen, Datei nur für `root` lesbar machen:
> `chmod 600 users.json`

### Alternativ: User per Web-Admin

Über `/admin/` → **Users** → *Add user*. Für Admin-Rechte das Häkchen bei
**Staff status** (und ggf. **Superuser status**) setzen.

## Konfiguration über Umgebungsvariablen

| Variable | Default | Bedeutung |
|----------|---------|-----------|
| `DJANGO_SECRET_KEY` | dev-Key | Für Produktion zwingend setzen |
| `DJANGO_DEBUG` | `True` | In Produktion auf `False` setzen |
| `DJANGO_ALLOWED_HOSTS` | `*` | Komma-separierte Hostliste |
| `EMAIL_HOST` | – | Wenn gesetzt, wird SMTP statt Konsole verwendet |
| `EMAIL_PORT` | `587` | |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | – | SMTP-Credentials |
| `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | `True` / `False` | |
| `DEFAULT_FROM_EMAIL` | `ticketsystem@example.com` | Absender |

Ohne `EMAIL_HOST` werden E-Mails in der Konsole ausgegeben – ideal für die Entwicklung.

## Tests

```bash
python3 manage.py test
```

## Projektstruktur

```
ticketsystem/   # Django-Projekt (settings, urls)
tickets/        # App: Models, Views, Forms, Admin, Tests
templates/      # HTML-Templates
```
