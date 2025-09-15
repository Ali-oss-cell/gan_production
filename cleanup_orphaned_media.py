#!/usr/bin/env python3
"""
Clean up orphaned media records (database entries without actual files)
"""
import os
import django
import sys

# Add the project directory to Python path
sys.path.append('talent_platform')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from profiles.models import TalentMedia
from django.core.files.storage import default_storage

def cleanup_orphaned_media():
    print("🧹 Cleaning up orphaned media records...")
    
    orphaned_count = 0
    total_count = 0
    
    for media in TalentMedia.objects.all():
        total_count += 1
        
        # Check if file exists in storage
        file_exists = False
        if media.media_file:
            try:
                file_exists = default_storage.exists(media.media_file.name)
            except:
                file_exists = False
        
        if not file_exists:
            print(f"❌ Orphaned: ID={media.id}, Name='{media.name}', File='{media.media_file}'")
            
            # Ask for confirmation before deleting
            response = input(f"Delete this orphaned record? (y/N): ")
            if response.lower() == 'y':
                media.delete()
                orphaned_count += 1
                print(f"✅ Deleted orphaned record ID={media.id}")
            else:
                print(f"⏭️ Skipped ID={media.id}")
    
    print(f"\n📊 Summary:")
    print(f"Total media records: {total_count}")
    print(f"Orphaned records deleted: {orphaned_count}")
    print(f"Remaining records: {total_count - orphaned_count}")

if __name__ == "__main__":
    cleanup_orphaned_media()


