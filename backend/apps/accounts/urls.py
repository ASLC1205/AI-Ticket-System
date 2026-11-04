from django.urls import path
from .views import (
    RegisterAPIView,
    LoginAPIView,
    ProfileAPIView,
    LogoutAPIView,ChangePasswordAPIView,
)
from .views import (
    PasswordResetRequestAPIView,
    PasswordResetConfirmAPIView
)
from rest_framework_simplejwt.views import TokenRefreshView
from .views import GoogleLoginAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path(
    'change-password/',
    ChangePasswordAPIView.as_view(),
    name='change_password'
),
path(
    'password-reset/',
    PasswordResetRequestAPIView.as_view(),
    name='password_reset'
),
path(
    'password-reset/confirm/',
    PasswordResetConfirmAPIView.as_view(),
    name='password_reset_confirm'
),
path(
    'google-login/',
    GoogleLoginAPIView.as_view(),
    name='google_login'
),
]