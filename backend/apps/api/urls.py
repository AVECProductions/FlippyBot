from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # Scanners API
    path('', include('apps.scanners.urls')),
    
    # Listings API  
    path('', include('apps.listings.urls')),
    
    # Shared services (notifications, etc.)
    path('', include('apps.shared.urls')),
]
