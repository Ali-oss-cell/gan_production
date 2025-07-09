#!/usr/bin/env python
"""
Migrate existing local media files to DigitalOcean Spaces
"""

import os
import sys
import django
from pathlib import Path
from django.core.files.base import ContentFile

# Add the talent_platform directory to Python path
project_dir = Path(__file__).resolve().parent / 'talent_platform'
sys.path.insert(0, str(project_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from talent_platform.profiles.models import TalentMedia
from django.conf import settings

def migrate_media_to_spaces():
    """Migrate existing media files to DigitalOcean Spaces"""
    print("=== Migrating Media Files to DigitalOcean Spaces ===")
    
    media_files = TalentMedia.objects.all()
    print(f"Found {media_files.count()} media files to migrate")
    
    migrated_count = 0
    error_count = 0
    
    for media in media_files:
        if media.media_file:
            try:
                print(f"Processing: {media.media_file.name}")
                
                # Check if file exists locally
                local_path = media.media_file.path
                if os.path.exists(local_path):
                    # Read the file content
                    with open(local_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Save to Spaces using Django's storage
                    media.media_file.save(
                        os.path.basename(media.media_file.name),
                        ContentFile(file_content),
                        save=True
                    )
                    
                    print(f"  ✅ Migrated: {media.media_file.name}")
                    print(f"  📎 New URL: {media.media_file.url}")
                    migrated_count += 1
                else:
                    print(f"  ❌ File not found locally: {local_path}")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error migrating {media.media_file.name}: {str(e)}")
                error_count += 1
    
    print(f"\n=== Migration Complete ===")
    print(f"✅ Successfully migrated: {migrated_count} files")
    print(f"❌ Errors: {error_count} files")
    
    return migrated_count, error_count

if __name__ == "__main__":
    migrate_media_to_spaces()