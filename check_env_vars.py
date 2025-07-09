#!/usr/bin/env python
"""
Check environment variables
"""

import os
import sys
import django
from pathlib import Path

# Add the talent_platform directory to Python path
project_dir = Path(__file__).resolve().parent / 'talent_platform'
sys.path.insert(0, str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from django.conf import settings

def check_environment_variables():
    """Check if environment variables are loaded correctly"""
    print("=== Checking Environment Variables ===")
    
    # Check Spaces configuration
    print("🔑 Spaces Configuration:")
    print(f"   USE_SPACES: {getattr(settings, 'USE_SPACES', 'Not set')}")
    print(f"   AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID[:10] if settings.AWS_ACCESS_KEY_ID else 'Not set'}...")
    print(f"   AWS_SECRET_ACCESS_KEY: {'*' * 10 if settings.AWS_SECRET_ACCESS_KEY else 'Not set'}...")
    print(f"   AWS_STORAGE_BUCKET_NAME: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"   AWS_S3_ENDPOINT_URL: {settings.AWS_S3_ENDPOINT_URL}")
    print(f"   AWS_S3_CUSTOM_DOMAIN: {getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'Not set')}")
    print(f"   AWS_LOCATION: {getattr(settings, 'AWS_LOCATION', 'Not set')}")
    print(f"   DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
    print(f"   MEDIA_URL: {settings.MEDIA_URL}")
    
    # Check if all required variables are set
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_STORAGE_BUCKET_NAME',
        'AWS_S3_ENDPOINT_URL'
    ]
    
    print(f"\n✅ Required variables check:")
    for var in required_vars:
        value = getattr(settings, var, None)
        status = "✅ Set" if value else "❌ Missing"
        print(f"   {var}: {status}")
    
    # Check storage backend
    print(f"\n🔧 Storage Backend:")
    try:
        from django.core.files.storage import default_storage
        print(f"   Default storage: {default_storage}")
        print(f"   Storage class: {default_storage.__class__}")
        print(f"   Location: {getattr(default_storage, 'location', 'Not set')}")
        print(f"   Bucket: {getattr(default_storage, 'bucket_name', 'Not set')}")
        print(f"   Endpoint: {getattr(default_storage, 'endpoint_url', 'Not set')}")
    except Exception as e:
        print(f"   ❌ Error loading storage: {e}")

if __name__ == "__main__":
    check_environment_variables() 