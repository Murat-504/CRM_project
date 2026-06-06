from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserViewSet, ClientViewSet, ContactViewSet,
    ClientRequestViewSet, DealViewSet, TaskViewSet, ReportsViewSet,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'requests', ClientRequestViewSet, basename='request')
router.register(r'deals', DealViewSet, basename='deal')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'reports', ReportsViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
    # JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
