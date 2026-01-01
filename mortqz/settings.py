from pathlib import Path
import os
from dotenv import load_dotenv

# ======================================================
# Base & ENV
# ======================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return default if val is None else val


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [
    h.strip()
    for h in env("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

# ======================================================
# Applications
# ======================================================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Cloudinary
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
    "django.contrib.sessions.middleware.SessionMiddleware",

    # مهم للعربية + الترجمة
    "django.middleware.locale.LocaleMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mortqz.urls"

# ======================================================
# Templates
# ======================================================
# ✅ هذا هو المفتاح اللي يخلي Django يرى:
# templates/admin/base_site.html
# templates/admin/index.html
# templates/admin/nav_sidebar.html
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                # لازم للـ admin + request داخل القوالب
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mortqz.wsgi.application"

# ======================================================
# Database
# ======================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ======================================================
# Password validation
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

# (اختياري) لو عندك ملفات ترجمة مخصصة
LOCALE_PATHS = [BASE_DIR / "locale"]

# ======================================================
# Django Admin UX
# ======================================================
# ✅ خلي السايدبار مفعل (حتى لو عدلته بقالبك)
# في أغلب الإصدارات الحديثة هذا افتراضيًا True، لكن نثبته لعدم المفاجآت.
ADMIN_ENABLE_NAV_SIDEBAR = True

# ======================================================
# Static files
# ======================================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ======================================================
# Cloudinary (Media Storage)
# ======================================================
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": env("CLOUDINARY_API_KEY"),
    "API_SECRET": env("CLOUDINARY_API_SECRET"),
}

# ⚠️ هذا السطر إلزامي لمكتبة django-cloudinary-storage
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# ✅ متوافق مع Django 6 (حتى لو بعض المكتبات لا تستخدمه)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Media (لن تُستخدم فعليًا بعد Cloudinary، لكن نُبقيها للتوافق)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ======================================================
# Security (development-safe)
# ======================================================
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# ✅ في التطوير لا نجبر https، في الإنتاج تقدر تفعّله عبر env
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)

# ✅ منع إعادة توجيه https بالغلط (مهم إذا كان عندك مشاكل تحويل للـ https محليًا)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)

# لو كنت خلف Proxy/Load Balancer في الإنتاج فعّل هذا من env
# مثال: DJANGO_SECURE_PROXY_SSL_HEADER=1
if env_bool("DJANGO_SECURE_PROXY_SSL_HEADER", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# (اختياري) للإنتاج: أضف نطاقك في env مثل:
# DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
_csrf_trusted = [x.strip() for x in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = _csrf_trusted

# ======================================================
# Defaults
# ======================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
