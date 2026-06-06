import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Расширенная модель пользователя CRM-системы."""

    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_SUPERVISOR = 'supervisor'
    ROLES = [
        (ROLE_ADMIN, 'Администратор'),
        (ROLE_MANAGER, 'Менеджер'),
        (ROLE_SUPERVISOR, 'Руководитель'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField('Роль', max_length=20, choices=ROLES, default=ROLE_MANAGER)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    department = models.CharField('Отдел', max_length=100, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField('О себе', blank=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_supervisor(self):
        return self.role == self.ROLE_SUPERVISOR

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    def get_full_name(self):
        return f'{self.last_name} {self.first_name}'.strip()
