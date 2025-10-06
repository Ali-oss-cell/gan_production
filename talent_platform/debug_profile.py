#!/usr/bin/env python3
"""
Debug script to test the talent profile API endpoint
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ali/Desktop/projects/gan_production/talent_platform')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from users.models import BaseUser
from profiles.models import TalentUserProfile
from profiles.talent_profile_serializers import TalentUserProfileSerializer

def test_profile_serialization():
    try:
        print("=== Testing Profile Serialization ===")
        
        # Get a user
        user = BaseUser.objects.get(id=325)
        print(f"✓ User found: {user.email}")
        
        # Get the talent profile
        profile = TalentUserProfile.objects.get(user=user)
        print(f"✓ Profile found: {profile.id}")
        
        # Test individual methods
        print("\n=== Testing Individual Methods ===")
        
        # Test residency field
        try:
            residency = getattr(user, 'residency', '')
            print(f"✓ Residency field: '{residency}'")
        except Exception as e:
            print(f"✗ Residency error: {e}")
        
        # Test profile score
        try:
            score = profile.get_profile_score()
            print(f"✓ Profile score: {score}")
        except Exception as e:
            print(f"✗ Profile score error: {e}")
        
        # Test upgrade benefits
        try:
            benefits = profile.get_upgrade_benefits()
            print(f"✓ Upgrade benefits: {benefits}")
        except Exception as e:
            print(f"✗ Upgrade benefits error: {e}")
        
        # Test account limitations
        try:
            limitations = {
                'images_used': profile.media.filter(media_type='image').count(),
                'videos_used': profile.media.filter(media_type='video').count(),
                'images_limit': profile.get_image_limit(),
                'videos_limit': profile.get_video_limit(),
            }
            print(f"✓ Account limitations: {limitations}")
        except Exception as e:
            print(f"✗ Account limitations error: {e}")
        
        # Test the full serializer
        print("\n=== Testing Full Serializer ===")
        try:
            serializer = TalentUserProfileSerializer(profile)
            data = serializer.data
            print(f"✓ Serializer successful! Keys: {list(data.keys())}")
            print(f"✓ Residency in data: {data.get('residency', 'NOT_FOUND')}")
        except Exception as e:
            print(f"✗ Serializer error: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ General error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_profile_serialization()
