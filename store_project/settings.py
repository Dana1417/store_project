from pathlib import Path
import os

# 📁 المسار الرئيسي للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 إعدادات الأمان
SECRET_KEY = 'django-insecure-ak4jifds7)fnqygkogylaybbfn!(@47-!j!aozy54+2q##!89$'
DEBUG = True
ALLOWED_HOSTS = []  # ← أضف ['yourdomain.com'] في حالة الإنتاج

# 📦 التطبيقات المثبتة
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # ✅ التطبيقات الخاصة بالمشروع
    'core',
    'store',
    'orders',
]

# 🧩 الوسطاء (Middleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # لدعم الترجمة
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 🛣️ ملف الروابط الرئيسي
ROOT_URLCONF = 'store_project.urls'

# 🧠 إعدادات القوالب (Templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # مجلد القوالب العام
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

# 🔁 WSGI
WSGI_APPLICATION = 'store_project.wsgi.application'

# 🗄️ إعدادات قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔐 التحقق من كلمات المرور
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🌍 اللغة والتوقيت
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# 🌐 ملفات الترجمة (اختياري)
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# 📁 إعدادات الملفات الثابتة (Static files)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']       # ملفات التطوير
STATIC_ROOT = BASE_DIR / 'staticfiles'         # لتجميع الملفات

# 📸 إعدادات ملفات الميديا (الصور والفيديو)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 🔑 إعداد المفتاح الافتراضي للنماذج
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
