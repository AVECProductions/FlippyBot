from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'listings'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'listings', views.ListingViewSet)

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Keywords API - used for legacy watchlist system
    path('keywords/by-scanner/', views.get_keywords_by_scanner, name='keywords-by-scanner'),
    path('keywords/bulk-update/', views.bulk_update_keywords, name='keywords-bulk-update'),
]

