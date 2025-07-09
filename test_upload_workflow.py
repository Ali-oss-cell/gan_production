#!/usr/bin/env python
"""
Test the complete upload workflow
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

def test_complete_workflow():
    """Test the complete upload workflow"""
    print("=== Testing Complete Upload Workflow ===")
    
    try:
        # Step 1: Test Django storage save
        test_content = "Complete workflow test file"
        test_filename = "workflow_test.txt"
        
        print(f"📝 Saving file: {test_filename}")
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        print(f"✅ Django storage saved: {saved_path}")
        
        # Step 2: Get URL
        file_url = default_storage.url(saved_path)
        print(f"🔗 Django storage URL: {file_url}")
        
        # Step 3: Check if file exists in bucket
        print("\n🔍 Checking bucket contents...")
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
        
        # Step 4: Test URL accessibility
        print(f"\n🌐 Testing URL accessibility: {file_url}")
        response = requests.get(file_url, timeout=10)
        if response.status_code == 200:
            print("✅ File is accessible via URL")
            print(f"📄 Content: {response.text[:50]}...")
        else:
            print(f"❌ File not accessible: {response.status_code}")
            
            # Try direct URL
            direct_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.fra1.cdn.digitaloceanspaces.com/{saved_path}"
            print(f"🔍 Trying direct URL: {direct_url}")
            response = requests.get(direct_url, timeout=10)
            if response.status_code == 200:
                print("✅ File accessible via direct URL")
            else:
                print(f"❌ Direct URL also failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_media_model_upload():
    """Test upload through Django model"""
    print("\n=== Testing Media Model Upload ===")
    
    try:
        from profiles.models import TalentMedia
        
        # Create a test media object
        media = TalentMedia()
        test_content = "Model upload test file"
        test_filename = "model_test.txt"
        
        # Save file to media object
        media.media_file.save(test_filename, ContentFile(test_content), save=True)
        print(f"✅ Model upload successful: {media.media_file.name}")
        print(f"🔗 Model URL: {media.media_file.url}")
        
        # Test URL accessibility
        response = requests.get(media.media_file.url, timeout=10)
        if response.status_code == 200:
            print("✅ Model file is accessible")
        else:
            print(f"❌ Model file not accessible: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in model upload test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_complete_workflow()
    test_media_model_upload() 