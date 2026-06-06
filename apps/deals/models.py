from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Deal(models.Model):
    """Сделка — воронка продаж."""

    STAGE_LEAD = 'lead'
    STAGE_NEGOTIATION = 'negotiation'
    STAGE_PROPOSAL = 'proposal'
    STAGE_APPROVAL = 'approval'
    STAGE_WON = 'won'
    STAGE_LOST = 'lost'
    STAGES = [
        (STAGE_LEAD, 'Лид'),
        (STAGE_NEGOTIATION, 'Переговоры'),
        (STAGE_PROPOSAL, 'Коммерческое предложение'),
        (STAGE_APPROVAL, 'Согласование'),
        (STAGE_WON, 'Победа'),
        (STAGE_LOST, 'Проигрыш'),
    ]

    STAGE_ORDER = [
        STAGE_LEAD, STAGE_NEGOTIATION, STAGE_PROPOSAL, STAGE_APPROVAL, STAGE_WON, STAGE_LOST
    ]

    name = models.CharField('Название сделки', max_length=255)
    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE,
        related_name='deals', verbose_name='Клиент'
    )
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='deals', verbose_name='Менеджер'
    )
    stage = models.CharField('Этап', max_length=20, choices=STAGES, default=STAGE_LEAD)
    amount = models.DecimalField('Сумма, руб.', max_digits=14, decimal_places=2, default=0)
    probability = models.IntegerField('Вероятность, %', default=10)
    expected_close_date = models.DateField('Ожидаемая дата закрытия', null=True, blank=True)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    comments = GenericRelation('clients.Comment')
    documents = GenericRelation('clients.Document')

    class Meta:
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stage']),
            models.Index(fields=['manager']),
        ]

    def __str__(self):
        return self.name

    @property
    def weighted_amount(self) -> Decimal:
        """Прогнозируемая выручка = сумма × вероятность / 100."""
        return self.amount * Decimal(self.probability) / Decimal(100)

    @property
    def is_active(self):
        return self.stage not in (self.STAGE_WON, self.STAGE_LOST)

    def save(self, *args, **kwargs):
        # Автоматическая вероятность по этапу
        default_probabilities = {
            self.STAGE_LEAD: 10,
            self.STAGE_NEGOTIATION: 30,
            self.STAGE_PROPOSAL: 50,
            self.STAGE_APPROVAL: 75,
            self.STAGE_WON: 100,
            self.STAGE_LOST: 0,
        }
        if not self.pk:  # только при создании
            self.probability = default_probabilities.get(self.stage, self.probability)
        super().save(*args, **kwargs)
