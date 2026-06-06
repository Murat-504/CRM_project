from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.utils import timezone
from django.conf import settings

User = settings.AUTH_USER_MODEL


class OverdueRequestManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            deadline__lt=timezone.now(),
            status__in=['new', 'in_progress', 'waiting']
        )


class ClientRequest(models.Model):
    """Заявка клиента."""

    # ── Статусы ──────────────────────────────────────────────────────────────
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_WAITING = 'waiting'
    STATUS_CLOSED = 'closed'
    STATUS_REJECTED = 'rejected'
    STATUSES = [
        (STATUS_NEW, 'Новая'),
        (STATUS_IN_PROGRESS, 'В работе'),
        (STATUS_WAITING, 'Ожидает ответа'),
        (STATUS_CLOSED, 'Завершена'),
        (STATUS_REJECTED, 'Отклонена'),
    ]

    # ── Приоритеты ───────────────────────────────────────────────────────────
    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITY_CRITICAL = 'critical'
    PRIORITIES = [
        (PRIORITY_LOW, 'Низкий'),
        (PRIORITY_MEDIUM, 'Средний'),
        (PRIORITY_HIGH, 'Высокий'),
        (PRIORITY_CRITICAL, 'Критический'),
    ]

    # ── Типы обращений ───────────────────────────────────────────────────────
    TYPE_COMPLAINT = 'complaint'
    TYPE_REQUEST = 'request'
    TYPE_CONSULTATION = 'consultation'
    TYPE_SERVICE = 'service'
    REQUEST_TYPES = [
        (TYPE_COMPLAINT, 'Жалоба'),
        (TYPE_REQUEST, 'Запрос'),
        (TYPE_CONSULTATION, 'Консультация'),
        (TYPE_SERVICE, 'Сервис'),
    ]

    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE,
        related_name='requests', verbose_name='Клиент'
    )
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_requests', verbose_name='Ответственный'
    )
    subject = models.CharField('Тема', max_length=255)
    description = models.TextField('Описание', blank=True)
    request_type = models.CharField(
        'Тип обращения', max_length=20, choices=REQUEST_TYPES, default=TYPE_REQUEST
    )
    status = models.CharField(
        'Статус', max_length=20, choices=STATUSES, default=STATUS_NEW
    )
    priority = models.CharField(
        'Приоритет', max_length=20, choices=PRIORITIES, default=PRIORITY_MEDIUM
    )
    deadline = models.DateTimeField('Срок выполнения', null=True, blank=True)
    closed_at = models.DateTimeField('Дата закрытия', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Generic relations
    comments = GenericRelation('clients.Comment')
    documents = GenericRelation('clients.Document')

    objects = models.Manager()
    overdue = OverdueRequestManager()

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['deadline']),
            models.Index(fields=['manager']),
        ]

    def __str__(self):
        return f'#{self.pk} — {self.subject}'

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем дату закрытия
        if self.status in (self.STATUS_CLOSED, self.STATUS_REJECTED) and not self.closed_at:
            self.closed_at = timezone.now()
        elif self.status not in (self.STATUS_CLOSED, self.STATUS_REJECTED):
            self.closed_at = None
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return (
            self.deadline
            and self.deadline < timezone.now()
            and self.status not in (self.STATUS_CLOSED, self.STATUS_REJECTED)
        )

    @property
    def priority_color(self):
        return {
            self.PRIORITY_LOW: 'success',
            self.PRIORITY_MEDIUM: 'warning',
            self.PRIORITY_HIGH: 'danger',
            self.PRIORITY_CRITICAL: 'dark',
        }.get(self.priority, 'secondary')
