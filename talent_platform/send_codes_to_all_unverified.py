#!/usr/bin/env python
"""
Script to send verification codes to all unverified users
This replaces the old link-based system with code-based verification
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.utils import timezone
from users.models import BaseUser
from users.serializers import send_verification_code_email
import random
import time

def send_codes_to_unverified_users():
    """
    Send verification codes to all unverified users
    """
    print("=== SENDING VERIFICATION CODES TO UNVERIFIED USERS ===\n")
    
    # Get all unverified users
    unverified_users = BaseUser.objects.filter(
        email_verified=False,
        is_active=True
    )
    
    count = unverified_users.count()
    
    if count == 0:
        print("✅ No unverified users found!")
        return
    
    print(f"Found {count} unverified users")
    print("Generating codes and sending emails...\n")
    
    sent_count = 0
    failed_count = 0
    
    for user in unverified_users:
        try:
            # Generate new verification code
            verification_code = str(random.randint(100000, 999999))
            user.email_verification_code = verification_code
            user.email_verification_code_created = timezone.now()
            user.last_verification_email_sent = timezone.now()
            user.save()
            
            # Send verification code email
            success = send_verification_code_email(user.email, verification_code)
            
            if success:
                print(f"✅ Sent code {verification_code} to {user.email}")
                sent_count += 1
            else:
                print(f"❌ Failed to send code to {user.email}")
                failed_count += 1
                
            # Add small delay to avoid overwhelming email server
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Error processing {user.email}: {str(e)}")
            failed_count += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Total users: {count}")
    print(f"Codes sent: {sent_count}")
    print(f"Failed: {failed_count}")
    
    if sent_count > 0:
        print(f"\n✅ Successfully sent verification codes!")
        print("Users can now verify their emails using the 6-digit codes")
        print("API endpoint: POST /api/verify-code/")

if __name__ == "__main__":
    send_codes_to_unverified_users()
