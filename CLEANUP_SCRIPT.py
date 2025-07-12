#!/usr/bin/env python
"""
Cleanup script to remove unnecessary test files
"""

import os

# Files to keep (essential)
files_to_keep = [
    'UPLOAD_FIX_SUMMARY.md',
    'test_production_upload.py',
    'configure_spaces_cors.py',
    'requirements.txt',
    'runtime.txt',
    'README.md',
    '.gitignore',
    'LICENSE',
    'PRODUCTION_DEPLOYMENT_GUIDE.md',
    'DEPLOYMENT_CHECKLIST.md',
    'profiles_endpoints_collection.json',
    'users_endpoints_collection.json',
    'nginx_cors_fix.conf'
]

# Files to remove (test files)
files_to_remove = [
    'check_env_vars.py',
    'debug_url_generation.py',
    'simple_storage_test.py',
    'test_upload_workflow.py',
    'debug_storage.py',
    'test_django_storage.py',
    'test_spaces_comprehensive.py',
    'add_csrf_to_env.py',
    'test_server_cors.py',
    'migrate_to_spaces.py',
    'check_all_media_types.py',
    'check_media_files.py',
    'debug_profile_test.py',
    'clear',
    'ssh-keygen',
    'CLEANUP_SCRIPT.py'  # This file will remove itself
]

def cleanup():
    """Remove unnecessary test files"""
    print("🧹 Cleaning up test files...")
    
    removed_count = 0
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"🗑️ Removed: {file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Could not remove {file}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} files.")
    print(f"📁 Kept {len(files_to_keep)} essential files.")

if __name__ == "__main__":
    cleanup() 