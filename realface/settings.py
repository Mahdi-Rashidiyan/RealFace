"""
Django settings for realface project.
"""
from pathlib import Path
from detector.utils import secure_settings
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load secure settings
try:
    secure_config = secure_settings(BASE_DIR)
    SECRET_KEY = secure_config['SECRET_KEY']
    FERNET_KEY = secure_config['FERNET_KEY']
except:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-development-key')
    FERNET_KEY = os.environ.get('FERNET_KEY', 'development-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'detector',
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
    'csp.middleware.CSPMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
]

ROOT_URLCONF = 'realface.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'realface.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'realface-cache',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'detector' / 'static',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy with HTTPS
CSP_DEFAULT_SRC = ("'self'", "https:")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com")
CSP_SCRIPT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "blob:", "https:")
CSP_FONT_SRC = ("'self'", "https://cdnjs.cloudflare.com")
CSP_UPGRADE_INSECURE_REQUESTS = True

# Static and Media files with HTTPS
STATIC_URL = 'https://' + ALLOWED_HOSTS[2] + '/static/' if not DEBUG else '/static/'
MEDIA_URL = 'https://' + ALLOWED_HOSTS[2] + '/media/' if not DEBUG else '/media/'

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Rate limiting settings
RATELIMIT_VIEW = 'detector.views.analyze_image'
RATELIMIT_KEY = 'ip'
RATELIMIT_RATE = '10/m'
RATELIMIT_BLOCK = True
RATELIMIT_USE_CACHE = 'default'

# Image cleanup settings
IMAGE_CLEANUP = {
    'MAX_AGE_DAYS': 7,
    'ANALYZED_ONLY': True,
}

# Maximum upload file size (10MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'task': {
            'format': '{asctime} - {levelname}: {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'formatter': 'verbose',
        },
        'tasks': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'tasks.log',
            'formatter': 'task',
        },
        'backup': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'backup.log',
            'formatter': 'task',
        },
        'cleanup': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'cleanup.log',
            'formatter': 'task',
        },
        'security': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'detector': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'detector.tasks': {
            'handlers': ['tasks', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'detector.tasks.backup': {
            'handlers': ['backup', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'detector.tasks.cleanup': {
            'handlers': ['cleanup', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'detector.security': {
            'handlers': ['security', 'console'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}

# Allowed image formats
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'WEBP']
