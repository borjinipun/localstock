from django.contrib import admin

from .models import City, Consent

admin.site.register(
    City,
    list_display=("code", "name", "is_live"),
)
admin.site.register(Consent, list_display=("phone", "scope", "given_at"))
