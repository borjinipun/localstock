from django.urls import path

from . import views

urlpatterns = [
    path("shops/<int:pk>", views.shop_detail, name="shop-detail"),
    path("shops/<int:pk>/availability", views.shop_availability_history, name="shop-avail"),
    path("shop/claim/lookup", views.claim_lookup, name="claim-lookup"),
    path("shop/claim/verify", views.claim_verify, name="claim-verify"),
    path("me/shop", views.me_shop, name="me-shop"),
    path("me/shop/catalog", views.shop_catalog, name="shop-catalog"),
    path("me/shop/catalog/import", views.shop_catalog_import, name="shop-catalog-import"),
    path("me/shop/inquiries", views.shop_inquiries, name="shop-inquiries"),
    path("me/shop/inquiries/<int:tid>/reply", views.shop_inquiry_reply, name="shop-inquiry-reply"),
]
