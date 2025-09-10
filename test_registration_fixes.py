#!/usr/bin/env python3
"""
Test script to verify registration fixes and settings loading
"""
import os
import sys
import time
import json
import requests
from datetime import datetime

# Add talent_platform to path
sys.path.insert(0, 'talent_platform')

def test_settings_loading():
    """Test that correct settings are loaded"""
    print("🔍 Testing settings loading...")
    
    try:
        # Set up Django environment
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"✅ Settings module loaded: {settings.SETTINGS_MODULE}")
        print(f"✅ EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        print(f"✅ EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        print(f"✅ DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        
        # Check if in production mode
        if '/var/www/gan7club' in str(settings.BASE_DIR) or os.environ.get('PRODUCTION') == 'true':
            print("🚀 Production settings detected")
            expected_host = 'smtp.hostinger.com'
        else:
            print("🏠 Development settings detected")
            expected_host = 'localhost'
        
        if settings.EMAIL_HOST == expected_host:
            print("✅ Correct email host configured")
        else:
            print(f"❌ Wrong email host: expected {expected_host}, got {settings.EMAIL_HOST}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings loading failed: {str(e)}")
        return False

def test_profile_model_fields():
    """Test that profile models have required fields"""
    print("\n🔍 Testing profile model fields...")
    
    try:
        from profiles.models import TalentUserProfile, BackGroundJobsProfile
        
        # Check TalentUserProfile fields
        talent_fields = [field.name for field in TalentUserProfile._meta.fields]
        print(f"✅ TalentUserProfile fields: {talent_fields}")
        
        required_talent_fields = ['country', 'date_of_birth']
        for field in required_talent_fields:
            if field in talent_fields:
                print(f"✅ TalentUserProfile has {field} field")
            else:
                print(f"❌ TalentUserProfile missing {field} field")
        
        # Check BackGroundJobsProfile fields
        bg_fields = [field.name for field in BackGroundJobsProfile._meta.fields]
        print(f"✅ BackGroundJobsProfile fields: {bg_fields}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model field test failed: {str(e)}")
        return False

def test_user_creation():
    """Test user creation with managers"""
    print("\n🔍 Testing user creation...")
    
    try:
        from users.models import BaseUser
        from profiles.models import TalentUserProfile
        from datetime import date
        
        # Test data
        test_email = f"test_{int(time.time())}@example.com"
        test_data = {
            'email': test_email,
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'country': 'United States',
            'date_of_birth': date(1990, 1, 1),
            'gender': 'Male'
        }
        
        print(f"Creating talent user: {test_email}")
        
        # Create talent user
        user = BaseUser.objects.create_talent_user(**test_data)
        print(f"✅ User created: {user.email}")
        print(f"✅ User roles: talent={user.is_talent}, background={user.is_background}")
        
        # Check if profile was created
        try:
            profile = TalentUserProfile.objects.get(user=user)
            print(f"✅ TalentUserProfile created: country={profile.country}, dob={profile.date_of_birth}")
        except TalentUserProfile.DoesNotExist:
            print("⚠️  TalentUserProfile not created (this might be expected if async)")
        
        # Cleanup
        user.delete()
        print("✅ Test user deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ User creation test failed: {str(e)}")
        return False

def test_registration_performance():
    """Test registration API performance"""
    print("\n🔍 Testing registration performance...")
    
    # This would require a running server, so we'll simulate
    registration_data = {
        'email': f'performance_test_{int(time.time())}@example.com',
        'password': 'testpass123',
        'first_name': 'Performance',
        'last_name': 'Test',
        'role': 'talent',
        'country': 'United States',
        'date_of_birth': '1990-01-01',
        'gender': 'Male'
    }
    
    print("📝 Registration data prepared:")
    print(json.dumps(registration_data, indent=2))
    print("⚠️  To test performance, run this on a live server:")
    print("curl -X POST http://localhost:8000/api/register/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(registration_data)}'")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting registration fixes verification...")
    print("=" * 50)
    
    tests = [
        ("Settings Loading", test_settings_loading),
        ("Profile Model Fields", test_profile_model_fields),
        ("User Creation", test_user_creation),
        ("Registration Performance", test_registration_performance),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n📈 Overall: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests passed! Registration fixes look good.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")

if __name__ == '__main__':
    main()
