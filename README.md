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

### Weitere User anlegen

Über `/admin/` → **Users** → *Add user*. Soll der User Admin-Rechte bekommen,
das Häkchen bei **Staff status** setzen.

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
