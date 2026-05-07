"""Bootstrap-Admin: legt beim ersten `migrate` automatisch einen Admin-Account an,
falls noch keiner existiert. Damit kannst du dich nach dem Deploy sofort einloggen
und dann via /admin/ dein eigenes Passwort setzen oder den Account löschen.

Defaults (überschreibbar per Umgebungsvariable):
    BOOTSTRAP_ADMIN_USERNAME = "admin"
    BOOTSTRAP_ADMIN_PASSWORD = "admin"
    BOOTSTRAP_ADMIN_EMAIL    = "admin@example.com"

Ist BOOTSTRAP_ADMIN_DISABLED=1 gesetzt, wird nichts erzeugt.
"""
import logging
import os
import sys

from django.db.models.signals import post_migrate
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_bootstrap_admin(sender, **kwargs):
    if sender.name != "tickets":
        return
    if os.environ.get("BOOTSTRAP_ADMIN_DISABLED", "").lower() in ("1", "true", "yes"):
        return
    # Beim Ausführen der Test-Suite niemals Bootstrap-Admin erzeugen
    if "test" in sys.argv:
        return

    from django.contrib.auth import get_user_model

    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return

    username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "admin")
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")

    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email, "is_staff": True, "is_superuser": True, "is_active": True},
    )
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.email = email
    user.set_password(password)
    user.save()

    msg = (
        f"\n{'=' * 60}\n"
        f"  BOOTSTRAP-ADMIN {'angelegt' if created else 'aktualisiert'}:\n"
        f"    Benutzername: {username}\n"
        f"    Passwort:     {password}\n"
        f"  >>> SOFORT ändern oder Account löschen unter /admin/ <<<\n"
        f"{'=' * 60}\n"
    )
    logger.warning(msg)
    print(msg)
