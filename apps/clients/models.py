import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

User = settings.AUTH_USER_MODEL


# ─── Менеджеры ────────────────────────────────────────────────────────────────

class ActiveClientManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# ─── Client ───────────────────────────────────────────────────────────────────

class Client(models.Model):
    """Карточка клиента."""

    TYPE_INDIVIDUAL = 'individual'
    TYPE_COMPANY = 'company'
    CLIENT_TYPES = [
        (TYPE_INDIVIDUAL, 'Физическое лицо'),
        (TYPE_COMPANY, 'Юридическое лицо'),
    ]

    CATEGORY_POTENTIAL = 'potential'
    CATEGORY_ACTIVE = 'active'
    CATEGORY_VIP = 'vip'
    CATEGORY_INACTIVE = 'inactive'
    CATEGORIES = [
        (CATEGORY_POTENTIAL, 'Потенциальный'),
        (CATEGORY_ACTIVE, 'Активный'),
        (CATEGORY_VIP, 'VIP'),
        (CATEGORY_INACTIVE, 'Неактивный'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Наименование', max_length=255)
    client_type = models.CharField('Тип', max_length=20, choices=CLIENT_TYPES)
    inn = models.CharField('ИНН', max_length=14, blank=True)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('E-mail', blank=True)
    address = models.TextField('Адрес', blank=True)
    category = models.CharField(
        'Категория', max_length=20, choices=CATEGORIES, default=CATEGORY_POTENTIAL
    )
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='clients', verbose_name='Менеджер'
    )
    is_active = models.BooleanField('Активен', default=True)
    notes = models.TextField('Заметки', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Generic relations
    comments = GenericRelation('Comment')
    documents = GenericRelation('Document')

    objects = models.Manager()
    active = ActiveClientManager()

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['manager']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def get_timeline_events(self):
        """Хронологическая лента событий клиента."""
        from apps.requests_app.models import ClientRequest
        from apps.deals.models import Deal

        events = []

        # Комментарии
        for c in self.comments.select_related('author').order_by('-created_at')[:20]:
            events.append({
                'type': 'comment',
                'icon': 'chat-left-text',
                'color': 'info',
                'title': c.get_interaction_type_display(),
                'description': c.text[:200],
                'author': str(c.author),
                'date': c.created_at.isoformat(),
            })

        # Смены статусов заявок
        for r in self.requests.select_related('manager').order_by('-created_at')[:10]:
            events.append({
                'type': 'request',
                'icon': 'ticket-detailed',
                'color': 'warning',
                'title': f'Заявка: {r.subject}',
                'description': r.get_status_display(),
                'author': str(r.manager) if r.manager else '—',
                'date': r.created_at.isoformat(),
            })

        # Сделки
        for d in self.deals.select_related('manager').order_by('-created_at')[:10]:
            events.append({
                'type': 'deal',
                'icon': 'currency-dollar',
                'color': 'success',
                'title': f'Сделка: {d.name}',
                'description': f'{d.get_stage_display()} — {d.amount} руб.',
                'author': str(d.manager) if d.manager else '—',
                'date': d.created_at.isoformat(),
            })

        events.sort(key=lambda x: x['date'], reverse=True)
        return events


# ─── Contact ──────────────────────────────────────────────────────────────────

class Contact(models.Model):
    """Контактное лицо клиента."""

    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='contacts', verbose_name='Клиент'
    )
    full_name = models.CharField('ФИО', max_length=255)
    position = models.CharField('Должность', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    email = models.EmailField('E-mail', blank=True)
    is_primary = models.BooleanField('Основной', default=False)
    notes = models.TextField('Заметки', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Контактное лицо'
        verbose_name_plural = 'Контактные лица'
        ordering = ['-is_primary', 'full_name']

    def __str__(self):
        return f'{self.full_name} ({self.client.name})'

    def save(self, *args, **kwargs):
        # Только один основной контакт на клиента
        if self.is_primary:
            Contact.objects.filter(client=self.client, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


# ─── Comment (Generic) ────────────────────────────────────────────────────────

class Comment(models.Model):
    """Комментарий/взаимодействие — привязан к любому объекту через ContentTypes."""

    INTERACTION_CALL = 'call'
    INTERACTION_MEETING = 'meeting'
    INTERACTION_EMAIL = 'email'
    INTERACTION_NOTE = 'note'
    INTERACTION_TYPES = [
        (INTERACTION_CALL, 'Звонок'),
        (INTERACTION_MEETING, 'Встреча'),
        (INTERACTION_EMAIL, 'E-mail'),
        (INTERACTION_NOTE, 'Заметка'),
    ]

    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='comments', verbose_name='Автор'
    )
    text = models.TextField('Текст')
    interaction_type = models.CharField(
        'Тип взаимодействия', max_length=20, choices=INTERACTION_TYPES, default=INTERACTION_NOTE
    )
    # Generic FK
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.get_interaction_type_display()} от {self.author} ({self.created_at:%d.%m.%Y})'


# ─── Document (Generic) ───────────────────────────────────────────────────────

class Document(models.Model):
    """Прикреплённый документ — привязан к любому объекту через ContentTypes."""

    DOC_CONTRACT = 'contract'
    DOC_ACT = 'act'
    DOC_INVOICE = 'invoice'
    DOC_OTHER = 'other'
    DOC_TYPES = [
        (DOC_CONTRACT, 'Договор'),
        (DOC_ACT, 'Акт'),
        (DOC_INVOICE, 'Счёт'),
        (DOC_OTHER, 'Прочее'),
    ]

    title = models.CharField('Название', max_length=255)
    doc_type = models.CharField('Тип документа', max_length=20, choices=DOC_TYPES, default=DOC_OTHER)
    file = models.FileField('Файл', upload_to='documents/%Y/%m/')
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='documents', verbose_name='Загрузил'
    )
    # Generic FK
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title
