from django.urls import path

from . import views

urlpatterns = [
    path("queries", views.query_create),
    path("queries/<int:pk>", views.query_detail),
    path("queries/<int:pk>/events", views.query_events, name="query-events"),
    path("queries/<int:pk>/extend", views.query_extend),
    path("queries/<int:pk>/cancel", views.query_cancel),
    path("availability/<int:rid>/report", views.availability_report),
]
