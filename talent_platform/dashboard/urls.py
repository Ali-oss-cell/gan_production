from django.urls import path, include
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Define dashboard URLs here
    path('', views.dashboard_home, name='home'),
    path('users/create/', views.DashboardUserCreateView.as_view(), name='create-user'),
    
    # Dashboard User Management (Admin only)
    path('users/', views.DashboardUserManagementView.as_view(), name='users'),
    path('users/<int:pk>/', views.DashboardUserDetailView.as_view(), name='user-detail'),
    
    # Payment Management (Admin only)
    path('payments/', include('payments.urls')),
]