from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Ticket, WorkLog

User = get_user_model()


class TicketSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", "alice@example.com", "pw-alice-123!")
        self.other = User.objects.create_user("bob", "bob@example.com", "pw-bob-123!")
        self.admin = User.objects.create_user("admin", "admin@example.com", "pw-admin-123!", is_staff=True)

    def login(self, username, password="pw-alice-123!"):
        self.client.login(username=username, password=password)

    def test_login_required(self):
        resp = self.client.get(reverse("ticket_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_user_can_create_ticket(self):
        self.login("alice")
        resp = self.client.post(
            reverse("ticket_create"),
            {"title": "Drucker geht nicht", "description": "Fehler 5", "priority": "high", "category": "hardware"},
        )
        self.assertEqual(resp.status_code, 302)
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.created_by, self.user)
        self.assertEqual(ticket.status, "open")

    def test_user_only_sees_own_tickets(self):
        Ticket.objects.create(title="A", description="x", created_by=self.user)
        Ticket.objects.create(title="B", description="x", created_by=self.other)
        self.login("alice")
        resp = self.client.get(reverse("ticket_list"))
        self.assertContains(resp, "A")
        self.assertNotContains(resp, ">B<")

    def test_admin_sees_all_tickets(self):
        Ticket.objects.create(title="UserTicket", description="x", created_by=self.user)
        self.login("admin", "pw-admin-123!")
        resp = self.client.get(reverse("ticket_list"))
        self.assertContains(resp, "UserTicket")

    def test_user_cannot_view_others_ticket(self):
        t = Ticket.objects.create(title="Secret", description="x", created_by=self.other)
        self.login("alice")
        resp = self.client.get(t.get_absolute_url())
        self.assertEqual(resp.status_code, 404)

    def test_admin_can_change_status(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("admin", "pw-admin-123!")
        resp = self.client.post(
            t.get_absolute_url(),
            {
                "action": "update",
                "status": "in_progress",
                "priority": "medium",
                "category": "other",
                "assigned_to": self.admin.pk,
            },
        )
        self.assertEqual(resp.status_code, 302)
        t.refresh_from_db()
        self.assertEqual(t.status, "in_progress")
        self.assertEqual(t.assigned_to, self.admin)

    def test_user_cannot_update_ticket(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("alice")
        resp = self.client.post(
            t.get_absolute_url(),
            {"action": "update", "status": "closed", "priority": "low", "category": "other"},
        )
        self.assertEqual(resp.status_code, 403)
        t.refresh_from_db()
        self.assertEqual(t.status, "open")

    def test_admin_can_add_worklog(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("admin", "pw-admin-123!")
        resp = self.client.post(
            t.get_absolute_url(),
            {
                "action": "worklog_add",
                "date": "2026-05-07",
                "travel_km": "12.5",
                "hours": "1.5",
                "material": "1x Netzteil",
                "description": "Tausch",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(WorkLog.objects.count(), 1)
        wl = WorkLog.objects.get()
        self.assertEqual(wl.performed_by, self.admin)
        self.assertEqual(str(wl.travel_km), "12.5")

    def test_user_cannot_add_worklog(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("alice")
        resp = self.client.post(
            t.get_absolute_url(),
            {"action": "worklog_add", "date": "2026-05-07", "travel_km": "1", "hours": "1"},
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(WorkLog.objects.count(), 0)

    def test_admin_can_close_ticket(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("admin", "pw-admin-123!")
        resp = self.client.post(reverse("ticket_close", args=[t.pk]))
        self.assertEqual(resp.status_code, 302)
        t.refresh_from_db()
        self.assertEqual(t.status, "closed")

    def test_user_cannot_close_ticket(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("alice")
        resp = self.client.post(reverse("ticket_close", args=[t.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_archive_only_closed(self):
        Ticket.objects.create(title="Open1", description="x", created_by=self.user, status="open")
        Ticket.objects.create(title="Closed1", description="x", created_by=self.user, status="closed")
        self.login("alice")
        resp = self.client.get(reverse("ticket_list"))
        self.assertContains(resp, "Open1")
        self.assertNotContains(resp, "Closed1")
        resp = self.client.get(reverse("ticket_archive"))
        self.assertContains(resp, "Closed1")
        self.assertNotContains(resp, "Open1")

    def test_comments(self):
        t = Ticket.objects.create(title="X", description="x", created_by=self.user)
        self.login("alice")
        resp = self.client.post(t.get_absolute_url(), {"action": "comment", "body": "Hallo"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)
