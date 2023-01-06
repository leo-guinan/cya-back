"""
Django settings for backend project.

Generated by 'django-appadmin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path

import dj_database_url
from decouple import config
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', default='django-insecure-g%%6#-0b%*0qzp(lwsf1&5$ms-7a8flnycnv0-)yo4k1!bla09')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'RENDER' not in os.environ

ALLOWED_HOSTS = [
    '82e6-2603-6010-b000-ba40-00-1000.ngrok.io',
    'localhost',
]
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    ALLOWED_HOSTS.append('api.feathercrm.io')
    ALLOWED_HOSTS.append('app.whoshouldiunfollow.com')
    ALLOWED_HOSTS.append('tools.whoshouldiunfollow.com')
    ALLOWED_HOSTS.append('automations.buildinpublicuniversity.com')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django.contrib.sites',
    'unfollow',
    'watchtweet',
    "corsheaders",
    "rest_framework_api_key",
    'django_celery_beat',
    'django_celery_results',
    'client',
    'feather',
    'twitter',
    'mail',
    'crawler',
    'friendcontent',
    "appadmin",
    'gardens',
    'bookmarks',
    'webhooks',
    'followed',
    'open_ai',
    'enhancer',
    'marketing',
    'podcast_toolkit',
    'search'
]
SITE_ID = 2

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases


DATABASES = {
    'default': dj_database_url.config(
        # Feel free to alter this value to suit your needs.
        default='postgresql://postgres:@localhost:5432/postgres',
        conn_max_age=600
    )
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework_api_key.permissions.HasAPIKey",
    ]
}
SOCIALACCOUNT_STORE_TOKENS = True

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'

SENDGRID_API_KEY = config('SENDGRID_API_KEY')

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_HOST_USER = 'apikey'  # this is exactly the value 'apikey'
EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
EMAIL_PORT = 587
EMAIL_USE_TLS = True

STATIC_URL = '/static/'
# Following settings only make sense on production and may break development environments.
if not DEBUG:    # Tell Django to copy statics to the `staticfiles` directory
    # in your application directory on Render.
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Turn on WhiteNoise storage backend that takes care of compressing static files
    # and creating unique names for each version so they can safely be cached forever.
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
LOGLEVEL = os.environ.get('LOGLEVEL', 'info').upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
    # root logger
        '': {
            'level': 'WARNING',
            'handlers': ['console',],
        },
        'backend': {
            'level': LOGLEVEL,
            'handlers': ['console',],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'bookmarks': {
            'level': LOGLEVEL,
            'handlers': ['console',],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'client': {
            'level': LOGLEVEL,
            'handlers': ['console',],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'crawler': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'enhancer': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'feather': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'followed': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'friendcontent': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'gardens': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'mail': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'marketing': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'open_ai': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'podcast_toolkit': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'rss': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'transformer': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'twitter': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'twitter_api': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'unfollow': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'watchtweet': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },
        'webhooks': {
            'level': LOGLEVEL,
            'handlers': ['console', ],
            # required to avoid double logging with root logger
            'propagate': False,
        },

    },
}