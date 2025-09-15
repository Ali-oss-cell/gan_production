#!/usr/bin/env python3
"""
Quick debug script to check a specific user's talent status
Usage: python debug_user_status.py user@example.com
"""
import os
import sys
import django

# Setup Django
if os.path.exists('/var/www/gan7club'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')

django.setup()

from users.models import BaseUser
from profiles.models import TalentUserProfile

def check_user_status(email):
    """Check a specific user's talent status"""
    try:
        user = BaseUser.objects.get(email=email)
        print(f"🔍 User: {user.email}")
        print(f"   - is_talent: {user.is_talent}")
        print(f"   - is_background: {user.is_background}")
        print(f"   - is_dashboard: {user.is_dashboard}")
        print(f"   - is_active: {user.is_active}")
        print(f"   - email_verified: {user.email_verified}")
        
        # Check if they have a talent profile
        try:
            profile = TalentUserProfile.objects.get(user=user)
            print(f"   - Has TalentUserProfile: ✅ (ID: {profile.id})")
            print(f"   - Profile complete: {profile.profile_complete}")
            print(f"   - Account type: {profile.account_type}")
        except TalentUserProfile.DoesNotExist:
            print(f"   - Has TalentUserProfile: ❌")
        
        # Fix the user if needed
        if not user.is_talent:
            print(f"\n🔧 FIXING: Setting is_talent=True for {user.email}")
            user.is_talent = True
            user.save(update_fields=['is_talent'])
            print(f"   ✅ Fixed: is_talent is now {user.is_talent}")
            
            # Create talent profile if missing
            try:
                profile = TalentUserProfile.objects.get(user=user)
            except TalentUserProfile.DoesNotExist:
                print(f"🔧 Creating missing TalentUserProfile...")
                profile = TalentUserProfile.objects.create(
                    user=user,
                    country=user.country or '',
                    date_of_birth=user.date_of_birth
                )
                print(f"   ✅ Created TalentUserProfile (ID: {profile.id})")
        else:
            print(f"   ✅ User already has is_talent=True")
        
        return user
        
    except BaseUser.DoesNotExist:
        print(f"❌ User not found: {email}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_user_status.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"🚀 Checking user status for: {email}")
    print("=" * 50)
    
    user = check_user_status(email)
    
    if user:
        print("\n" + "=" * 50)
        print("✅ User check completed!")
        print("Now try logging in again.")

if __name__ == '__main__':
    main()
