from django.contrib import admin

from .models import Attachment, Comment, Ticket, WorkLog


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("uploaded_by", "uploaded_at")


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("author", "created_at")


class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 0
    readonly_fields = ("performed_by", "created_at")
    fields = ("date", "travel_km", "hours", "material", "description", "performed_by", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "category", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "priority", "category", "assigned_to")
    search_fields = ("title", "description", "created_by__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CommentInline, AttachmentInline, WorkLogInline]
    autocomplete_fields = ("created_by", "assigned_to")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("body",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "file", "uploaded_by", "uploaded_at")


@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ("ticket", "date", "performed_by", "travel_km", "hours")
    list_filter = ("date", "performed_by")
    search_fields = ("ticket__title", "material", "description")
    date_hierarchy = "date"
