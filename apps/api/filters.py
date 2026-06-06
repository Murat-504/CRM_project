import django_filters
from apps.clients.models import Client
from apps.requests_app.models import ClientRequest
from apps.deals.models import Deal
from apps.tasks.models import Task


class ClientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.MultipleChoiceFilter(choices=Client.CATEGORIES)
    client_type = django_filters.ChoiceFilter(choices=Client.CLIENT_TYPES)
    is_active = django_filters.BooleanFilter()
    manager = django_filters.UUIDFilter(field_name='manager__id')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Client
        fields = ['category', 'client_type', 'is_active', 'manager']


class ClientRequestFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=ClientRequest.STATUSES)
    priority = django_filters.MultipleChoiceFilter(choices=ClientRequest.PRIORITIES)
    request_type = django_filters.ChoiceFilter(choices=ClientRequest.REQUEST_TYPES)
    manager = django_filters.UUIDFilter(field_name='manager__id')
    client = django_filters.UUIDFilter(field_name='client__id')
    deadline_before = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')
    deadline_after = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    is_overdue = django_filters.BooleanFilter(method='filter_overdue')

    class Meta:
        model = ClientRequest
        fields = ['status', 'priority', 'request_type', 'manager', 'client']

    def filter_overdue(self, queryset, name, value):
        from django.utils import timezone
        if value:
            return queryset.filter(
                deadline__lt=timezone.now(),
                status__in=['new', 'in_progress', 'waiting']
            )
        return queryset


class DealFilter(django_filters.FilterSet):
    stage = django_filters.MultipleChoiceFilter(choices=Deal.STAGES)
    manager = django_filters.UUIDFilter(field_name='manager__id')
    client = django_filters.UUIDFilter(field_name='client__id')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    close_before = django_filters.DateFilter(field_name='expected_close_date', lookup_expr='lte')
    close_after = django_filters.DateFilter(field_name='expected_close_date', lookup_expr='gte')

    class Meta:
        model = Deal
        fields = ['stage', 'manager', 'client']


class TaskFilter(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Task.STATUSES)
    priority = django_filters.MultipleChoiceFilter(choices=Task.PRIORITIES)
    assigned_to = django_filters.UUIDFilter(field_name='assigned_to__id')
    due_before = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='lte')
    due_after = django_filters.DateTimeFilter(field_name='due_date', lookup_expr='gte')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'assigned_to']
