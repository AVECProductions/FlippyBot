from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from decouple import config

urlpatterns = [
    # Admin URL with custom path from settings
    path(f'{settings.ADMIN_URL}/', admin.site.urls),
    
    # API endpoints
    path('api/', include('apps.api.urls')),
    
    # Simple JWT Auth URLs
    path('auth/', include('apps.auth.urls')),
    
    # Legacy main app temporarily disabled (models commented out)
    # path('legacy/', include('main.urls')),

    
    # Media files in development
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
]