from pathlib import Path
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api

# 🔐 تحميل المتغيرات من ملف .env
load_dotenv()

# 📁 المسار الرئيسي للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 إعدادات الأمان
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-key")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = (
    os.getenv("ALLOWED_HOSTS", "").split(",") if not DEBUG else []
)

# 📦 التطبيقات المثبتة
INSTALLED_APPS = [
    # تطبيقات Django الافتراضية
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ✅ تطبيقات المشروع
    'core',
    'store',
    'orders',

    # 🖼️ تطبيقات Cloudinary
    'cloudinary',
    'cloudinary_storage',
]

# 🧩 الوسيطات (Middlewares)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 🛣️ ملف المسارات الرئيسي
ROOT_URLCONF = 'store_project.urls'  # ← تأكد من اسم مشروعك هنا

# 📁 إعدادات القوالب
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 🧠 قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🌍 اللغة والتوقيت
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# 📦 إعدادات static
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 🖼️ إعدادات media عبر Cloudinary
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv("CLOUDINARY_CLOUD_NAME"),
    'API_KEY': os.getenv("CLOUDINARY_API_KEY"),
    'API_SECRET': os.getenv("CLOUDINARY_API_SECRET"),
}
MEDIA_URL = '/media/'  # لا تستخدم MEDIA_ROOT مع Cloudinary

# 📧 إعدادات البريد (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

# 🆔 الحقل الافتراضي
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
