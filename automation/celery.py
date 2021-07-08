import os

from celery import Celery

# set the default django project settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automation.settings.dev')

app = Celery('automation',)

# celery will apply all configuration keys with defined namespace, in this case it was CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# load tasks from all discover apps
app.autodiscover_tasks()

