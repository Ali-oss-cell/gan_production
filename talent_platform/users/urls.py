# urls.py
from django.urls import path
from .views import (
    UserRegistrationView, TalentLoginView, BackgroundLoginView, VerifyEmailView,
    DashboardLoginView
)

urlpatterns = [
    # Registration
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # Logins
    path('login/talent/', TalentLoginView.as_view(), name='talent-login'),
    path('login/background/', BackgroundLoginView.as_view(), name='background-login'),
    path('login/dashboard/', DashboardLoginView.as_view(), name='dashboard-login'),
    
    # Dashboard User Management endpoints moved to dashboard app
    
    # Email Verification
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
]