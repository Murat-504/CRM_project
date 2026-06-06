from django.db import models
from django.utils import timezone
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Task(models.Model):
    """Задача / напоминание."""

    STATUS_TODO = 'todo'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_DONE = 'done'
    STATUS_CANCELLED = 'cancelled'
    STATUSES = [
        (STATUS_TODO, 'К выполнению'),
        (STATUS_IN_PROGRESS, 'В работе'),
        (STATUS_DONE, 'Выполнено'),
        (STATUS_CANCELLED, 'Отменено'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_HIGH = 'high'
    PRIORITIES = [
        (PRIORITY_LOW, 'Низкий'),
        (PRIORITY_MEDIUM, 'Средний'),
        (PRIORITY_HIGH, 'Высокий'),
    ]

    title = models.CharField('Название', max_length=255)
    description = models.TextField('Описание', blank=True)
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='tasks', verbose_name='Ответственный'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_tasks', verbose_name='Создал'
    )
    # Опциональная привязка к клиенту / заявке / сделке
    client = models.ForeignKey(
        'clients.Client', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tasks', verbose_name='Клиент'
    )
    due_date = models.DateTimeField('Срок', null=True, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUSES, default=STATUS_TODO)
    priority = models.CharField('Приоритет', max_length=20, choices=PRIORITIES, default=PRIORITY_MEDIUM)
    completed_at = models.DateTimeField('Дата выполнения', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.status == self.STATUS_DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.STATUS_DONE:
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        return (
            self.due_date
            and self.due_date < timezone.now()
            and self.status not in (self.STATUS_DONE, self.STATUS_CANCELLED)
        )
