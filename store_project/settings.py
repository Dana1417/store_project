from pathlib import Path
import os

# 📁 المسار الرئيسي للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔐 إعدادات الأمان
SECRET_KEY = 'django-insecure-ak4jifds7)fnqygkogylaybbfn!(@47-!j!aozy54+2q##!89$'
DEBUG = True
ALLOWED_HOSTS = []  # ← أضف host مثل ['yourdomain.com'] في حالة الإنتاج

# 📦 التطبيقات المثبتة
INSTALLED_APPS = [
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
]

# 🧩 الوسطاء (Middleware)
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

# 🛣️ ملف روابط المشروع
ROOT_URLCONF = 'store_project.urls'

# 🧠 إعدادات القوالب
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ← مجلد القوالب العام
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

# 🔁 إعداد WSGI
WSGI_APPLICATION = 'store_project.wsgi.application'

# 🗄️ قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔐 تحقق من كلمات المرور
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

# 🌐 مسارات ملفات الترجمة
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# 📁 إعداد الملفات الثابتة (Static Files)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']         # ← ملفات التطوير
STATIC_ROOT = BASE_DIR / 'staticfiles'           # ← لتجميعها باستخدام collectstatic

# 📸 إعداد ملفات media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 🔑 إعداد المفتاح الأساسي الافتراضي
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
