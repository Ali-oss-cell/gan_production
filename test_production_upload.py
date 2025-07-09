#!/usr/bin/env python
"""
Test production upload workflow
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
import requests

def test_production_upload():
    """Test upload that will work in production"""
    print("=== Testing Production Upload ===")
    
    try:
        # Test 1: Create a test file
        test_content = "Production upload test file"
        test_filename = "production_test.txt"
        
        print(f"📝 Creating test file: {test_filename}")
        
        # Test 2: Save using Django storage
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        print(f"✅ File saved as: {saved_path}")
        
        # Test 3: Get the URL
        file_url = default_storage.url(saved_path)
        print(f"🔗 Generated URL: {file_url}")
        
        # Test 4: Check if file exists in storage
        exists = default_storage.exists(saved_path)
        print(f"📁 File exists in storage: {exists}")
        
        # Test 5: Check bucket contents
        print(f"\n🔍 Checking bucket contents...")
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        response = client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        objects = response.get('Contents', [])
        
        print(f"📁 Total files in bucket: {len(objects)}")
        for obj in objects:
            print(f"   - {obj['Key']}")
        
        # Test 6: Check if our file is in the bucket
        file_in_bucket = any(obj['Key'] == saved_path for obj in objects)
        print(f"📁 Our file in bucket: {file_in_bucket}")
        
        if file_in_bucket:
            print("✅ SUCCESS: File uploaded to Spaces!")
            
            # Test 7: Try to access the file
            try:
                response = requests.get(file_url, timeout=10)
                if response.status_code == 200:
                    print("✅ File is publicly accessible!")
                    print(f"📄 Content: {response.text[:50]}...")
                else:
                    print(f"⚠️ File not accessible: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Could not test file access: {e}")
        else:
            print("❌ File not found in bucket - check storage configuration")
        
        return file_in_bucket
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_media_model_upload():
    """Test upload through Django model (simplified)"""
    print("\n=== Testing Media Model Upload ===")
    
    try:
        from profiles.models import TalentMedia
        
        # Create a simple test without requiring talent relationship
        test_content = "Model upload test content"
        test_filename = "model_upload_test.txt"
        
        # Create a temporary file to test
        temp_file = ContentFile(test_content)
        temp_file.name = test_filename
        
        # Test the file field directly
        print(f"📝 Testing file field with: {test_filename}")
        
        # This would normally be done through a form or serializer
        # For testing, we'll just verify the storage works
        saved_path = default_storage.save(f"media/{test_filename}", temp_file)
        print(f"✅ Model file saved as: {saved_path}")
        
        # Get URL
        file_url = default_storage.url(saved_path)
        print(f"🔗 Model file URL: {file_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in model upload test: {e}")
        return False

def show_upload_instructions():
    """Show instructions for testing uploads"""
    print("\n" + "=" * 60)
    print("📋 UPLOAD TESTING INSTRUCTIONS")
    print("=" * 60)
    print("1. Run this script to test basic upload functionality")
    print("2. Check if files appear in your Spaces bucket")
    print("3. Test file accessibility via generated URLs")
    print("4. If successful, push to production and test there")
    print("\n🔧 To test in production:")
    print("   - Deploy your code")
    print("   - Run: python test_production_upload.py")
    print("   - Check Spaces bucket for uploaded files")
    print("\n🌐 Your Spaces bucket: ganspace")
    print("🔗 CDN URL: https://ganspace.fra1.cdn.digitaloceanspaces.com/")

if __name__ == "__main__":
    show_upload_instructions()
    test_production_upload()
    test_media_model_upload() 