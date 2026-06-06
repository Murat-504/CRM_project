from django.urls import path
from .views import ClientListView, ClientDetailView, ClientCreateView, ClientUpdateView

app_name = 'clients'

urlpatterns = [
    path('', ClientListView.as_view(), name='list'),
    path('new/', ClientCreateView.as_view(), name='create'),
    path('<uuid:pk>/', ClientDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', ClientUpdateView.as_view(), name='edit'),
]
