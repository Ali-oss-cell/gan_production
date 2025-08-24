#!/usr/bin/env python3
"""
Test webhook issues locally to identify the exact problem
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

def test_webhook_issues():
    print("🔍 TESTING WEBHOOK ISSUES LOCALLY")
    print("=" * 50)
    
    from django.conf import settings
    import stripe
    
    print("1. Testing Settings Loading:")
    print(f"   STRIPE_SECRET_KEY: {'SET' if getattr(settings, 'STRIPE_SECRET_KEY', None) else 'NOT SET'}")
    print(f"   STRIPE_WEBHOOK_SECRET: {'SET' if getattr(settings, 'STRIPE_WEBHOOK_SECRET', None) else 'NOT SET'}")
    
    if getattr(settings, 'STRIPE_WEBHOOK_SECRET', None):
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        print(f"   Webhook secret: {webhook_secret[:10]}... (length: {len(webhook_secret)})")
    
    print("\n2. Testing Stripe Library:")
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        print("   ✅ Stripe API key set successfully")
    except Exception as e:
        print(f"   ❌ Stripe API key error: {e}")
    
    print("\n3. Testing Webhook Event Construction:")
    try:
        # Test with a fake but properly formatted signature
        test_payload = '{"test": "data"}'
        test_sig = 't=1234567890,v1=test_signature'  # Properly formatted signature
        
        event = stripe.Webhook.construct_event(
            test_payload,
            test_sig,
            settings.STRIPE_WEBHOOK_SECRET
        )
        print("   ✅ Webhook construction succeeded (unexpected)")
    except stripe.error.SignatureVerificationError as e:
        print(f"   ✅ Signature verification failed as expected: {str(e)}")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
    
    print("\n4. Testing Payment Service Import:")
    try:
        from payments.payment_services import StripePaymentService
        print("   ✅ StripePaymentService imported")
        
        # Test if handle_webhook_event exists
        if hasattr(StripePaymentService, 'handle_webhook_event'):
            print("   ✅ handle_webhook_event method exists")
        else:
            print("   ❌ handle_webhook_event method missing")
            
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n5. Testing Webhook Handler Direct Call:")
    try:
        from payments.views import stripe_webhook
        from django.http import HttpRequest
        
        # Create a minimal test request
        request = HttpRequest()
        request.method = 'POST'
        
        # Test with no signature header
        response = stripe_webhook(request)
        print(f"   ✅ No signature header test: {response.status_code} - {response.content.decode()}")
        
    except Exception as e:
        print(f"   ❌ Webhook handler error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_webhook_issues()
