#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/var/www/gan7club/talent_platform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from payments.models import SubscriptionPlan, Subscription
from users.models import BaseUser
import stripe
from django.conf import settings

def debug_webhook_subscription():
    """Debug the webhook subscription creation issue"""
    
    print("🔍 Debugging webhook subscription creation...")
    
    # Check if user exists
    try:
        user = BaseUser.objects.get(id=64)
        print(f"✅ Found user: {user.email} (ID: {user.id})")
    except BaseUser.DoesNotExist:
        print("❌ User with ID 64 not found")
        return
    
    # Check available subscription plans
    print("\n📋 Available subscription plans:")
    plans = SubscriptionPlan.objects.all()
    for plan in plans:
        print(f"   - {plan.name} (ID: {plan.id}, Stripe Price: {plan.stripe_price_id})")
    
    # Check for 'BANDS' plan specifically
    try:
        bands_plan = SubscriptionPlan.objects.get(name='Bands')
        print(f"✅ Found Bands plan: {bands_plan.name} (Stripe Price: {bands_plan.stripe_price_id})")
    except SubscriptionPlan.DoesNotExist:
        print("❌ Bands plan not found")
        return
    
    # Set up Stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    # Try to retrieve the subscription from Stripe
    subscription_id = "sub_1RzYsjP623EsFG0opBLIgcCc"  # From your webhook data
    
    try:
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        print(f"✅ Retrieved Stripe subscription: {stripe_subscription.id}")
        print(f"   Status: {stripe_subscription.status}")
        print(f"   Customer: {stripe_subscription.customer}")
        
        # Check subscription items
        print(f"   Items: {stripe_subscription.items}")
        if hasattr(stripe_subscription.items, 'data'):
            items_data = stripe_subscription.items.data
            print(f"   Items data: {items_data}")
            if items_data:
                price_id = items_data[0].price.id
                print(f"   Price ID: {price_id}")
                
                # Check if we have a plan with this price ID
                try:
                    plan = SubscriptionPlan.objects.get(stripe_price_id=price_id)
                    print(f"✅ Found matching plan: {plan.name}")
                except SubscriptionPlan.DoesNotExist:
                    print(f"❌ No plan found with Stripe price ID: {price_id}")
                    
                    # Show all plans and their price IDs for comparison
                    print("   Available price IDs:")
                    for p in SubscriptionPlan.objects.all():
                        print(f"     - {p.name}: {p.stripe_price_id}")
        
    except Exception as e:
        print(f"❌ Error retrieving Stripe subscription: {str(e)}")
    
    # Check existing subscriptions for this user
    print(f"\n📊 Existing subscriptions for user {user.email}:")
    existing_subs = Subscription.objects.filter(user=user)
    for sub in existing_subs:
        print(f"   - {sub.plan.name}: {sub.status} (Active: {sub.is_active})")
    
    # Try to simulate the webhook processing
    print(f"\n🔄 Simulating webhook processing...")
    try:
        from payments.payment_services import StripePaymentService
        
        # This should work if everything is set up correctly
        subscription = StripePaymentService.create_or_update_subscription(user, stripe_subscription)
        print(f"✅ Successfully created/updated subscription: {subscription}")
        print(f"   Plan: {subscription.plan.name}")
        print(f"   Status: {subscription.status}")
        print(f"   Is Active: {subscription.is_active}")
        
    except Exception as e:
        print(f"❌ Error in create_or_update_subscription: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_webhook_subscription()
