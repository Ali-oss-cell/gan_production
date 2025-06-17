from django.urls import path

from .background_views import GreatItems, BackGroundJobsUserProfileDetailView
from .talent_profile_views import TalentUserProfileView, TalentMediaCreateView, TalentMediaDeleteView, SocialMediaLinksUpdateView
from .band_views import BandListView, BandDetailView, BandCreateView, BandUpdateView, BandDeleteView, JoinBandView, LeaveBandView
from .band_views import GenerateBandInvitationView, BandInvitationsListView, UseBandInvitationView
from .talent_specialization_views import TalentSpecializationView, ReferenceDataView
from .band_media_views import BandMediaView, BandMediaDeleteView

urlpatterns = [
    # Endpoint to upload media (protected by JWT authentication)
    path('profile/talent/media/', TalentMediaCreateView.as_view(), name='upload-media'),
    
    #Endpoint delete media by id
    path('media/<int:media_id>/delete/', TalentMediaDeleteView.as_view(), name='delete-media'),
    
    # Endpoint to show and update user profile details (protected by JWT authentication)
   
    path('profile/talent/', TalentUserProfileView.as_view(), name='profile-detail'),
    
    # Social media links endpoint
    path('profile/social-media/', SocialMediaLinksUpdateView.as_view(), name='social-media-links'),
    
    # Endpoints for background user profile (includes profile score)
    path('profile/background/', BackGroundJobsUserProfileDetailView.as_view(), name='background-profile-detail'),
    
    # Endpoint for managing talent specializations
    path('profile/specializations/', TalentSpecializationView.as_view(), name='talent-specializations'),
    
    # Background items endpoints
    path('profile/background/items/', GreatItems.as_view(), name='background-items-create'),
    
    # Band endpoints (includes band scoring)
    # Combined band endpoint (returns both list and details in one request)
    
    # Original separate endpoints (kept for backward compatibility)
    
    #get_the_band_for_the_users (includes band score)
    path('bands/', BandListView.as_view(), name='band-list'),

    path('bands/<int:id>/', BandDetailView.as_view(), name='band-detail'),
    path('bands/create/', BandCreateView.as_view(), name='band-create'),
    path('bands/<int:id>/update/', BandUpdateView.as_view(), name='band-update'),
    path('bands/<int:id>/delete/', BandDeleteView.as_view(), name='band-delete'),
    path('bands/<int:band_id>/join/', JoinBandView.as_view(), name='band-join'),
    path('bands/<int:band_id>/leave/', LeaveBandView.as_view(), name='band-leave'),
    # Member role updates are handled through the band update endpoint
    # Direct member addition endpoint has been removed - members can only join via invitations
    
    # Band invitation endpoints
    path('bands/<int:band_id>/generate-code/', GenerateBandInvitationView.as_view(), name='generate-band-invitation'),
    path('bands/<int:band_id>/invitations/', BandInvitationsListView.as_view(), name='band-invitations-list'),
    path('bands/join-with-code/', UseBandInvitationView.as_view(), name='use-band-invitation'),
    
    # Band media endpoints
    path('bands/<int:band_id>/media/', BandMediaView.as_view(), name='band-media'),
    path('bands/<int:band_id>/media/<int:media_id>/delete/', BandMediaDeleteView.as_view(), name='band-media-delete'),
    
    # Reference data endpoints
    path('reference-data/', ReferenceDataView.as_view(), name='reference_data'),
]