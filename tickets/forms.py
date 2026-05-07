from django import forms
from django.contrib.auth import get_user_model

from .models import Attachment, Comment, Ticket, WorkLog

User = get_user_model()


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"multiple": True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


class TicketCreateForm(forms.ModelForm):
    attachments = MultipleFileField(label="Anhänge", required=False)

    class Meta:
        model = Ticket
        fields = ["title", "description", "priority", "category"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }


class TicketAdminUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status", "priority", "category", "assigned_to"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_staff=True).order_by("username")
        self.fields["assigned_to"].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Kommentar schreiben..."})}
        labels = {"body": ""}


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["file"]


class WorkLogForm(forms.ModelForm):
    class Meta:
        model = WorkLog
        fields = ["date", "travel_km", "hours", "material", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "material": forms.Textarea(attrs={"rows": 2}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }
