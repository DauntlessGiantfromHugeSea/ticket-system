from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Ticket(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Niedrig"
        MEDIUM = "medium", "Mittel"
        HIGH = "high", "Hoch"
        CRITICAL = "critical", "Kritisch"

    class Category(models.TextChoices):
        HARDWARE = "hardware", "Hardware"
        SOFTWARE = "software", "Software"
        NETWORK = "network", "Netzwerk"
        ACCOUNT = "account", "Account / Zugang"
        OTHER = "other", "Sonstiges"

    class Status(models.TextChoices):
        OPEN = "open", "Offen"
        IN_PROGRESS = "in_progress", "In Arbeit"
        RESOLVED = "resolved", "Gelöst"
        CLOSED = "closed", "Geschlossen"

    title = models.CharField("Titel", max_length=200)
    description = models.TextField("Beschreibung")
    priority = models.CharField("Priorität", max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    category = models.CharField("Kategorie", max_length=20, choices=Category.choices, default=Category.OTHER)
    status = models.CharField("Status", max_length=20, choices=Status.choices, default=Status.OPEN)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tickets",
        verbose_name="Erstellt von",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        null=True,
        blank=True,
        limit_choices_to={"is_staff": True},
        verbose_name="Zugewiesen an",
    )

    created_at = models.DateTimeField("Erstellt am", auto_now_add=True)
    updated_at = models.DateTimeField("Geändert am", auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"#{self.pk} - {self.title}"

    def get_absolute_url(self):
        return reverse("ticket_detail", args=[self.pk])

    @property
    def is_closed(self):
        return self.status in (self.Status.RESOLVED, self.Status.CLOSED)


def attachment_upload_path(instance, filename):
    return f"tickets/{instance.ticket_id}/{filename}"


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField("Datei", upload_to=attachment_upload_path)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    body = models.TextField("Kommentar")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Kommentar von {self.author} zu {self.ticket}"


class WorkLog(models.Model):
    """Aufwandserfassung pro Ticket (nur für Admins).

    Trägt Anfahrt, Zeitaufwand, eingesetztes Material und eine
    Tätigkeitsbeschreibung ein. Mehrere Einträge pro Ticket möglich.
    """

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="worklogs")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="worklogs",
        verbose_name="Bearbeiter",
    )
    date = models.DateField("Datum", default=timezone.localdate)
    travel_km = models.DecimalField(
        "Anfahrt (km)", max_digits=7, decimal_places=1, default=0,
        help_text="Gefahrene Kilometer (einfach oder Hin+Rück, wie ihr es handhabt).",
    )
    hours = models.DecimalField(
        "Zeitaufwand (Std.)", max_digits=5, decimal_places=2, default=0,
        help_text="Stunden, z. B. 1.5 für 1 Std 30 Min.",
    )
    material = models.TextField(
        "Material", blank=True,
        help_text="Eingesetzte Teile/Material, z. B. '1× Netzteil 65W, 2m Patchkabel'.",
    )
    description = models.TextField("Durchgeführte Arbeiten", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Aufwand"
        verbose_name_plural = "Aufwände"

    def __str__(self):
        return f"{self.date} – {self.hours}h – {self.ticket}"
