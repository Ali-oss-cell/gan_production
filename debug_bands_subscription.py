#!/usr/bin/env python3
"""
Debug script to check bands subscription issue on the server
Run this with: python manage.py shell < debug_bands_subscription.py
"""

print("🔍 Debugging Bands Subscription Issue")
print("=" * 50)

from payments.models import SubscriptionPlan, Subscription
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n1. Available Subscription Plans:")
print("-" * 30)
for plan in SubscriptionPlan.objects.all():
    print(f'ID: {plan.id}, Name: "{plan.name}", Stripe Price ID: {plan.stripe_price_id}')

print("\n2. Current Subscriptions:")
print("-" * 30)
for sub in Subscription.objects.all():
    print(f'User: {sub.user.email}, Plan: "{sub.plan.name}", Status: {sub.status}, Active: {sub.is_active}')

print("\n3. Testing bands subscription detection:")
print("-" * 40)

# Test the exact logic used in band_views.py
try:
    user = User.objects.get(email='wewe@wewe.com')
    print(f'Testing for user: {user.email}')
    
    # This is the exact query from band_views.py line 50-55
    has_bands_subscription = Subscription.objects.filter(
        user=user,
        plan__name='bands',  # lowercase 'bands'
        is_active=True,
        status='active'
    ).exists()
    print(f'✓ has_bands_subscription (lowercase "bands"): {has_bands_subscription}')
    
    # Test with capital 'Bands'
    has_bands_subscription_capital = Subscription.objects.filter(
        user=user,
        plan__name='Bands',  # capital 'Bands'
        is_active=True,
        status='active'
    ).exists()
    print(f'✓ has_bands_subscription (capital "Bands"): {has_bands_subscription_capital}')
    
    # Get the actual subscription details
    user_subs = Subscription.objects.filter(user=user)
    print(f'\n📋 All subscriptions for {user.email}:')
    for sub in user_subs:
        print(f'  - Plan: "{sub.plan.name}", Status: {sub.status}, Active: {sub.is_active}')
        print(f'    Stripe ID: {sub.stripe_subscription_id}')
        print(f'    Created: {sub.start_date}')
    
except User.DoesNotExist:
    print('❌ User wewe@wewe.com not found')

print("\n4. Checking webhook logs:")
print("-" * 25)
print("Run this to check recent webhook activity:")
print("journalctl -u gan7club.service -f --since '10 minutes ago' | grep -E '(webhook|subscription|payment)'")

print("\n5. ISSUE DIAGNOSIS:")
print("-" * 20)
bands_plan = SubscriptionPlan.objects.filter(name__icontains='bands').first()
if bands_plan:
    print(f'✓ Found bands plan: "{bands_plan.name}" (ID: {bands_plan.id})')
    
    # Check if the plan name matches what the API is looking for
    if bands_plan.name.lower() == 'bands':
        print('✓ Plan name matches API expectation')
    else:
        print(f'❌ ISSUE FOUND: Plan name is "{bands_plan.name}" but API looks for "bands"')
        print('📝 FIX: Update band_views.py to use correct plan name')
else:
    print('❌ No bands plan found!')

print("\n🔧 NEXT STEPS:")
print("1. If plan name mismatch: Fix band_views.py")
print("2. If webhook not working: Check server logs")
print("3. If subscription inactive: Check webhook handlers")
print("=" * 50)
