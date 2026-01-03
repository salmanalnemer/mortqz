"""
Django settings for mortqz project
Compatible with Django 6.x
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# ======================================================
# Base & ENV
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


def env(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return default if val is None else val


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


# ======================================================
# Core
# ======================================================
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env_bool("DJANGO_DEBUG", True)
DJANGO_ENV = env("DJANGO_ENV", "development")

ALLOWED_HOSTS = [
    h.strip()
    for h in env(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,mortqz.onrender.com",
    ).split(",")
    if h.strip()
]

ROOT_URLCONF = "mortqz.urls"
WSGI_APPLICATION = "mortqz.wsgi.application"

# ======================================================
# Applications
# ======================================================
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Storage
    "cloudinary",
    "cloudinary_storage",

    # Project apps
    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "orders.apps.OrdersConfig",
]

# ======================================================
# Middleware
# ======================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # ⚠️ WhiteNoise MUST be immediately after SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ======================================================
# Templates
# ======================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ======================================================
# Database (Auto Environment Switch)
# ======================================================
if DJANGO_ENV == "production":
    DATABASES = {
        "default": {
            "ENGINE": env("PROD_DB_ENGINE"),
            "HOST": env("PROD_DB_HOST"),
            "PORT": env("PROD_DB_PORT"),
            "NAME": env("PROD_DB_NAME"),
            "USER": env("PROD_DB_USER"),
            "PASSWORD": env("PROD_DB_PASSWORD"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "sslmode": "prefer",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": env("DEV_DB_ENGINE", "django.db.backends.sqlite3"),
            "NAME": BASE_DIR / env("DEV_DB_NAME", "db.sqlite3"),
        }
    }

# ======================================================
# Password Validation
# ======================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ======================================================
# Localization
# ======================================================
LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("ar", "العربية"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# ======================================================
# Static & Media
# ======================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ======================================================
# Static files handling (WhiteNoise)
# ======================================================
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# ======================================================
# Cloudinary (Media only)
# ======================================================
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": env("CLOUDINARY_API_KEY"),
    "API_SECRET": env("CLOUDINARY_API_SECRET"),
}

DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
)

# ⚠️ لا نستخدم STORAGES هنا حتى لا نكسر WhiteNoise
# Django سيستخدم STATICFILES_STORAGE تلقائياً

# ======================================================
# Security
# ======================================================
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = env_bool(
    "DJANGO_CSRF_COOKIE_SECURE", not DEBUG
)
SESSION_COOKIE_SECURE = env_bool(
    "DJANGO_SESSION_COOKIE_SECURE", not DEBUG
)
SECURE_SSL_REDIRECT = env_bool(
    "DJANGO_SECURE_SSL_REDIRECT", False
)

if env_bool("DJANGO_SECURE_PROXY_SSL_HEADER", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

_csrf_trusted = [
    x.strip()
    for x in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if x.strip()
]
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = _csrf_trusted

# ======================================================
# Admin & Defaults
# ======================================================
ADMIN_ENABLE_NAV_SIDEBAR = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
