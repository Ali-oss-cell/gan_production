#!/usr/bin/env python3
"""
Simple test to check imports
"""
import sys
import os
import django

# Add the project directory to Python path
sys.path.append('/home/ali/Desktop/projects/gan_production/talent_platform')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

try:
    print("Testing imports...")
    
    # Test basic imports
    from profiles.models import TalentUserProfile
    print("✓ TalentUserProfile imported")
    
    from profiles.talent_profile_serializers import TalentUserProfileSerializer
    print("✓ TalentUserProfileSerializer imported")
    
    # Test the problematic import
    from dashboard.utils import get_sharing_status
    print("✓ get_sharing_status imported")
    
    print("All imports successful!")
    
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
