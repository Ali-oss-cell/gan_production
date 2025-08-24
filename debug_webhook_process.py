#!/usr/bin/env python3
"""
Debug the complete webhook process to find where bands subscription creation fails
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

def debug_webhook_process():
    print("🔍 DEBUGGING WEBHOOK PROCESS")
    print("=" * 60)
    
    from payments.models import Subscription, SubscriptionPlan
    from django.contrib.auth import get_user_model
    import stripe
    from django.conf import settings
    
    User = get_user_model()
    
    print("1. Check Subscription Plans in Database:")
    plans = SubscriptionPlan.objects.all()
    bands_plan = None
    for plan in plans:
        print(f"   - ID: {plan.id}, Name: '{plan.name}', Stripe ID: '{plan.stripe_price_id}'")
        if plan.name == 'bands':
            bands_plan = plan
    
    if not bands_plan:
        print("   ❌ No 'bands' plan found in database!")
        return
    else:
        print(f"   ✅ Bands plan found: ID {bands_plan.id}, Stripe ID: '{bands_plan.stripe_price_id}'")
    
    print("\n2. Check Test Users:")
    test_emails = ['wewe@wewe.com', 'dod@exam.com']
    test_users = []
    
    for email in test_emails:
        try:
            user = User.objects.get(email=email)
            test_users.append(user)
            print(f"   ✅ User found: {email} (ID: {user.id})")
            
            # Check subscriptions for this user
            user_subs = Subscription.objects.filter(user=user)
            if user_subs.exists():
                for sub in user_subs:
                    print(f"      - Plan: '{sub.plan.name}', Status: '{sub.status}', Active: {sub.is_active}")
                    print(f"        Stripe Sub ID: {sub.stripe_subscription_id}")
            else:
                print(f"      - No subscriptions found")
                
        except User.DoesNotExist:
            print(f"   ❌ User not found: {email}")
    
    print(f"\n3. Test Webhook Logic (Simulation):")
    if test_users:
        test_user = test_users[0]
        print(f"   Testing with user: {test_user.email} (ID: {test_user.id})")
        
        # Simulate a Stripe subscription object
        class MockStripeSubscription:
            def __init__(self):
                self.id = "sub_test_simulation"
                self.customer = "cus_test_customer"
                self.status = "active"
                self.current_period_start = 1693027200  # Aug 26, 2023
                self.current_period_end = 1724563200    # Aug 25, 2024
                self.cancel_at_period_end = False
                self.items = MockItems()
        
        class MockItems:
            def __init__(self):
                self.data = [MockItem()]
        
        class MockItem:
            def __init__(self):
                self.price = MockPrice()
        
        class MockPrice:
            def __init__(self):
                self.id = bands_plan.stripe_price_id  # Use the actual bands price ID
        
        mock_subscription = MockStripeSubscription()
        
        print(f"   Mock subscription:")
        print(f"     - Stripe ID: {mock_subscription.id}")
        print(f"     - Status: {mock_subscription.status}")
        print(f"     - Price ID: {mock_subscription.items.data[0].price.id}")
        
        # Test the create_or_update_subscription logic
        try:
            from payments.payment_services import StripePaymentService
            
            print(f"\n   Testing create_or_update_subscription...")
            subscription = StripePaymentService.create_or_update_subscription(test_user, mock_subscription)
            
            print(f"   ✅ Subscription created/updated:")
            print(f"     - Database ID: {subscription.id}")
            print(f"     - User: {subscription.user.email}")
            print(f"     - Plan: {subscription.plan.name}")
            print(f"     - Status: {subscription.status}")
            print(f"     - Is Active: {subscription.is_active}")
            print(f"     - Stripe Sub ID: {subscription.stripe_subscription_id}")
            
            # Test the API query
            print(f"\n   Testing API query...")
            api_result = Subscription.objects.filter(
                user=test_user,
                plan__name='bands',
                is_active=True,
                status='active'
            ).exists()
            
            print(f"   API Query Result: has_bands_subscription = {api_result}")
            
            if not api_result:
                print("   🔍 Debugging API query...")
                all_user_bands_subs = Subscription.objects.filter(user=test_user, plan__name='bands')
                for sub in all_user_bands_subs:
                    print(f"     - Found bands sub: Status='{sub.status}', Active={sub.is_active}")
                    print(f"       Matches API query: {sub.is_active and sub.status == 'active'}")
            
        except Exception as e:
            print(f"   ❌ Error in create_or_update_subscription: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n4. Check Webhook URL Configuration:")
    print(f"   Webhook endpoint should be: https://api.gan7club.com/api/payments/webhook/")
    print(f"   Check Stripe dashboard webhook configuration")
    
    print(f"\n5. Test Stripe Webhook Secret:")
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    if webhook_secret:
        print(f"   ✅ Webhook secret loaded: {webhook_secret[:10]}... (length: {len(webhook_secret)})")
    else:
        print(f"   ❌ Webhook secret not loaded!")

if __name__ == "__main__":
    debug_webhook_process()
