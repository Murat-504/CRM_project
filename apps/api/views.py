from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.utils import timezone
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.clients.models import Client, Contact, Comment, Document
from apps.requests_app.models import ClientRequest
from apps.deals.models import Deal
from apps.tasks.models import Task
from apps.accounts.models import CustomUser

from .serializers import (
    ClientListSerializer, ClientDetailSerializer,
    ContactSerializer, CommentSerializer, DocumentSerializer,
    ClientRequestSerializer, ClientRequestStatusSerializer,
    DealSerializer, DealFunnelSerializer,
    TaskSerializer, UserSerializer, UserMinimalSerializer,
)
from .filters import ClientFilter, ClientRequestFilter, DealFilter, TaskFilter
from .permissions import ClientPermission, RequestPermission, IsSupervisorOrAdmin


# ─── Users ────────────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'department']
    ordering_fields = ['last_name', 'date_joined', 'role']
    ordering = ['last_name']

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Профиль текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def managers(self, request):
        """Список менеджеров (для select2)."""
        qs = CustomUser.objects.filter(role='manager').order_by('last_name')
        serializer = UserMinimalSerializer(qs, many=True)
        return Response(serializer.data)


# ─── Clients ──────────────────────────────────────────────────────────────────

class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [ClientPermission]
    filterset_class = ClientFilter
    search_fields = ['name', 'phone', 'email', 'inn', 'address']
    ordering_fields = ['name', 'created_at', 'category', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('list',):
            return ClientListSerializer
        return ClientDetailSerializer

    def get_queryset(self):
        qs = Client.objects.select_related('manager').annotate(
            open_requests_count=Count(
                'requests',
                filter=Q(requests__status__in=['new', 'in_progress', 'waiting'])
            ),
            active_deals_count=Count(
                'deals',
                filter=~Q(deals__stage__in=['won', 'lost'])
            ),
        ).filter(is_active=True)

        # Менеджер видит только своих клиентов
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(manager=self.request.user)
        return qs

    def perform_create(self, serializer):
        # Если менеджер не указан — назначаем создателя
        if not serializer.validated_data.get('manager'):
            serializer.save(manager=self.request.user)
        else:
            serializer.save()

    # ── Дополнительные actions ────────────────────────────────────────────────

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        client = self.get_object()
        serializer = ContactSerializer(client.contacts.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def requests(self, request, pk=None):
        client = self.get_object()
        qs = client.requests.select_related('manager').order_by('-created_at')
        serializer = ClientRequestSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def deals(self, request, pk=None):
        client = self.get_object()
        qs = client.deals.select_related('manager').order_by('-created_at')
        serializer = DealSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Хронологическая лента событий клиента."""
        client = self.get_object()
        events = client.get_timeline_events()
        return Response(events)

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        client = self.get_object()
        qs = client.documents.select_related('author').order_by('-uploaded_at')
        serializer = DocumentSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


# ─── Contacts ─────────────────────────────────────────────────────────────────

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['full_name', 'phone', 'email', 'position']
    ordering = ['full_name']

    def get_queryset(self):
        return Contact.objects.select_related('client').all()


# ─── ClientRequests ───────────────────────────────────────────────────────────

class ClientRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ClientRequestSerializer
    permission_classes = [RequestPermission]
    filterset_class = ClientRequestFilter
    search_fields = ['subject', 'description', 'client__name']
    ordering_fields = ['created_at', 'deadline', 'priority', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = ClientRequest.objects.select_related('client', 'manager')
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(manager=self.request.user)
        return qs

    def perform_create(self, serializer):
        if not serializer.validated_data.get('manager'):
            serializer.save(manager=self.request.user)
        else:
            serializer.save()

    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        """PATCH /api/requests/{id}/status/ — Kanban drag-and-drop."""
        instance = self.get_object()
        serializer = ClientRequestStatusSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ClientRequestSerializer(instance, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def kanban(self, request):
        """Данные для Kanban-доски: {status: [requests]}."""
        qs = self.get_queryset()
        result = {}
        for status_key, status_label in ClientRequest.STATUSES:
            requests_qs = qs.filter(status=status_key).order_by('-priority', '-created_at')
            result[status_key] = {
                'label': status_label,
                'items': ClientRequestSerializer(
                    requests_qs, many=True, context={'request': request}
                ).data,
            }
        return Response(result)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        instance = self.get_object()
        if request.method == 'POST':
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(ClientRequest)
            comment = Comment.objects.create(
                author=request.user,
                text=request.data.get('text', ''),
                interaction_type=request.data.get('interaction_type', 'note'),
                content_type=ct,
                object_id=instance.pk,
            )
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        serializer = CommentSerializer(instance.comments.all(), many=True)
        return Response(serializer.data)


# ─── Deals ────────────────────────────────────────────────────────────────────

class DealViewSet(viewsets.ModelViewSet):
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = DealFilter
    search_fields = ['name', 'client__name', 'description']
    ordering_fields = ['created_at', 'amount', 'expected_close_date', 'probability']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = Deal.objects.select_related('client', 'manager')
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(manager=self.request.user)
        return qs

    def perform_create(self, serializer):
        if not serializer.validated_data.get('manager'):
            serializer.save(manager=self.request.user)
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def funnel(self, request):
        """GET /api/deals/funnel/ — данные воронки продаж для Chart.js."""
        qs = self.get_queryset()
        result = []
        for stage_key, stage_label in Deal.STAGES:
            agg = qs.filter(stage=stage_key).aggregate(
                count=Count('id'),
                total_amount=Sum('amount'),
            )
            # weighted_amount считаем вручную (property не агрегируется)
            deals_in_stage = qs.filter(stage=stage_key)
            weighted = sum(d.weighted_amount for d in deals_in_stage)
            result.append({
                'stage': stage_key,
                'stage_display': stage_label,
                'count': agg['count'] or 0,
                'total_amount': agg['total_amount'] or Decimal('0'),
                'weighted_amount': weighted,
            })
        serializer = DealFunnelSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Агрегированная сводка для дашборда."""
        qs = self.get_queryset()
        active = qs.exclude(stage__in=['won', 'lost'])
        agg = active.aggregate(count=Count('id'), total=Sum('amount'))
        won = qs.filter(stage='won').aggregate(count=Count('id'), total=Sum('amount'))
        return Response({
            'active_count': agg['count'] or 0,
            'active_amount': agg['total'] or 0,
            'won_count': won['count'] or 0,
            'won_amount': won['total'] or 0,
        })


# ─── Tasks ────────────────────────────────────────────────────────────────────

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TaskFilter
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'priority', 'status', 'created_at']
    ordering = ['due_date', '-priority']

    def get_queryset(self):
        qs = Task.objects.select_related('assigned_to', 'created_by', 'client')
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(assigned_to=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Задачи на сегодня."""
        today = timezone.now().date()
        qs = self.get_queryset().filter(
            due_date__date=today,
            status__in=['todo', 'in_progress']
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# ─── Reports ──────────────────────────────────────────────────────────────────

class ReportsViewSet(viewsets.ViewSet):
    permission_classes = [IsSupervisorOrAdmin]

    @action(detail=False, methods=['get'])
    def sales(self, request):
        """Отчёт по продажам за период."""
        from django.db.models.functions import TruncMonth
        period_start = request.query_params.get('start')
        period_end = request.query_params.get('end')

        qs = Deal.objects.filter(stage='won')
        if period_start:
            qs = qs.filter(created_at__date__gte=period_start)
        if period_end:
            qs = qs.filter(created_at__date__lte=period_end)

        by_month = (
            qs.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'), total=Sum('amount'))
            .order_by('month')
        )
        by_manager = (
            qs.values('manager__id', 'manager__last_name', 'manager__first_name')
            .annotate(count=Count('id'), total=Sum('amount'))
            .order_by('-total')
        )
        return Response({
            'by_month': list(by_month),
            'by_manager': list(by_manager),
            'totals': qs.aggregate(count=Count('id'), total=Sum('amount')),
        })

    @action(detail=False, methods=['get'])
    def clients_activity(self, request):
        """Активность клиентов за последние 30 дней."""
        from django.db.models.functions import TruncDay
        since = timezone.now() - timezone.timedelta(days=30)
        by_day = (
            Client.objects.filter(created_at__gte=since)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        return Response({'new_clients_by_day': list(by_day)})
