#!/usr/bin/env python
"""
Test Django storage backend
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
import requests

def test_django_storage():
    """Test Django storage backend"""
    print("=== Testing Django Storage Backend ===")
    
    try:
        # Test file content
        test_content = "Django storage test file - updated"
        test_filename = "django_storage_test.txt"
        
        # Save file using Django storage
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        print(f"✅ Django storage saved: {saved_path}")
        
        # Get URL
        file_url = default_storage.url(saved_path)
        print(f"🔗 Django storage URL: {file_url}")
        
        # Test URL accessibility
        response = requests.get(file_url, timeout=10)
        if response.status_code == 200:
            print("✅ Django storage file is accessible")
            print(f"📄 File content: {response.text[:50]}...")
        else:
            print(f"⚠️ Django storage accessibility test failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Django storage: {e}")
        return False

if __name__ == "__main__":
    test_django_storage() 