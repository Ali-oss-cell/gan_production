#!/usr/bin/env python
"""
Debug storage issues
"""

import boto3
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

def debug_bucket_contents():
    """Debug what's actually in the bucket"""
    print("=== Debugging Bucket Contents ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # List all objects
        response = client.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        objects = response.get('Contents', [])
        
        print(f"📁 Total files in bucket: {len(objects)}")
        
        if objects:
            print("\n📋 All files in bucket:")
            for obj in objects:
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"   - {obj['Key']} ({size_mb:.2f} MB)")
                
                # Test direct access
                try:
                    direct_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.fra1.cdn.digitaloceanspaces.com/{obj['Key']}"
                    print(f"     Direct URL: {direct_url}")
                except Exception as e:
                    print(f"     Error generating URL: {e}")
        
        return objects
        
    except Exception as e:
        print(f"❌ Error listing bucket contents: {e}")
        return []

def test_direct_upload():
    """Test direct upload to see the difference"""
    print("\n=== Testing Direct Upload ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # Upload directly to media folder
        test_content = "Direct upload test"
        test_key = "media/direct_test.txt"
        
        client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain',
            ACL='public-read'
        )
        
        print(f"✅ Direct upload successful: {test_key}")
        
        # Test URL
        direct_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.fra1.cdn.digitaloceanspaces.com/{test_key}"
        print(f"🔗 Direct URL: {direct_url}")
        
        import requests
        response = requests.get(direct_url, timeout=10)
        if response.status_code == 200:
            print("✅ Direct upload file is accessible")
        else:
            print(f"⚠️ Direct upload accessibility test failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing direct upload: {e}")
        return False

if __name__ == "__main__":
    debug_bucket_contents()
    test_direct_upload() 