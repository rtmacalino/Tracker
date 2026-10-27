"""Settings for the Tracker Django application."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _required_env(name):
    """Return a required environment variable without exposing its value."""
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"{name} is not set. Load the Tracker environment before starting Django."
        )
    return value


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {
        "1", "true", "yes", "on"
    }


SECRET_KEY = _required_env("DJANGO_SECRET_KEY")
DEBUG = _env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "10.10.10.124,localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS", "http://10.10.10.124"
    ).split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "inventory",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tracker.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tracker.wsgi.application"
ASGI_APPLICATION = "tracker.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("TRACKER_DB_NAME", "tracker"),
        "USER": os.environ.get("TRACKER_DB_USER", "tracker"),
        "PASSWORD": _required_env("TRACKER_DB_PASSWORD"),
        "HOST": os.environ.get("TRACKER_DB_HOST", "10.10.10.137"),
        "PORT": os.environ.get("TRACKER_DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("TRACKER_DB_CONN_MAX_AGE", "60")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Manila")
USE_I18N = True
USE_TZ = True

FORCE_SCRIPT_NAME = "/Tracker"
STATIC_URL = "/Tracker/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/Tracker/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/Tracker/accounts/login/"
LOGIN_REDIRECT_URL = "/Tracker/"
LOGOUT_REDIRECT_URL = "/Tracker/accounts/login/"

EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

# Enable secure cookies when HTTPS is configured. The current deployment URL is
# HTTP, so defaulting these flags on would prevent browsers from sending sessions.
# Set DJANGO_SECURE_COOKIES=1 after HTTPS is configured end-to-end.
SESSION_COOKIE_SECURE = _env_bool("DJANGO_SECURE_COOKIES", False)
CSRF_COOKIE_SECURE = _env_bool("DJANGO_SECURE_COOKIES", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
if not DEBUG:
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
