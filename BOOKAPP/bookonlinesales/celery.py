import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookonlinesales.settings")

app = Celery("bookonlinesales")

# Load settings from Django settings.py, using namespace CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all registered apps
app.autodiscover_tasks()

# Optional: default queue, timezone, etc.
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
)
