"""Django settings — LocalStock MVP (spec: docs/08 §2, docs/05 NFRs)."""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def _get(key, default=None):
    return os.environ.get(key, default)


SECRET_KEY = _get("SECRET_KEY", "dev-insecure-change-me")
DEBUG = _get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h for h in _get("ALLOWED_HOSTS", "*").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    # apps
    "apps.core",
    "apps.catalog",
    "apps.shops",
    "apps.queries",
    "apps.verification",
    "apps.billing",
    "apps.ops",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {
    "default": dj_database_url.config(
        default=_get("DATABASE_URL", "sqlite:///./db.sqlite3"), conn_max_age=600
    )
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {"TITLE": "LocalStock API", "VERSION": "v1"}

# CORS wide-open in dev/demo. In prod: explicit ALLOWED_ORIGINS env (docs NFR-S6).
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = _get("CORS_ALLOWED_ORIGINS", "").split(",")

# ---------------------------------------------------------------- celery
REDIS_URL = _get("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_TIME_LIMIT = 90
CELERY_BEAT_SCHEDULE = {
    "staleness-sweep": {
        "task": "apps.queries.tasks.staleness_sweep",
        "schedule": 3600.0,
    },
    "recompute-accuracy": {
        "task": "apps.verification.tasks.recompute_accuracy",
        "schedule": 60 * 60 * 6.0,
    },
}
CELERY_TIMEZONE = "Asia/Kolkata"

# ------------------------------------------------- product engine constants
VOICESVC_URL = _get("VOICESVC_URL", "http://localhost:8001")
SERVICE_TOKEN = _get("SERVICE_TOKEN", "dev-service-token")
PROVIDER_TELEPHONY = _get("PROVIDER_TELEPHONY", "mock")
PROVIDER_WHATSAPP = _get("PROVIDER_WHATSAPP", "mock")
PROVIDER_PAYMENTS = _get("PROVIDER_PAYMENTS", "mock")

MAX_TARGETS_PER_WAVE = int(_get("MAX_TARGETS_PER_WAVE", "6"))        # docs 02 F-M-02
SPOT_CHECK_EXTRA = int(_get("SPOT_CHECK_EXTRA", "5"))                # docs 02 F-C-03
QUERY_BUDGET_PAISE = int(_get("QUERY_BUDGET_PAISE", "2500"))         # docs 03 §7
FRESH_CATALOG_HOURS = int(_get("FRESH_CATALOG_HOURS", "48"))         # docs 03 §2
REUSE_WINDOW_MINUTES = int(_get("REUSE_WINDOW_MINUTES", "30"))       # docs 02 F-M-03
MAX_SHOP_CHECKS_PER_DAY = int(_get("MAX_SHOP_CHECKS_PER_DAY", "8"))  # docs 03 §7

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
