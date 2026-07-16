"""
Django settings for single_store_ecommerce project.
Production-ready configuration using environment variables.
"""

from pathlib import Path
from decouple import config, Csv
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# =============================================================
# CORE SECURITY SETTINGS
# =============================================================

SECRET_KEY = config('SECRET_KEY', default='django-insecure-z0q%i9^_@hdh*-=fxy4v8!w((w24e+*1d1(iwdtfooyr6d7bqt')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())


# =============================================================
# APPLICATION DEFINITION
# =============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'cloudinary',
    'cloudinary_storage',
    # Local apps
    'store',
    'accounts',
    'orders',
    'cart',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must be right after SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'single_store_ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Custom context processors
                'store.context_processors.site_settings',
                'cart.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'single_store_ecommerce.wsgi.application'


# =============================================================
# DATABASE — Neon PostgreSQL (via DATABASE_URL env var)
# Falls back to SQLite for local dev if DATABASE_URL not set.
# =============================================================

DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# =============================================================
# PASSWORD VALIDATION
# =============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =============================================================
# INTERNATIONALIZATION
# =============================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True


# =============================================================
# STATIC FILES — Served by WhiteNoise in production
# =============================================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# =============================================================
# MEDIA FILES — Stored in Cloudinary in production
# =============================================================

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY':    config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

# Always define MEDIA_URL and MEDIA_ROOT
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================
# STORAGE BACKENDS — Django 4.2+ / 6.x syntax (STORAGES dict)
# DEFAULT_FILE_STORAGE and STATICFILES_STORAGE were removed in
# Django 5.1+. The STORAGES dict is the only supported way.
# =============================================================

_media_backend = (
    'cloudinary_storage.storage.MediaCloudinaryStorage'
    if config('CLOUDINARY_CLOUD_NAME', default='')
    else 'django.core.files.storage.FileSystemStorage'
)

STORAGES = {
    # Media files: Cloudinary when credentials present, local otherwise
    'default': {
        'BACKEND': _media_backend,
    },
    # Static files: WhiteNoise for efficient production serving
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}


# =============================================================
# DEFAULT PRIMARY KEY FIELD TYPE
# =============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================
# AUTHENTICATION
# =============================================================

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# =============================================================
# STRIPE PAYMENT SETTINGS
# =============================================================

STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY     = config('STRIPE_SECRET_KEY',      default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET',  default='')



# =============================================================
# EMAIL SETTINGS
# =============================================================

EMAIL_BACKEND  = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = 'noreply@solostore.com'


# =============================================================
# PRODUCTION SECURITY SETTINGS (only active when DEBUG=False)
# =============================================================

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000          # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
