from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("PROD_DEBUG")

ALLOWED_HOSTS = config("PROD_ALLOWED_HOST")

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

