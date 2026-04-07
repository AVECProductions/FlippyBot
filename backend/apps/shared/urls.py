from django.urls import path
from . import views

app_name = 'shared'

urlpatterns = [
    path('notifications/test/', views.test_notifications, name='test-notifications'),
    path('notifications/status/', views.notification_status, name='notification-status'),
]
