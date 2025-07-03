#!/usr/bin/env python3
"""
Test script to demonstrate country code to full name conversion and database storage
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
from users.models import BaseUser
from profiles.models import TalentUserProfile, BackGroundJobsProfile

def test_country_storage():
    """Test country code to full name conversion and database storage"""
    print("💾 Testing Country Code to Full Name Storage")
    print("=" * 60)
    
    # Test country code to name conversion
    print("\n1. Country Code to Full Name Conversion:")
    test_codes = [
        ('ae', 'United Arab Emirates'),
        ('us', 'United States'),
        ('gb', 'United Kingdom'),
        ('sa', 'Saudi Arabia'),
        ('cn', 'China'),
        ('in', 'India'),
        ('br', 'Brazil'),
        ('de', 'Germany'),
        ('fr', 'France'),
        ('kw', 'Kuwait'),
        ('qa', 'Qatar'),
    ]
    
    for code, expected_name in test_codes:
        actual_name = CountryDetectionService.get_country_name_from_code(code)
        status = "✅" if actual_name == expected_name else "❌"
        print(f"   {status} {code.upper()} -> {actual_name} (expected: {expected_name})")
    
    # Test database storage
    print("\n2. Database Storage Test:")
    
    # Create test user
    test_email = "test_country_storage@example.com"
    user, created = BaseUser.objects.get_or_create(
        email=test_email,
        defaults={
            'first_name': 'Test',
            'last_name': 'Country',
            'is_talent': True,
            'is_background': False
        }
    )
    
    # Create talent profile
    profile, created = TalentUserProfile.objects.get_or_create(
        user=user,
        defaults={'country': 'country'}  # Default value
    )
    
    print(f"   Created test user: {user.email}")
    print(f"   Initial country in database: '{profile.country}'")
    
    # Test saving different country codes
    test_countries = ['ae', 'us', 'sa', 'gb']
    
    for country_code in test_countries:
        # Save country to profile
        success = CountryDetectionService.save_country_to_user_profile(user, country_code)
        
        # Refresh from database
        profile.refresh_from_db()
        
        country_name = CountryDetectionService.get_country_name_from_code(country_code)
        
        print(f"   📝 Saved '{country_code}' -> '{country_name}' to database: {'✅' if success else '❌'}")
        print(f"      Database now contains: '{profile.country}'")
    
    print("\n3. Complete Flow Example:")
    print("   Frontend sends: 'ae'")
    print("   Backend converts: 'ae' -> 'United Arab Emirates'")
    print("   Database stores: 'United Arab Emirates'")
    print("   Payment methods: ['card', 'apple_pay', 'google_pay', 'paypal', 'mada', 'unionpay']")
    
    print("\n" + "=" * 60)
    print("✅ Country Storage Test Complete!")

if __name__ == "__main__":
    test_country_storage() 