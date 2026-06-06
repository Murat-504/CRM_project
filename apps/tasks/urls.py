from django.urls import path
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Task
from django.utils import timezone

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_queryset(self):
        qs = Task.objects.select_related('assigned_to', 'client')
        if not self.request.user.is_admin and not self.request.user.is_supervisor:
            qs = qs.filter(assigned_to=self.request.user)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('due_date', '-priority')

app_name = 'tasks'

urlpatterns = [
    path('', TaskListView.as_view(), name='list'),
]
