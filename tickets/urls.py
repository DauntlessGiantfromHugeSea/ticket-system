from django.urls import path

from . import views

urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("archiv/", views.ticket_archive, name="ticket_archive"),
    path("neu/", views.ticket_create, name="ticket_create"),
    path("<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("<int:pk>/close/", views.ticket_close, name="ticket_close"),
    path("<int:pk>/reopen/", views.ticket_reopen, name="ticket_reopen"),
]
