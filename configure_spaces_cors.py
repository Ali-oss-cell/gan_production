#!/usr/bin/env python
"""
Configure CORS settings for DigitalOcean Spaces bucket
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

def configure_cors():
    """Configure CORS settings for the bucket"""
    print("=== Configuring CORS for DigitalOcean Spaces ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # CORS configuration for web applications
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': [
                        '*'
                    ],
                    'AllowedMethods': [
                        'GET',
                        'PUT',
                        'POST',
                        'DELETE',
                        'HEAD'
                    ],
                    'AllowedOrigins': [
                        'http://localhost:3000',  # React development
                        'http://localhost:3001',  # Alternative React port
                        'https://gan7club.com',   # Your production domain
                        'https://www.gan7club.com', # www subdomain
                        'https://api.gan7club.com', # API domain
                        'https://cdn.gan7club.com', # CDN domain
                        '*'  # Allow all origins (for testing - remove in production)
                    ],
                    'ExposeHeaders': [
                        'ETag',
                        'Content-Length',
                        'Content-Type'
                    ],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        # Apply CORS configuration
        client.put_bucket_cors(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        
        print("✅ CORS configuration applied successfully!")
        print("\n📋 Applied CORS rules:")
        for rule in cors_configuration['CORSRules']:
            print(f"   - Allowed Origins: {rule['AllowedOrigins']}")
            print(f"   - Allowed Methods: {rule['AllowedMethods']}")
            print(f"   - Allowed Headers: {rule['AllowedHeaders']}")
            print(f"   - Max Age: {rule['MaxAgeSeconds']} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring CORS: {e}")
        return False

def configure_bucket_policy():
    """Configure bucket policy for public read access"""
    print("\n=== Configuring Bucket Policy ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # Bucket policy for public read access
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{settings.AWS_STORAGE_BUCKET_NAME}/*"
                }
            ]
        }
        
        # Apply bucket policy
        client.put_bucket_policy(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Policy=str(bucket_policy).replace("'", '"')
        )
        
        print("✅ Bucket policy applied successfully!")
        print("📋 Policy allows public read access to all objects")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring bucket policy: {e}")
        return False

def remove_wildcard_cors():
    """Remove wildcard CORS rule for production security"""
    print("\n=== Removing Wildcard CORS for Production ===")
    
    try:
        session = boto3.session.Session()
        client = session.client('s3',
                               region_name='fra1',
                               endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                               aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                               aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        
        # Production CORS configuration (no wildcards)
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': [
                        'Content-Type',
                        'Authorization',
                        'X-Requested-With',
                        'Accept',
                        'Origin'
                    ],
                    'AllowedMethods': [
                        'GET',
                        'PUT',
                        'POST',
                        'DELETE',
                        'HEAD'
                    ],
                    'AllowedOrigins': [
                        'https://gan7club.com',
                        'https://www.gan7club.com',
                        'https://api.gan7club.com',
                        'https://cdn.gan7club.com'
                    ],
                    'ExposeHeaders': [
                        'ETag',
                        'Content-Length',
                        'Content-Type'
                    ],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        # Apply production CORS configuration
        client.put_bucket_cors(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            CORSConfiguration=cors_configuration
        )
        
        print("✅ Production CORS configuration applied!")
        print("📋 Removed wildcard origins for security")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating CORS: {e}")
        return False

def main():
    """Main function"""
    print("🚀 DigitalOcean Spaces Configuration")
    print("=" * 50)
    
    # Check if we have the required settings
    if not all([
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
        settings.AWS_STORAGE_BUCKET_NAME,
        settings.AWS_S3_ENDPOINT_URL
    ]):
        print("❌ Missing required Spaces configuration")
        return
    
    print(f"🪣 Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"🌐 Endpoint: {settings.AWS_S3_ENDPOINT_URL}")
    
    # Configure CORS
    if configure_cors():
        print("\n✅ CORS configuration completed")
    else:
        print("\n❌ CORS configuration failed")
        return
    
    # Configure bucket policy
    if configure_bucket_policy():
        print("\n✅ Bucket policy configuration completed")
    else:
        print("\n❌ Bucket policy configuration failed")
    
    print("\n" + "=" * 50)
    print("🎉 Configuration completed!")
    print("\n📝 Next steps:")
    print("1. Test file uploads from your application")
    print("2. Verify CORS works with your frontend")
    print("3. Run 'python configure_spaces_cors.py --production' to remove wildcards")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--production':
        remove_wildcard_cors()
    else:
        main() 