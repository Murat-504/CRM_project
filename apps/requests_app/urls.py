from django.urls import path
from .views import (
    RequestListView, RequestDetailView, RequestKanbanView,
    RequestCreateView, RequestUpdateView,
)

app_name = 'requests_app'

urlpatterns = [
    path('', RequestListView.as_view(), name='list'),
    path('kanban/', RequestKanbanView.as_view(), name='kanban'),
    path('new/', RequestCreateView.as_view(), name='create'),
    path('<int:pk>/', RequestDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', RequestUpdateView.as_view(), name='edit'),
]
