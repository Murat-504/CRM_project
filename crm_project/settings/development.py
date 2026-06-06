from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Celery — без Redis в dev используем синхронный режим
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'

CORS_ALLOW_ALL_ORIGINS = True
