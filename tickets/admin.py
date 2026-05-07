from django.contrib import admin

from .models import Attachment, Comment, Ticket


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ("uploaded_by", "uploaded_at")


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("author", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "category", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "priority", "category", "assigned_to")
    search_fields = ("title", "description", "created_by__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [CommentInline, AttachmentInline]
    autocomplete_fields = ("created_by", "assigned_to")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "author", "created_at")
    search_fields = ("body",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("ticket", "file", "uploaded_by", "uploaded_at")
