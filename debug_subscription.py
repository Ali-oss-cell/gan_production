#!/usr/bin/env python3

"""
Debug script to check subscription status for a user
Run this from your production server to see what's wrong with the subscription detection
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/var/www/gan7club/talent_platform')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from django.contrib.auth import get_user_model
from payments.models import Subscription, SubscriptionPlan

User = get_user_model()

def debug_user_subscription(user_email_or_id):
    """Debug subscription for a specific user"""
    try:
        # Try to get user by email first, then by ID
        try:
            user = User.objects.get(email=user_email_or_id)
        except User.DoesNotExist:
            user = User.objects.get(id=int(user_email_or_id))
        
        print(f"=== DEBUGGING SUBSCRIPTION FOR USER: {user.email} (ID: {user.id}) ===")
        print(f"User type: {getattr(user, 'account_type', 'Unknown')}")
        print(f"Is talent: {getattr(user, 'is_talent', False)}")
        print(f"Is background: {getattr(user, 'is_background', False)}")
        print()
        
        # Check all subscription plans
        print("=== AVAILABLE SUBSCRIPTION PLANS ===")
        plans = SubscriptionPlan.objects.all()
        for plan in plans:
            print(f"Plan: {plan.name} | Active: {plan.is_active} | Price: ${plan.price}")
        print()
        
        # Check user's subscriptions
        print("=== USER'S SUBSCRIPTIONS ===")
        subscriptions = Subscription.objects.filter(user=user)
        
        if not subscriptions.exists():
            print("❌ NO SUBSCRIPTIONS FOUND FOR THIS USER")
            return
        
        for sub in subscriptions:
            print(f"Subscription ID: {sub.id}")
            print(f"  Plan: {sub.plan.name}")
            print(f"  Status: {sub.status}")
            print(f"  Is Active: {sub.is_active}")
            print(f"  Start Date: {sub.start_date}")
            print(f"  End Date: {sub.end_date}")
            print(f"  Current Period End: {sub.current_period_end}")
            print(f"  Is Valid: {sub.is_valid()}")
            print("  ---")
        
        # Test the specific bands subscription query
        print("=== TESTING BANDS SUBSCRIPTION QUERY ===")
        bands_query = Subscription.objects.filter(
            user=user,
            plan__name='bands',
            is_active=True,
            status='active'
        )
        
        print(f"Bands subscription exists: {bands_query.exists()}")
        print(f"Bands subscription count: {bands_query.count()}")
        
        if bands_query.exists():
            bands_sub = bands_query.first()
            print(f"Found bands subscription: {bands_sub}")
        else:
            print("❌ No bands subscription found with the current query")
            
            # Check what's missing
            print("\n=== DEBUGGING WHAT'S MISSING ===")
            
            # Check if bands plan exists
            try:
                bands_plan = SubscriptionPlan.objects.get(name='bands')
                print(f"✅ Bands plan exists: {bands_plan}")
            except SubscriptionPlan.DoesNotExist:
                print("❌ Bands plan does not exist!")
                return
            
            # Check user's subscriptions to bands plan
            user_bands_subs = Subscription.objects.filter(user=user, plan__name='bands')
            print(f"User has {user_bands_subs.count()} subscriptions to bands plan")
            
            for sub in user_bands_subs:
                print(f"  Subscription {sub.id}:")
                print(f"    Status: {sub.status} (need: 'active')")
                print(f"    Is Active: {sub.is_active} (need: True)")
                print(f"    Plan Name: {sub.plan.name} (need: 'bands')")
        
    except User.DoesNotExist:
        print(f"❌ User not found: {user_email_or_id}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_subscription.py <user_email_or_id>")
        print("Example: python debug_subscription.py user@example.com")
        print("Example: python debug_subscription.py 123")
        sys.exit(1)
    
    debug_user_subscription(sys.argv[1])

