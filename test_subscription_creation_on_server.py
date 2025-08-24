#!/usr/bin/env python3
"""
Script to run on the server to test subscription creation manually
"""

# Simple test commands to run on the server via Django shell
commands = [
    # Check if bands plan exists
    """
from payments.models import SubscriptionPlan, Subscription
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== CHECKING BANDS PLAN ===")
try:
    bands_plan = SubscriptionPlan.objects.get(name='bands')
    print(f"✅ Bands plan found: ID {bands_plan.id}")
    print(f"   Stripe Price ID: {bands_plan.stripe_price_id}")
except SubscriptionPlan.DoesNotExist:
    print("❌ Bands plan not found!")
""",

    # Check test user
    """
print("\\n=== CHECKING TEST USER ===")
try:
    user = User.objects.get(email='wewe@wewe.com')
    print(f"✅ User found: {user.email} (ID: {user.id})")
    
    # Check existing subscriptions
    subs = Subscription.objects.filter(user=user)
    print(f"   Total subscriptions: {subs.count()}")
    for sub in subs:
        print(f"   - Plan: {sub.plan.name}, Status: {sub.status}, Active: {sub.is_active}")
        
except User.DoesNotExist:
    print("❌ Test user not found!")
""",

    # Test API query
    """
print("\\n=== TESTING API QUERY ===")
if 'user' in locals():
    has_bands = Subscription.objects.filter(
        user=user,
        plan__name='bands',
        is_active=True,
        status='active'
    ).exists()
    print(f"API Query Result: has_bands_subscription = {has_bands}")
    
    # Debug query
    bands_subs = Subscription.objects.filter(user=user, plan__name='bands')
    print(f"All bands subscriptions for user:")
    for sub in bands_subs:
        print(f"  - Status: '{sub.status}', Active: {sub.is_active}")
        print(f"    Meets criteria: {sub.is_active and sub.status == 'active'}")
""",

    # Test manual creation
    """
print("\\n=== TESTING MANUAL SUBSCRIPTION CREATION ===")
if 'user' in locals() and 'bands_plan' in locals():
    # Delete existing test subscriptions first
    test_subs = Subscription.objects.filter(
        user=user, 
        stripe_subscription_id__startswith='sub_test'
    )
    deleted_count = test_subs.count()
    test_subs.delete()
    print(f"Deleted {deleted_count} test subscriptions")
    
    # Create a test subscription
    test_sub = Subscription.objects.create(
        user=user,
        plan=bands_plan,
        stripe_customer_id='cus_test_customer',
        stripe_subscription_id='sub_test_manual_creation',
        status='active',
        is_active=True
    )
    print(f"✅ Created test subscription: ID {test_sub.id}")
    
    # Test API query again
    has_bands_after = Subscription.objects.filter(
        user=user,
        plan__name='bands',
        is_active=True,
        status='active'
    ).exists()
    print(f"API Query Result after creation: has_bands_subscription = {has_bands_after}")
"""
]

print("🔧 MANUAL SUBSCRIPTION TEST COMMANDS")
print("=" * 50)
print("Run these commands on your server:")
print()

for i, cmd in enumerate(commands, 1):
    print(f"## Command {i}:")
    print("```bash")
    print(f"python manage.py shell -c \"{cmd.strip()}\"")
    print("```")
    print()

print("🚀 OR run all at once:")
print("```bash")
all_commands = "; ".join([cmd.strip().replace('\n', '\\n') for cmd in commands])
print(f"python manage.py shell -c \"{all_commands}\"")
print("```")
