from django.urls import path
from .views_and_urls import CRMLoginView, logout_view, profile_view

app_name = 'accounts'

urlpatterns = [
    path('login/', CRMLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]
