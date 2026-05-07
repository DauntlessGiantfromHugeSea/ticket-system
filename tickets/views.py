import logging
import threading

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AttachmentForm,
    CommentForm,
    TicketAdminUpdateForm,
    TicketCreateForm,
    WorkLogForm,
)
from .models import Attachment, Ticket, WorkLog

User = get_user_model()
logger = logging.getLogger(__name__)


def _notify(subject, body, recipients):
    """Verschickt E-Mails im Hintergrund-Thread, damit der Request nicht blockiert."""
    recipients = [r for r in recipients if r]
    if not recipients:
        return

    def _send():
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
        except Exception as e:
            logger.warning("E-Mail-Versand fehlgeschlagen: %s", e)

    threading.Thread(target=_send, daemon=True).start()


ARCHIVE_STATUSES = ("resolved", "closed")


@login_required
def ticket_list(request):
    """Aktive Tickets (ohne Archiv)."""
    qs = Ticket.objects.select_related("created_by", "assigned_to").exclude(status__in=ARCHIVE_STATUSES)
    if not request.user.is_staff:
        qs = qs.filter(created_by=request.user)
    return _render_ticket_list(request, qs, archive=False)


@login_required
def ticket_archive(request):
    """Geschlossene/gelöste Tickets."""
    qs = Ticket.objects.select_related("created_by", "assigned_to").filter(status__in=ARCHIVE_STATUSES)
    if not request.user.is_staff:
        qs = qs.filter(created_by=request.user)
    return _render_ticket_list(request, qs, archive=True)


def _render_ticket_list(request, qs, archive):
    status = request.GET.get("status")
    priority = request.GET.get("priority")
    category = request.GET.get("category")
    q = request.GET.get("q")
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    return render(
        request,
        "tickets/ticket_list.html",
        {
            "tickets": qs,
            "archive": archive,
            "status_choices": Ticket.Status.choices,
            "priority_choices": Ticket.Priority.choices,
            "category_choices": Ticket.Category.choices,
            "filters": {
                "status": status or "",
                "priority": priority or "",
                "category": category or "",
                "q": q or "",
            },
        },
    )


@login_required
def ticket_close(request, pk):
    if not request.user.is_staff or request.method != "POST":
        return HttpResponseForbidden()
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.status = Ticket.Status.CLOSED
    ticket.save(update_fields=["status", "updated_at"])
    if ticket.created_by.email:
        _notify(
            f"[Ticket #{ticket.pk}] Geschlossen",
            f"Dein Ticket '{ticket.title}' wurde geschlossen.",
            [ticket.created_by.email],
        )
    messages.success(request, f"Ticket #{ticket.pk} wurde geschlossen und ins Archiv verschoben.")
    return redirect("ticket_list")


@login_required
def ticket_reopen(request, pk):
    if not request.user.is_staff or request.method != "POST":
        return HttpResponseForbidden()
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.status = Ticket.Status.OPEN
    ticket.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Ticket #{ticket.pk} wurde wieder geöffnet.")
    return redirect(ticket.get_absolute_url())


@login_required
def ticket_create(request):
    if request.method == "POST":
        form = TicketCreateForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            for f in form.cleaned_data.get("attachments", []):
                Attachment.objects.create(ticket=ticket, file=f, uploaded_by=request.user)

            admin_emails = list(
                User.objects.filter(is_staff=True).exclude(email="").values_list("email", flat=True)
            )
            _notify(
                subject=f"[Ticket #{ticket.pk}] Neues Ticket: {ticket.title}",
                body=(
                    f"Ein neues Ticket wurde von {request.user} erstellt.\n\n"
                    f"Priorität: {ticket.get_priority_display()}\n"
                    f"Kategorie: {ticket.get_category_display()}\n\n"
                    f"{ticket.description}"
                ),
                recipients=admin_emails,
            )
            messages.success(request, f"Ticket #{ticket.pk} wurde erstellt.")
            return redirect(ticket.get_absolute_url())
    else:
        form = TicketCreateForm()
    return render(request, "tickets/ticket_form.html", {"form": form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related("created_by", "assigned_to"), pk=pk
    )
    if not request.user.is_staff and ticket.created_by_id != request.user.id:
        raise Http404()

    comment_form = CommentForm()
    attachment_form = AttachmentForm()
    admin_form = TicketAdminUpdateForm(instance=ticket) if request.user.is_staff else None
    worklog_form = WorkLogForm() if request.user.is_staff else None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "comment":
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                recipients = []
                if request.user.id != ticket.created_by_id and ticket.created_by.email:
                    recipients.append(ticket.created_by.email)
                if (
                    ticket.assigned_to
                    and request.user.id != ticket.assigned_to_id
                    and ticket.assigned_to.email
                ):
                    recipients.append(ticket.assigned_to.email)
                _notify(
                    subject=f"[Ticket #{ticket.pk}] Neuer Kommentar",
                    body=f"{request.user} hat kommentiert:\n\n{comment.body}",
                    recipients=recipients,
                )
                messages.success(request, "Kommentar hinzugefügt.")
                return redirect(ticket.get_absolute_url())

        elif action == "attach":
            attachment_form = AttachmentForm(request.POST, request.FILES)
            if attachment_form.is_valid():
                att = attachment_form.save(commit=False)
                att.ticket = ticket
                att.uploaded_by = request.user
                att.save()
                messages.success(request, "Anhang hinzugefügt.")
                return redirect(ticket.get_absolute_url())

        elif action == "worklog_add" and request.user.is_staff:
            worklog_form = WorkLogForm(request.POST)
            if worklog_form.is_valid():
                wl = worklog_form.save(commit=False)
                wl.ticket = ticket
                wl.performed_by = request.user
                wl.save()
                messages.success(request, "Aufwand erfasst.")
                return redirect(ticket.get_absolute_url())

        elif action == "worklog_delete" and request.user.is_staff:
            wl_id = request.POST.get("worklog_id")
            WorkLog.objects.filter(pk=wl_id, ticket=ticket).delete()
            messages.success(request, "Aufwand gelöscht.")
            return redirect(ticket.get_absolute_url())

        elif action == "update" and request.user.is_staff:
            admin_form = TicketAdminUpdateForm(request.POST, instance=ticket)
            if admin_form.is_valid():
                old_status = ticket.status
                updated = admin_form.save()
                if updated.status != old_status and ticket.created_by.email:
                    _notify(
                        subject=f"[Ticket #{ticket.pk}] Status: {updated.get_status_display()}",
                        body=(
                            f"Der Status deines Tickets wurde auf "
                            f"'{updated.get_status_display()}' geändert."
                        ),
                        recipients=[ticket.created_by.email],
                    )
                messages.success(request, "Ticket aktualisiert.")
                return redirect(ticket.get_absolute_url())
        else:
            return HttpResponseForbidden()

    worklogs = ticket.worklogs.select_related("performed_by").all() if request.user.is_staff else []
    totals = ticket.worklogs.aggregate(km=Sum("travel_km"), hours=Sum("hours")) if request.user.is_staff else {}

    return render(
        request,
        "tickets/ticket_detail.html",
        {
            "ticket": ticket,
            "comment_form": comment_form,
            "attachment_form": attachment_form,
            "admin_form": admin_form,
            "worklog_form": worklog_form,
            "worklogs": worklogs,
            "worklog_totals": totals,
        },
    )
