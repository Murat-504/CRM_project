from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from apps.clients.models import Client, Contact
from apps.clients.forms import ClientForm, ContactForm


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/list.html'
    context_object_name = 'clients'
    paginate_by = 25

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

        user = self.request.user
        if not user.is_admin and not user.is_supervisor:
            qs = qs.filter(manager=user)

        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search) |
                Q(inn__icontains=search)
            )
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        client_type = self.request.GET.get('client_type')
        if client_type:
            qs = qs.filter(client_type=client_type)
        return qs.order_by('-created_at')


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/detail.html'
    context_object_name = 'client'

    def get_queryset(self):
        qs = Client.objects.prefetch_related('contacts')
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(manager=self.request.user)
        return qs


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'
    success_url = reverse_lazy('clients:list')

    def form_valid(self, form):
        if not form.instance.manager:
            form.instance.manager = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Новый клиент'
        return ctx


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/form.html'

    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = f'Редактирование: {self.object.name}'
        return ctx
