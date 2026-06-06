# ── views.py ─────────────────────────────────────────────────────────────────
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q
from apps.requests_app.models import ClientRequest
from django import forms as dj_forms


class RequestListView(LoginRequiredMixin, ListView):
    model = ClientRequest
    template_name = 'requests_app/list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        qs = ClientRequest.objects.select_related('client', 'manager')
        user = self.request.user
        if not user.is_admin and not user.is_supervisor:
            qs = qs.filter(manager=user)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(subject__icontains=search) | Q(client__name__icontains=search))
        return qs.order_by('-created_at')


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = ClientRequest
    template_name = 'requests_app/detail.html'
    context_object_name = 'req'

    def get_queryset(self):
        qs = ClientRequest.objects.select_related('client', 'manager')
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(manager=self.request.user)
        return qs


class RequestKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'requests_app/kanban.html'


# ── Form ──────────────────────────────────────────────────────────────────────

class ClientRequestForm(dj_forms.ModelForm):
    class Meta:
        model = ClientRequest
        fields = [
            'client', 'subject', 'description', 'request_type',
            'priority', 'deadline', 'manager',
        ]
        widgets = {
            'client':       dj_forms.Select(attrs={'class': 'form-select select2'}),
            'subject':      dj_forms.TextInput(attrs={'class': 'form-control'}),
            'description':  dj_forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'request_type': dj_forms.Select(attrs={'class': 'form-select'}),
            'priority':     dj_forms.Select(attrs={'class': 'form-select'}),
            'deadline':     dj_forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'manager':      dj_forms.Select(attrs={'class': 'form-select select2'}),
        }


class RequestCreateView(LoginRequiredMixin, CreateView):
    model = ClientRequest
    form_class = ClientRequestForm
    template_name = 'requests_app/form.html'
    success_url = reverse_lazy('requests_app:list')

    def get_initial(self):
        initial = super().get_initial()
        client_id = self.request.GET.get('client')
        if client_id:
            initial['client'] = client_id
        return initial

    def form_valid(self, form):
        if not form.instance.manager:
            form.instance.manager = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Новая заявка'
        return ctx


class RequestUpdateView(LoginRequiredMixin, UpdateView):
    model = ClientRequest
    form_class = ClientRequestForm
    template_name = 'requests_app/form.html'

    def get_success_url(self):
        return reverse_lazy('requests_app:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f'Заявка: {self.object.subject}'
        return ctx
