from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, path
from django.db.models import Q
from apps.deals.models import Deal
from django import forms as dj_forms


class DealForm(dj_forms.ModelForm):
    class Meta:
        model = Deal
        fields = [
            'name', 'client', 'stage', 'amount', 'probability',
            'expected_close_date', 'description', 'manager',
        ]
        widgets = {
            'name':               dj_forms.TextInput(attrs={'class': 'form-control'}),
            'client':             dj_forms.Select(attrs={'class': 'form-select select2'}),
            'stage':              dj_forms.Select(attrs={'class': 'form-select'}),
            'amount':             dj_forms.NumberInput(attrs={'class': 'form-control'}),
            'probability':        dj_forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'expected_close_date': dj_forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description':        dj_forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager':            dj_forms.Select(attrs={'class': 'form-select select2'}),
        }


class DealListView(LoginRequiredMixin, ListView):
    model = Deal
    template_name = 'deals/list.html'
    context_object_name = 'deals'
    paginate_by = 25

    def get_queryset(self):
        qs = Deal.objects.select_related('client', 'manager')
        user = self.request.user
        if not user.is_admin and not user.is_supervisor:
            qs = qs.filter(manager=user)
        stage = self.request.GET.get('stage')
        if stage:
            qs = qs.filter(stage=stage)
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(client__name__icontains=search))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stages'] = Deal.STAGES
        return ctx


class DealDetailView(LoginRequiredMixin, DetailView):
    model = Deal
    template_name = 'deals/detail.html'
    context_object_name = 'deal'


class DealCreateView(LoginRequiredMixin, CreateView):
    model = Deal
    form_class = DealForm
    template_name = 'deals/form.html'
    success_url = reverse_lazy('deals:list')

    def form_valid(self, form):
        if not form.instance.manager:
            form.instance.manager = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Новая сделка'
        return ctx


class DealUpdateView(LoginRequiredMixin, UpdateView):
    model = Deal
    form_class = DealForm
    template_name = 'deals/form.html'

    def get_success_url(self):
        return reverse_lazy('deals:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f'Сделка: {self.object.name}'
        return ctx


# ── URLs ──────────────────────────────────────────────────────────────────────
app_name = 'deals'

urlpatterns = [
    path('', DealListView.as_view(), name='list'),
    path('new/', DealCreateView.as_view(), name='create'),
    path('<int:pk>/', DealDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', DealUpdateView.as_view(), name='edit'),
]
