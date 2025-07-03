#!/usr/bin/env python3
"""
Test script to verify UAE payment methods configuration
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from payments.payment_methods_config import PAYMENT_METHODS_CONFIG, REGIONAL_PREFERENCES
from payments.services import StripePaymentService

def test_uae_payment_methods():
    """Test UAE payment methods configuration"""
    print("🇦🇪 Testing UAE Payment Methods Configuration")
    print("=" * 50)
    
    # Test regional preferences
    print("\n1. Regional Preferences:")
    uae_methods = REGIONAL_PREFERENCES.get('ae', [])
    print(f"   UAE methods: {uae_methods}")
    
    # Test payment method types
    print("\n2. Payment Method Types:")
    stripe_methods = StripePaymentService.get_payment_methods_for_region('ae')
    print(f"   Stripe methods for UAE: {stripe_methods}")
    
    # Test individual payment methods
    print("\n3. Individual Payment Methods:")
    for method in uae_methods:
        if method in PAYMENT_METHODS_CONFIG:
            config = PAYMENT_METHODS_CONFIG[method]
            print(f"   ✅ {method.upper()}:")
            print(f"      - Name: {config['name']}")
            print(f"      - Stripe Type: {config['stripe_type']}")
            print(f"      - Processing Fee: {config['processing_fee']}%")
            print(f"      - Fixed Fee: ${config['fixed_fee']}")
            print(f"      - Description: {config['description']}")
        else:
            print(f"   ❌ {method.upper()}: Not configured")
    
    # Test other regions
    print("\n4. Other Regions:")
    for region in ['us', 'eu', 'uk', 'sa']:
        methods = StripePaymentService.get_payment_methods_for_region(region)
        print(f"   {region.upper()}: {methods}")
    
    print("\n" + "=" * 50)
    print("✅ UAE Payment Methods Test Complete!")

if __name__ == "__main__":
    test_uae_payment_methods() 