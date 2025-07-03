from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminDashboardUser, IsDashboardUser
from payments.models_restrictions import RestrictedCountryUser
from .serializers import RestrictedCountryUserSerializer
from payments.country_restrictions import RESTRICTED_COUNTRIES
from users.models import BaseUser
from profiles.models import TalentUserProfile, BackGroundJobsProfile
from django.db.models import Q

class RestrictedUsersAPIView(APIView):
    """
    API endpoint for dashboard to manage restricted users (Syrian users).
    
    Features:
    - View all Syrian users with their current profiles
    - Scan for new Syrian users automatically
    - Approve users with talent subscriptions (free, silver, gold, platinum)
    - Give band subscriptions (basic, premium, pro) + band creator privileges
         - Give background jobs accounts (free, back_ground_jobs)
    - Update existing user account types
    - Track approval history and notes
    
    Available Actions:
    - scan_users: Find new Syrian users
    - approve_user: Approve with talent subscription
    - give_band_subscription: Give band access + creator privileges
    - give_background_account: Give background jobs access
    - update_user: Update existing user account
    """
    permission_classes = [IsAuthenticated, IsAdminDashboardUser | IsDashboardUser]
    
    def get(self, request):
        """Get all restricted country users for dashboard display"""
        restricted_users = RestrictedCountryUser.objects.all().select_related('user', 'last_updated_by')
        
        # Enhance user data with profile information
        enhanced_users = []
        for restricted_user in restricted_users:
            user_data = RestrictedCountryUserSerializer(restricted_user).data
            
            # Check what profiles the user has
            user_data['profiles'] = {
                'has_talent_profile': hasattr(restricted_user.user, 'talent_user'),
                'has_background_profile': hasattr(restricted_user.user, 'background_user'),
                'talent_account_type': getattr(restricted_user.user.talent_user, 'account_type', None) if hasattr(restricted_user.user, 'talent_user') else None,
                'background_account_type': getattr(restricted_user.user.background_user, 'account_type', None) if hasattr(restricted_user.user, 'background_user') else None,
            }
            
            enhanced_users.append(user_data)
        
        return Response({
            'title': 'Restricted Country Users',
            'active_page': 'restricted_users',
            'users': enhanced_users,
            'total_count': restricted_users.count(),
            'approved_count': restricted_users.filter(is_approved=True).count(),
            'pending_count': restricted_users.filter(is_approved=False).count(),
            'restricted_countries': RESTRICTED_COUNTRIES,
            'available_actions': [
                'scan_users',
                'approve_user',
                'update_user',
                'give_band_subscription',
                'give_background_account'
            ],
            'account_types': {
                'talent': ['free', 'silver', 'gold', 'platinum'],
                'background': ['free', 'back_ground_jobs'],
                'band_subscription': ['bands']  # Only one type of band subscription
            }
        })
    
    def post(self, request):
        """Handle different actions for restricted users"""
        action = request.data.get('action')
        
        if action == 'scan_users':
            return self._scan_for_restricted_users(request)
        elif action == 'approve_user':
            return self._approve_user(request)
        elif action == 'update_user':
            return self._update_user(request)
        elif action == 'give_band_subscription':
            return self._give_band_subscription(request)
        elif action == 'give_background_account':
            return self._give_background_account(request)
        else:
            return Response({
                'error': 'Invalid action. Use: scan_users, approve_user, update_user, give_band_subscription, or give_background_account'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _scan_for_restricted_users(self, request):
        """Scan all users to find those from restricted countries"""
        # Get all users with country information from either BaseUser or their profiles
        users = BaseUser.objects.filter(
            Q(country__isnull=False) & ~Q(country='') |  # Check BaseUser country
            Q(talent_user__country__isnull=False) & ~Q(talent_user__country='') |  # Check TalentUserProfile
            Q(background_profile__country__isnull=False) & ~Q(background_profile__country='')  # Check BackgroundUserProfile
        ).distinct()

        restricted_countries_lower = [c.lower() for c in RESTRICTED_COUNTRIES]
        new_restricted_users = []
        
        for user in users:
            # Check country in all possible locations
            user_country = None
            
            # Check BaseUser country
            if user.country and user.country.lower() in restricted_countries_lower:
                user_country = user.country
            # Check TalentUserProfile country
            elif hasattr(user, 'talent_user') and user.talent_user.country and user.talent_user.country.lower() in restricted_countries_lower:
                user_country = user.talent_user.country
            # Check BackgroundUserProfile country
            elif hasattr(user, 'background_profile') and user.background_profile.country and user.background_profile.country.lower() in restricted_countries_lower:
                user_country = user.background_profile.country
            
            if user_country:
                # Check if entry already exists
                entry, created = RestrictedCountryUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'country': user_country,
                        'account_type': getattr(user.talent_user, 'account_type', 'free') if hasattr(user, 'talent_user') else 'free'
                    }
                )
                
                if created:
                    new_restricted_users.append(entry)
        
        return Response({
            'message': f'Found {len(new_restricted_users)} new users from restricted countries',
            'count': len(new_restricted_users),
            'new_users': RestrictedCountryUserSerializer(new_restricted_users, many=True).data
        })
    
    def _approve_user(self, request):
        """Approve a restricted user and set their account type"""
        user_id = request.data.get('user_id')
        account_type = request.data.get('account_type', 'free')
        notes = request.data.get('notes', '')
        
        try:
            restricted_user = RestrictedCountryUser.objects.get(id=user_id)
            
            # Update restricted user record
            restricted_user.is_approved = True
            restricted_user.account_type = account_type
            restricted_user.notes = notes
            restricted_user.last_updated_by = request.user
            restricted_user.save()
            
            # Update talent profile if exists
            if hasattr(restricted_user.user, 'talent_user'):
                talent_profile = restricted_user.user.talent_user
                talent_profile.account_type = account_type
                talent_profile.save(update_fields=['account_type'])
            
            return Response({
                'message': f'User approved with account type: {account_type}',
                'user': RestrictedCountryUserSerializer(restricted_user).data
            })
            
        except RestrictedCountryUser.DoesNotExist:
            return Response({
                'error': 'Restricted user not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _give_band_subscription(self, request):
        """Give a Syrian user band subscription and make them band creator"""
        user_id = request.data.get('user_id')
        notes = request.data.get('notes', '')
        
        try:
            restricted_user = RestrictedCountryUser.objects.get(id=user_id)
            user = restricted_user.user
            
            # Check if user has talent profile
            if not hasattr(user, 'talent_user'):
                return Response({
                    'error': 'User does not have a talent profile. Please create a talent profile first.',
                    'user_id': user_id,
                    'email': user.email
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update talent profile first (required for bands)
            talent_profile, created = TalentUserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'account_type': restricted_user.account_type,  # Keep original account type
                }
            )
            
            # Update talent profile account type if it exists
            if not created:
                talent_profile.account_type = restricted_user.account_type  # Keep original account type
                talent_profile.save(update_fields=['account_type'])
            
            # Update restricted user record
            restricted_user.is_approved = True
            restricted_user.notes = f"{notes} | Band subscription granted"
            restricted_user.last_updated_by = request.user
            restricted_user.save()
            
            return Response({
                'message': 'User granted band subscription and band creator privileges',
                'user': RestrictedCountryUserSerializer(restricted_user).data,
                'account_type': restricted_user.account_type,
                'band_creator': True
            })
            
        except RestrictedCountryUser.DoesNotExist:
            return Response({
                'error': 'Restricted user not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _give_background_account(self, request):
        """Give a Syrian user background jobs account"""
        user_id = request.data.get('user_id')
        background_account_type = request.data.get('background_account_type', 'free')  # back_ground_jobs, free
        notes = request.data.get('notes', '')
        
        try:
            restricted_user = RestrictedCountryUser.objects.get(id=user_id)
            user = restricted_user.user
            
            # Check if user has background profile
            if not hasattr(user, 'background_user'):
                return Response({
                    'error': 'User does not have a background profile. Please create a background profile first.',
                    'user_id': user_id,
                    'email': user.email
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create or update background profile
            background_profile, created = BackGroundJobsProfile.objects.get_or_create(
                user=user,
                defaults={
                    'account_type': background_account_type,
                }
            )
            
            # Update background profile account type if it exists
            if not created:
                background_profile.account_type = background_account_type
                background_profile.save(update_fields=['account_type'])
            
            # Update restricted user record
            restricted_user.is_approved = True
            restricted_user.account_type = background_account_type
            restricted_user.notes = f"{notes} | Background account: {background_account_type} | Background jobs access granted"
            restricted_user.last_updated_by = request.user
            restricted_user.save()
            
            return Response({
                'message': f'User granted background jobs account ({background_account_type})',
                'user': RestrictedCountryUserSerializer(restricted_user).data,
                'background_account': background_account_type,
                'background_profile_created': created,
                'access_level': 'Full background jobs marketplace access' if background_account_type == 'back_ground_jobs' else 'Basic background jobs access'
            })
            
        except RestrictedCountryUser.DoesNotExist:
            return Response({
                'error': 'Restricted user not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _update_user(self, request):
        """Update a restricted user's account type"""
        user_id = request.data.get('user_id')
        account_type = request.data.get('account_type')
        notes = request.data.get('notes', '')
        
        try:
            restricted_user = RestrictedCountryUser.objects.get(id=user_id)
            
            # Update fields
            if account_type:
                restricted_user.account_type = account_type
                # Update talent profile if exists
                if hasattr(restricted_user.user, 'talent_user'):
                    talent_profile = restricted_user.user.talent_user
                    talent_profile.account_type = account_type
                    talent_profile.save(update_fields=['account_type'])
            
            if notes:
                restricted_user.notes = notes
            
            restricted_user.last_updated_by = request.user
            restricted_user.save()
            
            return Response({
                'message': 'User updated successfully',
                'user': RestrictedCountryUserSerializer(restricted_user).data
            })
            
        except RestrictedCountryUser.DoesNotExist:
            return Response({
                'error': 'Restricted user not found'
            }, status=status.HTTP_404_NOT_FOUND) 