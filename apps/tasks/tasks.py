try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func

from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta


@shared_task
def send_deadline_reminder(request_id):
    from apps.requests_app.models import ClientRequest
    try:
        req = ClientRequest.objects.select_related('manager', 'client').get(pk=request_id)
        if req.manager and req.manager.email:
            send_mail(
                subject=f'[CRM] Напоминание: заявка #{req.pk} — дедлайн через 24 часа',
                message=(
                    f'Уважаемый(ая) {req.manager.get_full_name()},\n\n'
                    f'Срок выполнения заявки «{req.subject}» '
                    f'(клиент: {req.client.name}) истекает {req.deadline:%d.%m.%Y %H:%M}.\n\n'
                    f'Текущий статус: {req.get_status_display()}\n\n'
                    'С уважением, CRM-система'
                ),
                from_email=None,
                recipient_list=[req.manager.email],
            )
    except Exception:
        pass


@shared_task
def check_upcoming_deadlines():
    from apps.requests_app.models import ClientRequest
    now = timezone.now()
    threshold = now + timedelta(hours=24)
    reqs = ClientRequest.objects.filter(
        deadline__gte=now, deadline__lte=threshold,
        status__in=['new', 'in_progress', 'waiting'],
        manager__isnull=False,
    )
    for req in reqs:
        send_deadline_reminder(req.pk)
    return f'Проверено {reqs.count()} заявок'


@shared_task
def send_weekly_digest():
    pass
