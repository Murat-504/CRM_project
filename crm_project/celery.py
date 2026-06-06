import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings.development')

app = Celery('crm_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# ─── Периодические задачи ─────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Ежедневная проверка дедлайнов в 08:00
    'check-deadlines-daily': {
        'task': 'apps.tasks.tasks.check_upcoming_deadlines',
        'schedule': crontab(hour=8, minute=0),
    },
    # Еженедельный дайджест по понедельникам в 09:00
    'weekly-digest': {
        'task': 'apps.tasks.tasks.send_weekly_digest',
        'schedule': crontab(hour=9, minute=0, day_of_week='monday'),
    },
}
