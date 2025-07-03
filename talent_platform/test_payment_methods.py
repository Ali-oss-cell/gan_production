#!/usr/bin/env python
"""
Test script to check payment methods configuration
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from payments.services import StripePaymentService
from payments.payment_methods_config import REGIONAL_PREFERENCES, PAYMENT_METHODS_CONFIG

def test_payment_methods():
    """Test payment methods for different regions"""
    print("=== Payment Methods Configuration Test ===\n")
    
    # Test UAE region
    print("1. Testing UAE (ae) region:")
    uae_methods = StripePaymentService.get_payment_methods_for_region('ae')
    print(f"   Final payment methods: {uae_methods}\n")
    
    # Test Saudi Arabia region
    print("2. Testing Saudi Arabia (sa) region:")
    sa_methods = StripePaymentService.get_payment_methods_for_region('sa')
    print(f"   Final payment methods: {sa_methods}\n")
    
    # Test US region
    print("3. Testing US region:")
    us_methods = StripePaymentService.get_payment_methods_for_region('us')
    print(f"   Final payment methods: {us_methods}\n")
    
    # Test global region
    print("4. Testing global region:")
    global_methods = StripePaymentService.get_payment_methods_for_region('global')
    print(f"   Final payment methods: {global_methods}\n")
    
    # Show regional preferences
    print("5. Regional Preferences Configuration:")
    for region, methods in REGIONAL_PREFERENCES.items():
        print(f"   {region}: {methods}")
    
    print("\n6. Payment Methods Configuration:")
    for method, config in PAYMENT_METHODS_CONFIG.items():
        stripe_type = config.get('stripe_type', 'unknown')
        print(f"   {method} -> {stripe_type}")

if __name__ == "__main__":
    test_payment_methods() 