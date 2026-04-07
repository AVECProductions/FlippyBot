from django.urls import path
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


class LoginRateThrottle(AnonRateThrottle):
    rate = '10/min'
    scope = 'login'


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]


app_name = 'auth'

urlpatterns = [
    # JWT token endpoints
    path('login/', ThrottledTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/', TokenVerifyView.as_view(), name='token_verify'),
]

