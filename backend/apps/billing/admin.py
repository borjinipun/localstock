from django.contrib import admin

from .models import Payment, Plan, Subscription

admin.site.register(Plan, list_display=("code", "name", "monthly_paise", "checks_month"))
admin.site.register(Subscription, list_display=("shop", "plan_code", "status", "period_end"))
admin.site.register(Payment, list_display=("invoice_no", "amount_paise", "status", "paid_at"))
