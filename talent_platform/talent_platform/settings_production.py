import os
from .settings import *
from dotenv import load_dotenv

load_dotenv()

# Security Settings
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'talent_platform',
        'USER': 'talent_user',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')

# Static Files
STATIC_ROOT = os.getenv('STATIC_ROOT', '/home/yourusername/talent-platform/staticfiles')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/home/yourusername/talent-platform/media')

# Security Settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = os.getenv('SECURE_BROWSER_XSS_FILTER', 'True').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

# Additional Security Headers
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/yourusername/talent-platform/logs/django.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'mail_admins', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'profiles': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'payments': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Admin Email Configuration
ADMINS = [
    ('Admin Name', os.getenv('ADMIN_EMAIL', 'admin@yourdomain.com')),
]

# Create logs directory
import os
logs_dir = '/home/yourusername/talent-platform/logs'
os.makedirs(logs_dir, exist_ok=True)

# Cache Configuration (Database-based for Railway compatibility)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

# Session Configuration (Database-based)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Rate Limiting (more restrictive for production)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/hour',           # Reduced for production
        'user': '200/hour',          # Reduced for production
        'talent_user': '300/hour',   # Reduced for production
        'background_user': '300/hour', # Reduced for production
        'dashboard_user': '500/hour', # Reduced for production
        'admin_dashboard_user': '2000/hour', # Reduced for production
        'payment_endpoints': '30/hour', # Reduced for production
        'restricted_country': '50/hour', # Reduced for production
    }
}

# JWT settings (shorter tokens for production)
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),  # Shorter for security
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=12),   # Shorter for security
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# Stripe Configuration (Production keys)
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Stripe Price IDs
STRIPE_PRICE_IDS = {
    'silver': os.getenv('STRIPE_PRICE_SILVER'),
    'gold': os.getenv('STRIPE_PRICE_GOLD'),
    'platinum': os.getenv('STRIPE_PRICE_PLATINUM'),
    'back_ground_jobs': os.getenv('STRIPE_PRICE_BACKGROUND_JOBS'),
}

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Media Files Configuration
MEDIA_URL = '/media/'
STATIC_URL = '/static/'

# Disable Django Debug Toolbar in production
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')

# Remove debug middleware in production
if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

# Performance optimizations
CONN_MAX_AGE = 60  # Database connection pooling 