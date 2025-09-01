#!/usr/bin/env python
"""
Force delete all admin users using direct Django shell commands
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from users.models import BaseUser

def force_delete_admin_users():
    """Force delete all admin dashboard users"""
    
    print("💥 FORCE DELETING ADMIN USERS")
    print("=" * 40)
    
    # Method 1: Find by is_dashboard_admin
    admin_users_1 = BaseUser.objects.filter(is_dashboard_admin=True)
    print(f"Method 1 - is_dashboard_admin=True: {admin_users_1.count()} users")
    
    # Method 2: Find by email (specific users we know exist)
    admin_users_2 = BaseUser.objects.filter(email__in=['admin@gan7club.com', 'ali@admin.com'])
    print(f"Method 2 - Specific emails: {admin_users_2.count()} users")
    
    # Method 3: Find all dashboard users
    dashboard_users = BaseUser.objects.filter(is_dashboard=True)
    print(f"Method 3 - All dashboard users: {dashboard_users.count()} users")
    
    # Show all dashboard users
    print("\n📋 All dashboard users found:")
    for user in dashboard_users:
        print(f"  - {user.email} (ID: {user.id})")
        print(f"    is_dashboard: {user.is_dashboard}")
        print(f"    is_dashboard_admin: {user.is_dashboard_admin}")
        print(f"    is_staff: {user.is_staff}")
        print(f"    is_superuser: {user.is_superuser}")
        print()
    
    # Delete specific users we know exist
    users_to_delete = BaseUser.objects.filter(email__in=['admin@gan7club.com', 'ali@admin.com'])
    
    if users_to_delete.exists():
        print(f"🗑️  Deleting {users_to_delete.count()} specific users:")
        for user in users_to_delete:
            print(f"  - {user.email} (ID: {user.id})")
        
        confirm = input(f"\nAre you sure you want to delete these users? (yes/no): ")
        if confirm.lower() == 'yes':
            users_to_delete.delete()
            print("✅ Users deleted successfully!")
        else:
            print("❌ Deletion cancelled")
    else:
        print("❌ No users found to delete")
    
    # Verify deletion
    remaining = BaseUser.objects.filter(email__in=['admin@gan7club.com', 'ali@admin.com'])
    print(f"\nRemaining users: {remaining.count()}")

if __name__ == "__main__":
    force_delete_admin_users()
