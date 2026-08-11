from pathlib import Path
import os
import sys
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

IS_TEST = 'test' in sys.argv
IS_PRODUCTION = os.environ.get('RENDER', '').lower() == 'true' or os.environ.get('APP_ENV') == 'production'


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


DEBUG = env_bool('DEBUG', False)
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise ImproperlyConfigured('SECRET_KEY must be set in production.')
    SECRET_KEY = 'development-only-7q!N3x#K9v@P2m$R8w%T5y&U1i*O4p-L6s'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        'ALLOWED_HOSTS',
        'sspa400-public.onrender.com,localhost,127.0.0.1,testserver',
    ).split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        'https://sspa400-public.onrender.com',
    ).split(',')
    if origin.strip()
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/learning/'
LOGOUT_REDIRECT_URL = '/'

# Firebase web SDK config – set these on Render as env vars.
# Get them from Firebase console → Project settings → Your apps → SDK setup.
FIREBASE_WEB_CONFIG = {
    'apiKey':            os.environ.get('FIREBASE_API_KEY',      ''),
    'authDomain':        os.environ.get('FIREBASE_AUTH_DOMAIN',  ''),
    'projectId':         os.environ.get('FIREBASE_PROJECT_ID',   ''),
    'storageBucket':     os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
    'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
    'appId':             os.environ.get('FIREBASE_APP_ID',       ''),
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'lms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=IS_PRODUCTION,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Ulaanbaatar'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication email. Configure SMTP_* on Render for password reset delivery.
if os.environ.get('SMTP_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ['SMTP_HOST']
    EMAIL_PORT = int(os.environ.get('SMTP_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    EMAIL_USE_TLS = env_bool('SMTP_USE_TLS', True)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'SSPA400 LMS <noreply@sspa400.mn>')

# Render terminates TLS before forwarding to Django.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # JavaScript progress endpoints read this token.
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = IS_PRODUCTION
CSRF_COOKIE_SECURE = IS_PRODUCTION
SECURE_SSL_REDIRECT = IS_PRODUCTION
SECURE_HSTS_SECONDS = 31536000 if IS_PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PRODUCTION
SECURE_HSTS_PRELOAD = IS_PRODUCTION
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'
PASSWORD_RESET_TIMEOUT = 60 * 60 * 2
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
_staticfiles_backend = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if IS_TEST or not IS_PRODUCTION
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _staticfiles_backend},
}
