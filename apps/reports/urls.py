from django.urls import path
from .views import dashboard

app_name = 'reports'

urlpatterns = [
    path('', dashboard, name='index'),
]
