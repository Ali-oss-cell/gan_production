from django.db import models
from django.conf import settings
from django.utils import timezone
from .country_restrictions import RESTRICTED_COUNTRIES

class RestrictedCountryUser(models.Model):
    """
    Model to track users from restricted countries who need manual account management.
    This allows administrators to view and update account types for users from countries
    with payment restrictions (like Syria).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restricted_country_status')
    country = models.CharField(max_length=50)
    is_approved = models.BooleanField(default=False)
    account_type = models.CharField(max_length=20, default='free')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='restricted_country_updates'
    )
    
    class Meta:
        verbose_name = 'Restricted Country User'
        verbose_name_plural = 'Restricted Country Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} ({self.country})"
    
    @classmethod
    def create_for_user(cls, user, country=None):
        """
        Create a restricted country user entry if the user's country is in the restricted list.
        
        Args:
            user: The user object
            country: Optional country override (if not using user.country)
            
        Returns:
            RestrictedCountryUser instance or None if not applicable
        """
        country_to_check = country or user.country
        
        if not country_to_check:
            return None
            
        if country_to_check.strip().lower() in [c.lower() for c in RESTRICTED_COUNTRIES]:
            return cls.objects.create(
                user=user,
                country=country_to_check,
                account_type=getattr(user.talent_user, 'account_type', 'free') if hasattr(user, 'talent_user') else 'free'
            )
        return None