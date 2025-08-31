#!/usr/bin/env python
"""
Script to completely clean all admin users from the database
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from users.models import BaseUser

def clean_admin_users():
    """Delete all admin dashboard users"""
    
    print("🧹 CLEANING ADMIN USERS")
    print("=" * 40)
    
    # Find all admin users
    admin_users = BaseUser.objects.filter(is_dashboard_admin=True)
    print(f"Found {admin_users.count()} admin users:")
    
    for user in admin_users:
        print(f"  - {user.email} (ID: {user.id})")
    
    if not admin_users.exists():
        print("✅ No admin users found to delete!")
        return
    
    # Confirm deletion
    confirm = input(f"\nAre you sure you want to delete {admin_users.count()} admin user(s)? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Deletion cancelled")
        return
    
    # Delete all admin users
    deleted_count = admin_users.count()
    admin_users.delete()
    
    print(f"✅ Successfully deleted {deleted_count} admin user(s)")
    
    # Verify deletion
    remaining = BaseUser.objects.filter(is_dashboard_admin=True).count()
    print(f"Remaining admin users: {remaining}")
    
    if remaining == 0:
        print("🎉 All admin users successfully deleted!")
    else:
        print(f"⚠️  Warning: {remaining} admin users still exist")

if __name__ == "__main__":
    clean_admin_users()
