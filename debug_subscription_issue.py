#!/usr/bin/env python3
"""
Debug the exact subscription issue by checking what's in the database
"""
import os
import sys
import django

# Add the Django project path
sys.path.append('./talent_platform')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')

# Setup Django
django.setup()

def debug_subscription_issue():
    print("🔍 DEBUGGING SUBSCRIPTION ISSUE")
    print("=" * 50)
    
    from payments.models import Subscription, SubscriptionPlan
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    print("1. Available Subscription Plans:")
    plans = SubscriptionPlan.objects.all()
    for plan in plans:
        print(f"   - ID: {plan.id}, Name: '{plan.name}', Price: ${plan.price}, Stripe ID: {plan.stripe_price_id}")
    
    print("\n2. All Subscriptions in Database:")
    subscriptions = Subscription.objects.all().select_related('user', 'plan')
    for sub in subscriptions:
        print(f"   - User: {sub.user.email} (ID: {sub.user.id})")
        print(f"     Plan: '{sub.plan.name}' (ID: {sub.plan.id})")
        print(f"     Status: {sub.status}")
        print(f"     Is Active: {sub.is_active}")
        print(f"     Stripe Sub ID: {sub.stripe_subscription_id}")
        print()
    
    print("3. Check Specific User Subscriptions:")
    test_emails = ['wewe@wewe.com', 'dod@exam.com']
    
    for email in test_emails:
        try:
            user = User.objects.get(email=email)
            print(f"\n   👤 User: {email} (ID: {user.id})")
            
            # Check all subscriptions for this user
            user_subs = Subscription.objects.filter(user=user)
            if user_subs.exists():
                for sub in user_subs:
                    print(f"      - Plan: '{sub.plan.name}', Status: {sub.status}, Active: {sub.is_active}")
            else:
                print("      - No subscriptions found")
            
            # Test the exact query from the API
            bands_query = Subscription.objects.filter(
                user=user,
                plan__name='bands',
                is_active=True,
                status='active'
            )
            has_bands = bands_query.exists()
            print(f"      - API Query Result: has_bands_subscription = {has_bands}")
            
            if bands_query.exists():
                band_sub = bands_query.first()
                print(f"        Found subscription: ID {band_sub.id}, Plan: '{band_sub.plan.name}'")
        
        except User.DoesNotExist:
            print(f"   ❌ User {email} not found")
    
    print("\n4. Test Different Plan Name Variations:")
    test_user_id = 70  # Use a known user ID
    try:
        user = User.objects.get(id=test_user_id)
        print(f"   Testing with user ID {test_user_id}: {user.email}")
        
        # Test different plan name searches
        for plan_name in ['bands', 'Bands', 'BANDS', 'band']:
            query = Subscription.objects.filter(
                user=user,
                plan__name=plan_name,
                is_active=True,
                status='active'
            )
            count = query.count()
            print(f"      - plan__name='{plan_name}': {count} results")
            
    except User.DoesNotExist:
        print(f"   ❌ User ID {test_user_id} not found")

if __name__ == "__main__":
    debug_subscription_issue()
