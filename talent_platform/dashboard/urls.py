from django.urls import path, include
from . import views, email_views
from .search_views import UnifiedSearchView
from .views_restricted_api import RestrictedUsersAPIView
from .shared_media_views import (
    ShareMediaView, SharedMediaListView, SharedMediaDetailView,
    DeleteSharedMediaView, MySharedMediaView, SharedMediaStatsView
)
from django.views.generic import TemplateView

app_name = 'dashboard'

urlpatterns = [
    # Health check endpoint
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    
    # Dashboard Analytics
    path('analytics/', views.DashboardAnalyticsView.as_view(), name='dashboard-analytics'),
    
    # Define dashboard URLs here
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
    path('profiles/background/<int:pk>/', views.BackGroundJobsProfileDetailView.as_view(), name='background-profile-detail'),
    path('profiles/visual/<int:pk>/', views.VisualWorkerDetailView.as_view(), name='visual-worker-detail'),
    path('profiles/expressive/<int:pk>/', views.ExpressiveWorkerDetailView.as_view(), name='expressive-worker-detail'),
    path('profiles/hybrid/<int:pk>/', views.HybridWorkerDetailView.as_view(), name='hybrid-worker-detail'),
    path('profiles/band/<int:pk>/', views.BandDetailView.as_view(), name='band-detail'),
    
    # Shared Media Management
    path('share-media/', ShareMediaView.as_view(), name='share-media'),
    path('shared-media/', SharedMediaListView.as_view(), name='shared-media-list'),
    path('shared-media/<int:pk>/', SharedMediaDetailView.as_view(), name='shared-media-detail'),
    path('shared-media/<int:pk>/delete/', DeleteSharedMediaView.as_view(), name='delete-shared-media'),
    path('my-shared-media/', MySharedMediaView.as_view(), name='my-shared-media'),
    path('shared-media/stats/', SharedMediaStatsView.as_view(), name='shared-media-stats'),
    
    # Restricted country users management
    path('restricted-users/', RestrictedUsersAPIView.as_view(), name='restricted-users-api'),
    
    # Email management URLs
    path('email/send/', email_views.SendEmailView.as_view(), name='send-email'),
    path('send-email/', email_views.SendEmailView.as_view(), name='send-email-alt'),
    path('email/list/', email_views.EmailListView.as_view(), name='email-list'),
    path('email/<int:pk>/', email_views.EmailDetailView.as_view(), name='email-detail'),
]