from .settings import *
import os

# Production settings
DEBUG = False

# Set allowed hosts from environment variable
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# Get SQLite path from environment or use default
SQLITE_PATH = os.environ.get('SQLITE_PATH', BASE_DIR)

# Ensure directories exist
import os
os.makedirs(os.path.join(SQLITE_PATH, 'media'), exist_ok=True)

# Register maintenance middleware for production
MIDDLEWARE = ['detector.middleware.MaintenanceMiddleware'] + MIDDLEWARE

# Database settings - Use SQLite with persistent storage on Render
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(SQLITE_PATH, 'db.sqlite3'),
    }
}

# Use local memory cache if Redis is not configured
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'realface-prod-cache',
    }
}

# Memory optimization for limited environments like Render's free tier
import sys
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(SQLITE_PATH, 'media')

# Logging - Use console logging for Render
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'detector': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}