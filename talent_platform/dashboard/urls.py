from django.urls import path, include
from . import views
from .search_views import UnifiedSearchView

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

    # All profiles view - dashboard users can see all profiles
    path('profiles/', views.AllProfilesView.as_view(), name='all-profiles'),
    
    # Unified search endpoint - handles all search functionality
    path('search/', UnifiedSearchView.as_view(), name='unified-search'),
    
    # Profile detail endpoints for dashboard users
    path('profiles/talent/<int:pk>/', views.TalentProfileDetailView.as_view(), name='talent-profile-detail'),
    path('profiles/visual/<int:pk>/', views.VisualWorkerDetailView.as_view(), name='visual-worker-detail'),
    path('profiles/expressive/<int:pk>/', views.ExpressiveWorkerDetailView.as_view(), name='expressive-worker-detail'),
    path('profiles/hybrid/<int:pk>/', views.HybridWorkerDetailView.as_view(), name='hybrid-worker-detail'),
    path('profiles/band/<int:pk>/', views.BandDetailView.as_view(), name='band-detail'),
]