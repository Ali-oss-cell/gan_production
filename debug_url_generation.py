#!/usr/bin/env python
"""
Debug URL generation issues
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

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import boto3

def debug_url_generation():
    """Debug URL generation step by step"""
    print("=== Debugging URL Generation ===")
    
    try:
        # Test 1: Save a file and check the path
        test_content = "URL debug test"
        test_filename = "url_debug_test.txt"
        
        print(f"📝 Saving file: {test_filename}")
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        print(f"✅ Saved path: {saved_path}")
        
        # Test 2: Check what Django thinks the URL should be
        django_url = default_storage.url(saved_path)
        print(f"🔗 Django generated URL: {django_url}")
        
        # Test 3: Check what the actual URL should be
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        location = getattr(default_storage, 'location', 'media')
        custom_domain = getattr(default_storage, 'custom_domain', None)
        
        print(f"\n📋 Storage configuration:")
        print(f"   Bucket: {bucket_name}")
        print(f"   Location: {location}")
        print(f"   Custom domain: {custom_domain}")
        print(f"   Saved path: {saved_path}")
        
        # Test 4: Generate expected URL
        if custom_domain:
            expected_url = f"https://{custom_domain}/{location}/{saved_path}"
        else:
            expected_url = f"https://{bucket_name}.fra1.cdn.digitaloceanspaces.com/{location}/{saved_path}"
        
        print(f"🔗 Expected URL: {expected_url}")
        
        # Test 5: Check if file actually exists in bucket
        print(f"\n🔍 Checking bucket for file...")
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # List all objects
        response = client.list_objects_v2(Bucket=bucket_name)
        objects = response.get('Contents', [])
        
        print(f"📁 Total files in bucket: {len(objects)}")
        for obj in objects:
            print(f"   - {obj['Key']}")
        
        # Test 6: Check if our file is in the bucket
        file_in_bucket = any(obj['Key'] == saved_path for obj in objects)
        print(f"📁 Our file in bucket: {file_in_bucket}")
        
        # Test 7: Try to access the file directly
        if file_in_bucket:
            try:
                import requests
                direct_url = f"https://{bucket_name}.fra1.cdn.digitaloceanspaces.com/{saved_path}"
                print(f"🔍 Testing direct access: {direct_url}")
                response = requests.get(direct_url, timeout=10)
                print(f"📡 Direct access status: {response.status_code}")
                if response.status_code == 200:
                    print(f"📄 Content: {response.text[:50]}...")
            except Exception as e:
                print(f"❌ Direct access error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_backend_directly():
    """Test the storage backend directly"""
    print("\n=== Testing Storage Backend Directly ===")
    
    try:
        from talent_platform.storage_backends import MediaStorage
        
        # Create storage instance
        storage = MediaStorage()
        print(f"📋 Storage instance created")
        print(f"   Location: {storage.location}")
        print(f"   Custom domain: {storage.custom_domain}")
        print(f"   Endpoint URL: {getattr(storage, 'endpoint_url', 'Not set')}")
        
        # Test URL generation
        test_path = "test_url_generation.txt"
        url = storage.url(test_path)
        print(f"🔗 Generated URL for '{test_path}': {url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_url_generation()
    test_storage_backend_directly() 