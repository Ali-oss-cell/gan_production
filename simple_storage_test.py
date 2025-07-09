#!/usr/bin/env python
"""
Simple storage test
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

def test_simple_storage():
    """Test simple storage operations"""
    print("=== Simple Storage Test ===")
    
    try:
        # Test 1: Save a file
        test_content = "Simple test content"
        test_filename = "simple_test.txt"
        
        print(f"📝 Saving: {test_filename}")
        saved_path = default_storage.save(test_filename, ContentFile(test_content))
        print(f"✅ Saved as: {saved_path}")
        
        # Test 2: Check if file exists
        exists = default_storage.exists(saved_path)
        print(f"📁 File exists: {exists}")
        
        # Test 3: Get URL
        file_url = default_storage.url(saved_path)
        print(f"🔗 URL: {file_url}")
        
        # Test 4: Read file back
        with default_storage.open(saved_path, 'r') as f:
            content = f.read()
            print(f"📄 Content: {content}")
        
        # Test 5: Delete file
        default_storage.delete(saved_path)
        print("🗑️ File deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_storage() 