#!/usr/bin/env python3
"""
Test script to verify country detection for payment methods
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from payments.utils import CountryDetectionService
from payments.services import StripePaymentService
from users.models import BaseUser
from profiles.models import TalentUserProfile, BackGroundJobsProfile

def test_country_detection():
    """Test country detection functionality"""
    print("🌍 Testing Country Detection for Payment Methods")
    print("=" * 60)
    
    # Test country code mapping
    print("\n1. Country Code Mapping Tests:")
    test_countries = [
        ('UAE', 'ae'),
        ('United States', 'us'),
        ('USA', 'us'),
        ('United Kingdom', 'gb'),
        ('UK', 'gb'),
        ('Canada', 'ca'),
        ('Australia', 'au'),
        ('Germany', 'de'),
        ('France', 'fr'),
        ('Saudi Arabia', 'sa'),
        ('China', 'cn'),
        ('India', 'in'),
        ('Brazil', 'br'),
        ('South Africa', 'za'),
    ]
    
    for country_name, expected_code in test_countries:
        detected = CountryDetectionService._normalize_country_code(country_name)
        status = "✅" if detected == expected_code else "❌"
        print(f"   {status} {country_name} -> {detected} (expected: {expected_code})")
    
    # Test payment methods for different regions
    print("\n2. Payment Methods by Region:")
    test_regions = ['ae', 'us', 'gb', 'ca', 'au', 'de', 'fr', 'sa', 'cn', 'in']
    
    for region in test_regions:
        methods = StripePaymentService.get_payment_methods_for_region(region)
        print(f"   {region.upper()}: {methods}")
    
    # Test with sample user profiles
    print("\n3. User Profile Country Detection:")
    
    # Create test users with different countries
    test_users = [
        ('test_uae@example.com', 'UAE', 'talent'),
        ('test_us@example.com', 'United States', 'talent'),
        ('test_uk@example.com', 'United Kingdom', 'background'),
        ('test_sa@example.com', 'Saudi Arabia', 'talent'),
    ]
    
    for email, country, profile_type in test_users:
        try:
            # Create or get user
            user, created = BaseUser.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': 'Test',
                    'last_name': 'User',
                    'is_talent': profile_type == 'talent',
                    'is_background': profile_type == 'background'
                }
            )
            
            # Create profile with country
            if profile_type == 'talent':
                profile, created = TalentUserProfile.objects.get_or_create(
                    user=user,
                    defaults={'country': country}
                )
                if not created:
                    profile.country = country
                    profile.save()
            else:
                profile, created = BackGroundJobsProfile.objects.get_or_create(
                    user=user,
                    defaults={'country': country}
                )
                if not created:
                    profile.country = country
                    profile.save()
            
            # Test country detection
            detected_country = CountryDetectionService.get_user_country(user)
            payment_methods = StripePaymentService.get_payment_methods_for_region(detected_country)
            
            print(f"   {email}:")
            print(f"      Profile Country: {country}")
            print(f"      Detected Country: {detected_country}")
            print(f"      Payment Methods: {payment_methods}")
            
        except Exception as e:
            print(f"   ❌ Error testing {email}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Country Detection Test Complete!")

if __name__ == "__main__":
    test_country_detection() 