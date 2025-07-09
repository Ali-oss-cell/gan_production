#!/usr/bin/env python
"""
Comprehensive DigitalOcean Spaces Test Script
Tests configuration, bucket access, file listing, and upload functionality
"""

import boto3
import os
import sys
import django
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError
import requests

# Add the talent_platform directory to Python path
project_dir = Path(__file__).resolve().parent / 'talent_platform'
sys.path.insert(0, str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from django.conf import settings

def test_spaces_connection():
    """Test basic connection to DigitalOcean Spaces"""
    print("=== Testing DigitalOcean Spaces Connection ===")
    
    try:
        # Get credentials from Django settings
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        
        print(f"🔑 Access Key: {access_key[:10]}..." if access_key else "❌ No access key")
        print(f"🔑 Secret Key: {'*' * 10}..." if secret_key else "❌ No secret key")
        print(f"🪣 Bucket Name: {bucket_name}")
        print(f"🌐 Endpoint URL: {endpoint_url}")
        
        if not all([access_key, secret_key, bucket_name, endpoint_url]):
            print("❌ Missing required credentials")
            return False
        
        # Create session and client
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=endpoint_url,
                               aws_access_key_id=access_key,
                               aws_secret_access_key=secret_key)
        
        # Test bucket access
        response = client.head_bucket(Bucket=bucket_name)
        print(f"✅ Successfully connected to bucket: {bucket_name}")
        
        # Get bucket location
        location = client.get_bucket_location(Bucket=bucket_name)
        print(f"📍 Bucket location: {location.get('LocationConstraint', 'us-east-1')}")
        
        return True
        
    except NoCredentialsError:
        print("❌ No credentials found")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Bucket '{bucket_name}' does not exist")
        elif error_code == 'AccessDenied':
            print(f"❌ Access denied to bucket '{bucket_name}'")
        else:
            print(f"❌ Error: {error_code} - {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def list_bucket_contents():
    """List all files in the bucket"""
    print("\n=== Listing Bucket Contents ===")
    
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
            print("\n📋 Files in bucket:")
            for obj in objects:
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"   - {obj['Key']} ({size_mb:.2f} MB)")
        else:
            print("📭 Bucket is empty")
        
        # Check media folder specifically
        media_response = client.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME, 
            Prefix='media/'
        )
        media_objects = media_response.get('Contents', [])
        print(f"\n📁 Files in media folder: {len(media_objects)}")
        
        if media_objects:
            print("📋 Media files:")
            for obj in media_objects:
                size_mb = obj['Size'] / (1024 * 1024)
                print(f"   - {obj['Key']} ({size_mb:.2f} MB)")
        
        return objects
        
    except Exception as e:
        print(f"❌ Error listing bucket contents: {e}")
        return []

def test_file_upload():
    """Test uploading a small test file"""
    print("\n=== Testing File Upload ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # Create a test file
        test_content = "This is a test file for DigitalOcean Spaces upload"
        test_key = "media/test_upload.txt"
        
        # Upload the file
        client.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain',
            ACL='public-read'
        )
        
        print(f"✅ Successfully uploaded: {test_key}")
        
        # Generate URL
        if settings.AWS_S3_CUSTOM_DOMAIN:
            url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{test_key}"
        else:
            url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.fra1.cdn.digitaloceanspaces.com/{test_key}"
        
        print(f"🔗 File URL: {url}")
        
        # Test URL accessibility
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print("✅ File is publicly accessible")
        else:
            print(f"⚠️ File accessibility test failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing upload: {e}")
        return False

def test_django_storage():
    """Test Django's storage backend"""
    print("\n=== Testing Django Storage Backend ===")
    
    try:
        from django.core.files.base import ContentFile
        from django.core.files.storage import default_storage
        
        # Test file content
        test_content = "Django storage test file"
        test_filename = "django_test.txt"
        
        # Save file using Django storage
        saved_path = default_storage.save(f"media/{test_filename}", ContentFile(test_content))
        print(f"✅ Django storage saved: {saved_path}")
        
        # Get URL
        file_url = default_storage.url(saved_path)
        print(f"🔗 Django storage URL: {file_url}")
        
        # Test URL accessibility
        response = requests.get(file_url, timeout=10)
        if response.status_code == 200:
            print("✅ Django storage file is accessible")
        else:
            print(f"⚠️ Django storage accessibility test failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Django storage: {e}")
        return False

def check_cors_configuration():
    """Check CORS configuration for the bucket"""
    print("\n=== Checking CORS Configuration ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # Get CORS configuration
        response = client.get_bucket_cors(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        cors_rules = response.get('CORSRules', [])
        
        print(f"📋 Found {len(cors_rules)} CORS rules:")
        
        for i, rule in enumerate(cors_rules, 1):
            print(f"\n   Rule {i}:")
            print(f"     Allowed Origins: {rule.get('AllowedOrigins', [])}")
            print(f"     Allowed Methods: {rule.get('AllowedMethods', [])}")
            print(f"     Allowed Headers: {rule.get('AllowedHeaders', [])}")
            print(f"     Max Age: {rule.get('MaxAgeSeconds', 'Not set')}")
        
        return cors_rules
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
            print("⚠️ No CORS configuration found")
        else:
            print(f"❌ Error checking CORS: {e}")
        return []
    except Exception as e:
        print(f"❌ Error checking CORS: {e}")
        return []

def check_bucket_policy():
    """Check bucket policy"""
    print("\n=== Checking Bucket Policy ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # Get bucket policy
        response = client.get_bucket_policy(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        policy = response.get('Policy', '')
        
        print("📋 Bucket policy found:")
        print(policy)
        
        return policy
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
            print("⚠️ No bucket policy found")
        else:
            print(f"❌ Error checking bucket policy: {e}")
        return None
    except Exception as e:
        print(f"❌ Error checking bucket policy: {e}")
        return None

def main():
    """Run all tests"""
    print("🚀 DigitalOcean Spaces Comprehensive Test")
    print("=" * 50)
    
    # Test 1: Connection
    if not test_spaces_connection():
        print("\n❌ Connection test failed. Stopping.")
        return
    
    # Test 2: List contents
    list_bucket_contents()
    
    # Test 3: File upload
    test_file_upload()
    
    # Test 4: Django storage
    test_django_storage()
    
    # Test 5: CORS configuration
    check_cors_configuration()
    
    # Test 6: Bucket policy
    check_bucket_policy()
    
    print("\n" + "=" * 50)
    print("✅ Comprehensive test completed!")

if __name__ == "__main__":
    main() 