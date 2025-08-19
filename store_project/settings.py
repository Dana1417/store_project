# store_project/settings.py
from pathlib import Path
import os
from dotenv import load_dotenv

# =========================
#        تحميل المتغيرات
# =========================
load_dotenv()

# 📁 المسار الرئيسي
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================
#     أدوات قراءة env
# =========================
def env_str(key: str, default: str = "") -> str:
    val = os.getenv(key)
    return default if val is None else val

def env_bool(key: str, default: bool = False) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}

def env_int(key: str, default: int) -> int:
    val = os.getenv(key)
    try:
        return int(val) if val is not None else default
    except ValueError:
        return default

def env_list(key: str, default: list[str] | None = None, sep: str = ",") -> list[str]:
    s = os.getenv(key)
    if not s:
        return default or []
    return [x.strip() for x in s.split(sep) if x.strip()]

# =========================
#         الأمان
# =========================
SECRET_KEY = env_str("SECRET_KEY", "django-insecure-key")
DEBUG = env_bool("DEBUG", True)

# 🖇️ المضيفون المسموحون
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["127.0.0.1", "localhost"])

# دعم Render: إضافة اسم المضيف الخارجي تلقائيًا إن وُجد
_render_host = env_str("RENDER_EXTERNAL_HOSTNAME", "")
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

# ✅ CSRF Trusted Origins
# مثال في .env:
# CSRF_TRUSTED_ORIGINS="https://store-project-xxxx.onrender.com,https://*.onrender.com"
_env_csrf = env_list("CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _env_csrf if _env_csrf else ["https://*.onrender.com"]

# =========================
#        التطبيقات
# =========================
INSTALLED_APPS = [
    # تطبيقاتك
    "core",   # ← يأتي أولًا إذا كان لديك AUTH_USER_MODEL مُخصص
    "store",
    "orders.apps.OrdersConfig",   # ✅ لتفعيل signals
    "cart",
    "students.apps.StudentsConfig",
    "teachers.apps.TeachersConfig",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # طرف ثالث
    "cloudinary",
    "cloudinary_storage",
    "crispy_forms",
    "crispy_bootstrap5",
]

# =========================
#         الوسطاء
# =========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise لخدمة الملفات الثابتة بكفاءة (خصوصًا في الإنتاج)
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =========================
#        القوالب والـ URLs
# =========================
ROOT_URLCONF = "store_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # مجلد القوالب الرئيسي للمشروع
        "DIRS": [BASE_DIR / "templates"],
        # تمكين التحميل من templates داخل التطبيقات
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # أثناء التطوير، اجعلي التنبيه على المتغيرات غير الموجودة أوضح
            **({"string_if_invalid": "[INVALID: %s]"} if DEBUG else {}),
        },
    },
]

WSGI_APPLICATION = "store_project.wsgi.application"

# =========================
#        قاعدة البيانات
# =========================
# - في التطوير: SQLite (بلا ضبط إضافي)
# - في الإنتاج: PostgreSQL عبر متغيرات البيئة (Render)
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": env_str("DB_HOST"),
            "PORT": env_str("DB_PORT", "5432"),
            "NAME": env_str("DB_NAME"),
            "USER": env_str("DB_USER"),
            "PASSWORD": env_str("DB_PASSWORD"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),  # اتصالات دائمة محسّنة
            "OPTIONS": {
                "connect_timeout": env_int("DB_CONNECT_TIMEOUT", 10),
            },
        }
    }

# =========================
#     اللغة والتوقيت
# =========================
LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Riyadh"
USE_I18N = True
USE_TZ = True

# =========================
#    Static & Media files
# =========================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# مجلد static اختياري للمشروع (بالإضافة إلى static داخل التطبيقات)
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Django 5: STORAGES بدل STATICFILES_STORAGE/DEFAULT_FILE_STORAGE
if DEBUG:
    STORAGES = {
        "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# Cloudinary
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env_str("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": env_str("CLOUDINARY_API_KEY", ""),
    "API_SECRET": env_str("CLOUDINARY_API_SECRET", ""),
}
MEDIA_URL = "/media/"

# WhiteNoise: إعدادات مفيدة أثناء التطوير
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG

# =========================
#        البريد الإلكتروني
# =========================
EMAIL_BACKEND = env_str("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env_str("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@example.com")

# =========================
#   نموذج المستخدم المخصص
# =========================
AUTH_USER_MODEL = "core.CustomUser"

# =========================
#  سياسة كلمات المرور
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =========================
#       تسجيل الأخطاء
# =========================
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        # أخطاء الطلبات تُظهر في الكونسول بشكل أنظف
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}

# =========================
#     عناوين تسجيل الدخول
# =========================
LOGIN_URL = env_str("LOGIN_URL", "login")
LOGIN_REDIRECT_URL = env_str("LOGIN_REDIRECT_URL", "/")
LOGOUT_REDIRECT_URL = env_str("LOGOUT_REDIRECT_URL", "/")

# =========================
#     الحقول/الإعدادات
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# =========================
#   رفع الملفات والذاكرة
# =========================
FILE_UPLOAD_MAX_MEMORY_SIZE = env_int("FILE_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024)   # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = env_int("DATA_UPLOAD_MAX_MEMORY_SIZE", 20 * 1024 * 1024)  # 20MB

# =========================
#  إعدادات أمان في الإنتاج
# =========================
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 60 * 60 * 24 * 30)  # 30 يوم
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)

    # سياسات أخرى
    SECURE_REFERRER_POLICY = env_str("SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
    X_FRAME_OPTIONS = env_str("X_FRAME_OPTIONS", "DENY")
    SECURE_CONTENT_TYPE_NOSNIFF = True
