from rest_framework.permissions import BasePermission
from .models import BandMembership, TalentUserProfile
from django.contrib.auth import get_user_model
from payments.models import Subscription

User = get_user_model()

class IsBandAdmin(BasePermission):
    """
    Custom permission to only allow band admins to perform certain actions.
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get the band_id from the URL parameters
        band_id = view.kwargs.get('band_id')
        if not band_id:
            return False
        
        # Check if the user has a talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return False
        
        # Check if the user is an admin of the band
        is_admin = BandMembership.objects.filter(
            band_id=band_id, 
            talent_user=talent_profile, 
            role='admin'
        ).exists()
        
        # Also check if the user is the creator of the band
        is_creator = talent_profile.created_bands.filter(id=band_id).exists()
        
        return is_admin or is_creator
    
    def has_object_permission(self, request, view, obj):
        # Check if the object has a band attribute
        if not hasattr(obj, 'band'):
            return False
        
        # Get the user's talent profile
        try:
            talent_profile = TalentUserProfile.objects.get(user=request.user)
        except TalentUserProfile.DoesNotExist:
            return False
        
        # Check if the user is an admin of the band
        is_admin = BandMembership.objects.filter(
            band=obj.band, 
            talent_user=talent_profile, 
            role='admin'
        ).exists()
        
        # Also check if the user is the creator of the band
        is_creator = obj.band.creator == talent_profile
        
        return is_admin or is_creator

class BackgroundUserSubscriptionRequired(BasePermission):
    """
    Permission class to ensure background users have an active subscription
    before they can access certain features.
    """
    
    def has_permission(self, request, view):
        # Allow all non-background users
        if not hasattr(request.user, 'is_background') or not request.user.is_background:
            return True
            
        # For background users, check if they have an active subscription
        if request.user.is_background:
            # Check if user has an active subscription
            has_active_subscription = Subscription.objects.filter(
                user=request.user,
                status='active',
                is_active=True
            ).exists()
            
            if not has_active_subscription:
                return False
                
        return True
    
    def message(self):
        return "Background users must have an active subscription to access this feature."

class BackgroundUserCanShareItems(BasePermission):
    """
    Permission class specifically for sharing items (props, costumes, etc.)
    """
    
    def has_permission(self, request, view):
        # Allow all non-background users
        if not hasattr(request.user, 'is_background') or not request.user.is_background:
            return True
            
        # For background users, check subscription
        if request.user.is_background:
            has_active_subscription = Subscription.objects.filter(
                user=request.user,
                status='active',
                is_active=True
            ).exists()
            
            if not has_active_subscription:
                return False
                
        return True
    
    def message(self):
        return "Background users must have an active subscription to share items."

class BackgroundUserCanRentOrSell(BasePermission):
    """
    Permission class for renting or selling items
    """
    
    def has_permission(self, request, view):
        # Allow all non-background users
        if not hasattr(request.user, 'is_background') or not request.user.is_background:
            return True
            
        # For background users, check subscription
        if request.user.is_background:
            has_active_subscription = Subscription.objects.filter(
                user=request.user,
                status='active',
                is_active=True
            ).exists()
            
            if not has_active_subscription:
                return False
                
        return True
    
    def message(self):
        return "Background users must have an active subscription to rent or sell items."