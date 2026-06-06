from django.urls import path
from .views_and_urls import DealListView, DealDetailView, DealCreateView, DealUpdateView

app_name = 'deals'

urlpatterns = [
    path('', DealListView.as_view(), name='list'),
    path('new/', DealCreateView.as_view(), name='create'),
    path('<int:pk>/', DealDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', DealUpdateView.as_view(), name='edit'),
]
