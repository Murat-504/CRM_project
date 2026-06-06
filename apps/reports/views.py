from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from apps.clients.models import Client
from apps.requests_app.models import ClientRequest
from apps.deals.models import Deal
from apps.tasks.models import Task


@login_required
def dashboard(request):
    user = request.user
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── Фильтрация по роли ────────────────────────────────────────────────
    if user.is_admin or user.is_supervisor:
        client_qs = Client.objects.all()
        request_qs = ClientRequest.objects.all()
        deal_qs = Deal.objects.all()
        task_qs = Task.objects.all()
    else:
        client_qs = Client.objects.filter(manager=user)
        request_qs = ClientRequest.objects.filter(manager=user)
        deal_qs = Deal.objects.filter(manager=user)
        task_qs = Task.objects.filter(assigned_to=user)

    # ── KPI-карточки ─────────────────────────────────────────────────────
    kpi = {
        'total_clients': client_qs.filter(is_active=True).count(),
        'new_clients_month': client_qs.filter(created_at__gte=month_start).count(),
        'open_requests': request_qs.filter(
            status__in=['new', 'in_progress', 'waiting']
        ).count(),
        'overdue_requests': request_qs.filter(
            deadline__lt=now,
            status__in=['new', 'in_progress', 'waiting']
        ).count(),
        'active_deals': deal_qs.exclude(stage__in=['won', 'lost']).count(),
        'won_deals_month': deal_qs.filter(stage='won', updated_at__gte=month_start).count(),
        'won_amount_month': deal_qs.filter(
            stage='won', updated_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'tasks_today': task_qs.filter(
            due_date__date=now.date(),
            status__in=['todo', 'in_progress']
        ).count(),
    }

    # ── Воронка сделок для Chart.js ────────────────────────────────────
    funnel_data = []
    for stage_key, stage_label in Deal.STAGES:
        agg = deal_qs.filter(stage=stage_key).aggregate(
            count=Count('id'), total=Sum('amount')
        )
        funnel_data.append({
            'stage': stage_key,
            'label': stage_label,
            'count': agg['count'] or 0,
            'amount': float(agg['total'] or 0),
        })

    # ── Новые заявки за 7 дней (mini sparkline) ────────────────────────
    sparkline = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        sparkline.append({
            'day': day.strftime('%d.%m'),
            'count': request_qs.filter(created_at__date=day).count(),
        })

    # ── Последние заявки ───────────────────────────────────────────────
    recent_requests = (
        request_qs.select_related('client', 'manager')
        .order_by('-created_at')[:8]
    )

    # ── Задачи на сегодня ─────────────────────────────────────────────
    tasks_today = (
        task_qs.filter(due_date__date=now.date(), status__in=['todo', 'in_progress'])
        .select_related('assigned_to', 'client')
        .order_by('-priority')[:10]
    )

    context = {
        'kpi': kpi,
        'funnel_data': funnel_data,
        'sparkline': sparkline,
        'recent_requests': recent_requests,
        'tasks_today': tasks_today,
    }
    return render(request, 'dashboard/index.html', context)
