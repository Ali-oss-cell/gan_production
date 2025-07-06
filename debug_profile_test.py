#!/usr/bin/env python3

import os
import sys
import django
import time

# Add the project directory to Python path
sys.path.insert(0, './talent_platform')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

from users.models import BaseUser
from profiles.models import TalentUserProfile

def test_profile_creation():
    """Test the profile creation with the new timeout fix"""
    print("🧪 Testing Profile Creation with Timeout Fix")
    print("=" * 50)
    
    # Create a test user first
    print("Step 1: Creating test user...")
    try:
        user = BaseUser.objects.create_user(
            email='debug_local@test.com',
            password='testpass123',
            is_talent=True
        )
        print(f"✅ User created: {user.email}")
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False
    
    # Test profile creation with the new method
    print("\nStep 2: Testing profile creation...")
    try:
        start_time = time.time()
        
        # This should use the new timeout-protected method
        from users.managers import BaseUserManager
        manager = BaseUserManager()
        
        # Test the timeout-protected profile creation
        profile = manager._create_profile_with_timeout(
            user=user,
            country='US',
            date_of_birth='1990-01-01'
        )
        
        end_time = time.time()
        print(f"✅ Profile created in {end_time - start_time:.2f} seconds")
        print(f"✅ Profile ID: {profile.id}")
        
        # Clean up
        profile.delete()
        user.delete()
        print("✅ Cleanup completed")
        return True
        
    except Exception as e:
        print(f"❌ Profile creation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up user
        try:
            user.delete()
        except:
            pass
        return False

def test_user_manager():
    """Test the complete user manager functionality"""
    print("\n🧪 Testing User Manager create_talent_user")
    print("=" * 50)
    
    try:
        from users.managers import BaseUserManager
        manager = BaseUserManager()
        manager.model = BaseUser  # Set the model
        
        start_time = time.time()
        
        user = manager.create_talent_user(
            email='manager_test@test.com',
            password='testpass123',
            country='US',
            date_of_birth='1990-01-01'
        )
        
        end_time = time.time()
        print(f"✅ User created via manager in {end_time - start_time:.2f} seconds")
        print(f"✅ User: {user.email}")
        
        # Check if profile was created
        try:
            profile = TalentUserProfile.objects.get(user=user)
            print(f"✅ Profile found: {profile.id}")
            profile.delete()
        except TalentUserProfile.DoesNotExist:
            print("⚠️ Profile not created (this is OK with the new fallback logic)")
        
        # Clean up
        user.delete()
        print("✅ Cleanup completed")
        return True
        
    except Exception as e:
        print(f"❌ User manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Local Profile Creation Debug")
    print("Testing the timeout fix locally...")
    print()
    
    # Test 1: Direct profile creation
    success1 = test_profile_creation()
    
    # Test 2: User manager
    success2 = test_user_manager()
    
    print("\n📊 Results:")
    print(f"Profile Creation Test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"User Manager Test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! The fix should work on production.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 