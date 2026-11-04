from django.urls import path

from . import views

urlpatterns = [
    path("internal/verification/update/", views.verification_update),
]
