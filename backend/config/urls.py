from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", lambda r: JsonResponse({"ok": True})),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/", include("apps.queries.urls")),
    path("api/v1/", include("apps.shops.urls")),
    path("api/v1/", include("apps.billing.urls")),
    path("api/", include("apps.verification.urls")),  # /api/internal/... (service-to-service)
]
