from payments.models import Subscription
from django.contrib.auth import get_user_model

User = get_user_model()

def check_background_user_subscription(user):
    """
    Check if a background user has an active subscription.
    
    Returns:
        dict: {
            'has_subscription': bool,
            'subscription': Subscription object or None,
            'message': str,
            'can_access_features': bool
        }
    """
    if not hasattr(user, 'is_background') or not user.is_background:
        return {
            'has_subscription': True,
            'subscription': None,
            'message': 'User is not a background user',
            'can_access_features': True
        }
    
    # Check for active subscription
    try:
        subscription = Subscription.objects.get(
            user=user,
            status='active',
            is_active=True
        )
        
        return {
            'has_subscription': True,
            'subscription': subscription,
            'message': 'Active subscription found',
            'can_access_features': True
        }
        
    except Subscription.DoesNotExist:
        return {
            'has_subscription': False,
            'subscription': None,
            'message': 'Background users must have an active subscription to access features. Please subscribe to the Production Assets Pro plan.',
            'can_access_features': False
        }

def get_background_user_restrictions(user):
    """
    Get a list of restrictions for background users without subscriptions.
    
    Returns:
        dict: {
            'restricted': bool,
            'restrictions': list,
            'subscription_required': bool
        }
    """
    if not hasattr(user, 'is_background') or not user.is_background:
        return {
            'restricted': False,
            'restrictions': [],
            'subscription_required': False
        }
    
    subscription_check = check_background_user_subscription(user)
    
    if subscription_check['has_subscription']:
        return {
            'restricted': False,
            'restrictions': [],
            'subscription_required': False
        }
    
    # List of restrictions for background users without subscription
    restrictions = [
        "Cannot share props, costumes, or other items",
        "Cannot rent or sell items",
        "Cannot access background job processing services",
        "Cannot upload media files",
        "Cannot create listings",
        "Cannot respond to job requests"
    ]
    
    return {
        'restricted': True,
        'restrictions': restrictions,
        'subscription_required': True,
        'subscription_message': 'Subscribe to Production Assets Pro plan ($300/year) to unlock all features'
    } 