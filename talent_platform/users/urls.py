# urls.py
from django.urls import path
from .views import (
    UserRegistrationView, TalentLoginView, BackgroundLoginView, 
    VerifyEmailCodeView, ResendVerificationCodeView, DashboardLoginView
)

urlpatterns = [
    # Registration
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # Logins
    path('login/talent/', TalentLoginView.as_view(), name='talent-login'),
    path('login/background/', BackgroundLoginView.as_view(), name='background-login'),
    path('admin/login/', DashboardLoginView.as_view(), name='dashboard-login'),
    
    # Dashboard User Management endpoints moved to dashboard app
    
    # Email Verification (code-based only)
    path('verify-code/', VerifyEmailCodeView.as_view(), name='verify-code'),
    path('resend-code/', ResendVerificationCodeView.as_view(), name='resend-code'),
]