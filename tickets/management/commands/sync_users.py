"""Synchronisiert User-Accounts aus einer JSON-Datei mit der Datenbank.

Datei-Format (users.json):
[
  {
    "username": "admin",
    "email": "admin@example.com",
    "password": "Geheim123!",
    "is_admin": true,
    "first_name": "Max",
    "last_name": "Muster"
  },
  ...
]

- Existiert ein User noch nicht → wird angelegt.
- Existiert er → E-Mail / Name / Admin-Status werden aktualisiert.
- Passwort wird nur gesetzt, wenn das Feld "password" gefüllt ist
  (so kannst du es nach dem ersten Setup leer lassen, ohne es zu überschreiben).
- Mit --prune werden User, die in der DB sind aber nicht in der Datei,
  deaktiviert (is_active=False). Sie werden NICHT gelöscht (Tickets bleiben erhalten).
"""
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Synchronisiert User aus users.json mit der Datenbank."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="users.json", help="Pfad zur User-Datei (Default: users.json)")
        parser.add_argument("--prune", action="store_true", help="Nicht aufgelistete User deaktivieren")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"Datei nicht gefunden: {path.resolve()}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"Ungültiges JSON in {path}: {e}")

        if not isinstance(data, list):
            raise CommandError("users.json muss eine Liste von Objekten sein.")

        seen = set()
        for entry in data:
            username = entry.get("username")
            if not username:
                self.stderr.write(self.style.WARNING(f"Eintrag ohne 'username' übersprungen: {entry}"))
                continue
            seen.add(username)

            email = entry.get("email", "")
            first_name = entry.get("first_name", "")
            last_name = entry.get("last_name", "")
            is_admin = bool(entry.get("is_admin", False))
            password = entry.get("password") or ""

            user, created = User.objects.get_or_create(username=username)
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = is_admin
            user.is_superuser = is_admin
            user.is_active = True
            if password:
                user.set_password(password)
            user.save()

            verb = "angelegt" if created else "aktualisiert"
            role = "Admin" if is_admin else "User"
            self.stdout.write(self.style.SUCCESS(f"  ✓ {role} '{username}' {verb}"))

        if opts["prune"]:
            qs = User.objects.exclude(username__in=seen).filter(is_active=True)
            count = qs.update(is_active=False)
            if count:
                self.stdout.write(self.style.WARNING(f"  ! {count} nicht-gelistete(r) User deaktiviert"))

        self.stdout.write(self.style.SUCCESS(f"Fertig. {len(seen)} User aus {path} synchronisiert."))
