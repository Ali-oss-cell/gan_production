#!/usr/bin/env python3
"""
Debug Stripe Checkout
"""
import os
import django

# Setup Django with production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from django.conf import settings
import stripe
from payments.pricing_config import SUBSCRIPTION_PLANS

def debug_stripe_checkout():
    """Debug the Stripe checkout issue"""
    print("🔍 DEBUGGING STRIPE CHECKOUT")
    print("=" * 50)
    
    try:
        # Check Stripe key
        stripe_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
        print(f"✅ STRIPE_SECRET_KEY: {stripe_key[:20] if stripe_key else 'Not set'}...")
        
        if not stripe_key:
            print("❌ Stripe key not found!")
            return False
        
        # Test Stripe connection
        stripe.api_key = stripe_key
        try:
            account = stripe.Account.retrieve()
            print(f"✅ Stripe connection: {account.id}")
        except Exception as e:
            print(f"❌ Stripe connection failed: {e}")
            return False
        
        # Check plan configuration
        print(f"✅ Available plans: {list(SUBSCRIPTION_PLANS.keys())}")
        
        # Test specific plan
        plan_id = 'SILVER'
        if plan_id in SUBSCRIPTION_PLANS:
            plan = SUBSCRIPTION_PLANS[plan_id]
            print(f"✅ Plan {plan_id}: {plan['name']} - ${plan['price']}")
            print(f"✅ Stripe price ID: {plan['stripe_price_id']}")
            
            # Test creating checkout session
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': plan['stripe_price_id'],
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url='https://gan7club.com/success',
                    cancel_url='https://gan7club.com/cancel',
                    customer_email='test@example.com',
                    metadata={
                        'user_id': '1',
                        'plan_id': plan_id
                    }
                )
                print(f"✅ Checkout session created: {session.id}")
                print(f"✅ Checkout URL: {session.url}")
                return True
                
            except stripe.error.InvalidRequestError as e:
                print(f"❌ Stripe API error: {e}")
                return False
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                return False
        else:
            print(f"❌ Plan {plan_id} not found!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    debug_stripe_checkout() 