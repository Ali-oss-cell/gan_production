#!/usr/bin/env python3
"""
Debug script to test DigitalOcean Spaces upload functionality
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')

# Initialize Django
django.setup()

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_storage_configuration():
    """Test storage configuration and connectivity"""
    print("🔧 STORAGE CONFIGURATION TEST")
    print("=" * 50)
    
    # Check if Spaces is enabled
    print(f"USE_SPACES: {getattr(settings, 'USE_SPACES', False)}")
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
    
    # Check AWS/Spaces settings
    print(f"AWS_ACCESS_KEY_ID: {'Set' if getattr(settings, 'AWS_ACCESS_KEY_ID', None) else 'Not set'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'Set' if getattr(settings, 'AWS_SECRET_ACCESS_KEY', None) else 'Not set'}")
    print(f"AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
    print(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Not set')}")
    print(f"AWS_S3_CUSTOM_DOMAIN: {getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', 'Not set')}")
    print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
    
    # Check if we're using the custom storage backend
    storage_class = default_storage.__class__.__name__
    print(f"Current storage class: {storage_class}")
    
    return True

def test_spaces_connectivity():
    """Test direct connection to DigitalOcean Spaces"""
    print("\n🌐 SPACES CONNECTIVITY TEST")
    print("=" * 50)
    
    try:
        # Create S3 client for Spaces
        session = boto3.session.Session()
        client = session.client('s3',
                              region_name='fra1',
                              endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL'),
                              aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY'))
        
        # Test bucket access
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME')
        print(f"Testing connection to bucket: {bucket_name}")
        
        response = client.head_bucket(Bucket=bucket_name)
        print("✅ Successfully connected to Spaces bucket")
        
        # List objects in bucket
        response = client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
        objects = response.get('Contents', [])
        print(f"📁 Found {len(objects)} objects in bucket:")
        for obj in objects:
            print(f"   - {obj['Key']}")
        
        return True
        
    except NoCredentialsError:
        print("❌ No credentials found")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print("❌ Bucket not found")
        elif error_code == '403':
            print("❌ Access denied to bucket")
        else:
            print(f"❌ Error: {error_code}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_django_storage_upload():
    """Test Django storage upload functionality"""
    print("\n📤 DJANGO STORAGE UPLOAD TEST")
    print("=" * 50)
    
    try:
        # Create test content
        test_content = "This is a test file for Django storage upload"
        test_filename = "django_storage_test.txt"
        
        print(f"📝 Creating test file: {test_filename}")
        
        # Save file using Django storage
        file_path = default_storage.save(test_filename, ContentFile(test_content.encode()))
        print(f"✅ File saved as: {file_path}")
        
        # Check if file exists in storage
        exists = default_storage.exists(file_path)
        print(f"📁 File exists in storage: {exists}")
        
        # Get file URL
        file_url = default_storage.url(file_path)
        print(f"🔗 File URL: {file_url}")
        
        # Try to read the file back
        try:
            with default_storage.open(file_path, 'r') as f:
                content = f.read()
                print(f"📖 File content: {content[:50]}...")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
        
        return file_path
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_direct_spaces_upload():
    """Test direct upload to Spaces using boto3"""
    print("\n🚀 DIRECT SPACES UPLOAD TEST")
    print("=" * 50)
    
    try:
        # Create S3 client
        session = boto3.session.Session()
        client = session.client('s3',
                              region_name='fra1',
                              endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL'),
                              aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID'),
                              aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY'))
        
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME')
        test_filename = "direct_spaces_test.txt"
        test_content = "This is a direct Spaces upload test"
        
        print(f"📝 Uploading to Spaces: {test_filename}")
        
        # Upload directly to Spaces
        client.put_object(
            Bucket=bucket_name,
            Key=f"media/{test_filename}",
            Body=test_content.encode(),
            ACL='public-read',
            ContentType='text/plain'
        )
        
        print("✅ Direct upload successful")
        
        # Verify file exists
        try:
            response = client.head_object(Bucket=bucket_name, Key=f"media/{test_filename}")
            print(f"✅ File verified in Spaces")
            return True
        except ClientError:
            print("❌ File not found in Spaces after upload")
            return False
            
    except Exception as e:
        print(f"❌ Direct upload error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 DIGITALOCEAN SPACES STORAGE DIAGNOSTIC")
    print("=" * 60)
    
    # Test 1: Configuration
    config_ok = test_storage_configuration()
    
    # Test 2: Connectivity
    connectivity_ok = test_spaces_connectivity()
    
    # Test 3: Django Storage Upload
    django_upload_ok = test_django_storage_upload()
    
    # Test 4: Direct Spaces Upload
    direct_upload_ok = test_direct_spaces_upload()
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Configuration: {'✅' if config_ok else '❌'}")
    print(f"Connectivity: {'✅' if connectivity_ok else '❌'}")
    print(f"Django Upload: {'✅' if django_upload_ok else '❌'}")
    print(f"Direct Upload: {'✅' if direct_upload_ok else '❌'}")
    
    if not connectivity_ok:
        print("\n💡 RECOMMENDATION: Check your Spaces credentials and bucket name")
    elif not django_upload_ok:
        print("\n💡 RECOMMENDATION: Django storage backend may not be configured correctly")
    elif not direct_upload_ok:
        print("\n💡 RECOMMENDATION: Check bucket permissions and ACL settings")

if __name__ == "__main__":
    main() 