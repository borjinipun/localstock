from django.urls import path

from . import views

urlpatterns = [
    path("shop/plans", views.plans_list),
    path("shop/subscription", views.subscription_endpoint),
]
