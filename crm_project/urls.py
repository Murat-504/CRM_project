from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.reports.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    # Дашборд — главная страница
    path('', dashboard, name='dashboard'),
    # API
    path('api/', include('apps.api.urls')),
    # Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Frontend
    path('clients/', include('apps.clients.urls')),
    path('requests/', include('apps.requests_app.urls')),
    path('deals/', include('apps.deals.urls')),
    path('reports/', include('apps.reports.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('tasks/', include('apps.tasks.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
