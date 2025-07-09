#!/usr/bin/env python
"""
Check media files in DigitalOcean Spaces and verify URLs
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
from talent_platform.profiles.models import TalentMedia

def check_spaces_files():
    """Check files in DigitalOcean Spaces"""
    print("=== DigitalOcean Spaces Files Check ===")
    
    # Connect to Spaces
    session = boto3.session.Session()
    client = session.client('s3',
                           region_name='fra1',
                           endpoint_url='https://fra1.digitaloceanspaces.com',
                           aws_access_key_id='DO0068G3VB7QMN222YRT',
                           aws_secret_access_key='myn1ZEC26kVj99ZOC/qBYT2C2Vouk5IZ1bDcVZWRnes')
    
    # List all files in media folder
    response = client.list_objects_v2(Bucket='ganspace', Prefix='media/')
    objects = response.get('Contents', [])
    
    print(f"📁 Total files in media folder: {len(objects)}")
    print("\n📋 Files in DigitalOcean Spaces:")
    for obj in objects:
        print(f"   - {obj['Key']} ({obj['Size']} bytes)")
    
    return objects

def check_django_media():
    """Check media files in Django database"""
    print("\n=== Django Database Media Files ===")
    
    media_files = TalentMedia.objects.all()
    print(f"📊 Total media files in database: {media_files.count()}")
    
    print("\n📋 Media files in Django database:")
    for media in media_files[:10]:  # Show first 10
        if media.media_file:
            print(f"   - {media.media_file.name} ({media.media_type})")
            print(f"     URL: {media.media_file.url}")
            
            # Safely get file size
            try:
                size = media.media_file.size
                print(f"     Size: {size} bytes")
            except (FileNotFoundError, OSError):
                print(f"     Size: File not found locally")
            print()

def test_media_urls():
    """Test if media URLs are accessible"""
    print("=== Media URL Accessibility Test ===")
    
    media_files = TalentMedia.objects.all()[:5]  # Test first 5 files
    
    for media in media_files:
        if media.media_file:
            url = media.media_file.url
            print(f"Testing: {url}")
            
            try:
                import requests
                response = requests.head(url, timeout=5)
                status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
                print(f"   Status: {status}")
            except Exception as e:
                print(f"   Status: ❌ Error - {str(e)}")
            print()

if __name__ == "__main__":
    check_spaces_files()
    check_django_media()
    test_media_urls()
    print("\n=== Check Complete ===")