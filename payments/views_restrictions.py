from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models_restrictions import RestrictedCountryUser
from .serializers_restrictions import RestrictedCountryUserSerializer
from .country_restrictions import RESTRICTED_COUNTRIES
from users.permissions import IsAdminDashboardUser, IsDashboardUser
from users.models import BaseUser
from profiles.models import TalentUserProfile

class RestrictedCountryUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing users from restricted countries (e.g., Syria).
    This allows dashboard administrators to view and update account types for users
    from countries with payment restrictions.
    """
    serializer_class = RestrictedCountryUserSerializer
    permission_classes = [IsAuthenticated, IsAdminDashboardUser | IsDashboardUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'is_approved', 'account_type']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'notes']
    ordering_fields = ['created_at', 'updated_at', 'user__email']
    ordering = ['-created_at']
    throttle_scope = 'restricted_country'
    
    def get_queryset(self):
        """
        Return all restricted country users.
        """
        return RestrictedCountryUser.objects.all().select_related('user', 'last_updated_by')
    
    def perform_update(self, serializer):
        """
        Update the restricted country user and set the last_updated_by field.
        """
        serializer.save(last_updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a restricted country user and update their account type.
        """
        restricted_user = self.get_object()
        account_type = request.data.get('account_type', 'free')
        
        # Update the restricted user record
        restricted_user.is_approved = True
        restricted_user.account_type = account_type
        restricted_user.last_updated_by = request.user
        restricted_user.notes = request.data.get('notes', restricted_user.notes)
        restricted_user.save()
        
        # Update the user's talent profile if it exists
        if hasattr(restricted_user.user, 'talent_user'):
            talent_profile = restricted_user.user.talent_user
            talent_profile.account_type = account_type
            talent_profile.save(update_fields=['account_type'])
        
        return Response({
            'message': f'User approved with account type: {account_type}',
            'user': RestrictedCountryUserSerializer(restricted_user).data
        })
    
    @action(detail=False, methods=['get'])
    def countries(self, request):
        """
        Get the list of restricted countries.
        """
        return Response({
            'restricted_countries': RESTRICTED_COUNTRIES
        })
    
    @action(detail=False, methods=['post'])
    def scan_users(self, request):
        """
        Scan all users to find those from restricted countries and create entries for them.
        """
        # Get all users with country information
        users = BaseUser.objects.filter(country__isnull=False).exclude(country='')
        
        # Filter users from restricted countries
        restricted_countries_lower = [c.lower() for c in RESTRICTED_COUNTRIES]
        restricted_users = []
        
        for user in users:
            if user.country.lower() in restricted_countries_lower:
                # Check if entry already exists
                entry, created = RestrictedCountryUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'country': user.country,
                        'account_type': getattr(user.talent_user, 'account_type', 'free') if hasattr(user, 'talent_user') else 'free'
                    }
                )
                
                if created:
                    restricted_users.append(entry)
        
        return Response({
            'message': f'Found {len(restricted_users)} new users from restricted countries',
            'count': len(restricted_users)
        })