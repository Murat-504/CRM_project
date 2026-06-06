from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta


@receiver(post_save, sender='requests_app.ClientRequest')
def schedule_deadline_reminder(sender, instance, created, **kwargs):
    """
    При создании или обновлении заявки с дедлайном —
    ставим Celery-задачу на уведомление за 24 часа до срока.
    """
    from apps.tasks.tasks import send_deadline_reminder

    if not instance.deadline or not instance.manager:
        return
    if instance.status in ('closed', 'rejected'):
        return

    reminder_time = instance.deadline - timedelta(hours=24)
    now = timezone.now()

    if reminder_time > now:
        countdown_seconds = int((reminder_time - now).total_seconds())
        send_deadline_reminder.apply_async(
            args=[instance.pk],
            countdown=countdown_seconds,
            task_id=f'deadline-reminder-{instance.pk}',
        )
