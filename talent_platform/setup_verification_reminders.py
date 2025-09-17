#!/usr/bin/env python
"""
Setup script for email verification reminders
Run this script to set up automatic email verification reminders
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.utils import timezone
from users.models import BaseUser

def setup_verification_reminders():
    """
    Setup verification reminders for existing unverified users
    """
    print("Setting up email verification reminders...")
    
    # Get all unverified users
    unverified_users = BaseUser.objects.filter(
        email_verified=False,
        is_active=True
    )
    
    count = unverified_users.count()
    print(f"Found {count} unverified users")
    
    if count == 0:
        print("No unverified users found. Setup complete!")
        return
    
    # Set last_verification_email_sent to now for all unverified users
    # This ensures they won't get immediate reminders
    now = timezone.now()
    updated = unverified_users.update(last_verification_email_sent=now)
    
    print(f"Updated {updated} users with verification email timestamp")
    print("Setup complete!")
    
    print("\nTo run verification reminders manually:")
    print("python manage.py send_verification_reminders")
    
    print("\nTo test without sending emails:")
    print("python manage.py send_verification_reminders --dry-run")
    
    print("\nTo set up automatic reminders (add to crontab):")
    print("0 */24 * * * cd /path/to/your/project && python manage.py send_verification_reminders")

if __name__ == "__main__":
    setup_verification_reminders()
