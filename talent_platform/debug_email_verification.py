#!/usr/bin/env python
"""
Debug script for email verification issues
Run this to check what's happening with email verification
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
from datetime import timedelta
from users.models import BaseUser

def debug_email_verification():
    """
    Debug email verification issues
    """
    print("=== EMAIL VERIFICATION DEBUG ===\n")
    
    # Get all unverified users with tokens
    unverified_users = BaseUser.objects.filter(
        email_verified=False,
        email_verification_token__isnull=False
    )
    
    print(f"Found {unverified_users.count()} unverified users with tokens:\n")
    
    for user in unverified_users:
        print(f"User: {user.email}")
        print(f"  Email Verified: {user.email_verified}")
        print(f"  Token: {user.email_verification_token}")
        print(f"  Token Created: {user.email_verification_token_created}")
        
        # Check if token is expired
        if user.email_verification_token_created:
            time_diff = timezone.now() - user.email_verification_token_created
            is_expired = time_diff > timedelta(hours=24)
            print(f"  Token Age: {time_diff}")
            print(f"  Token Expired: {is_expired}")
        
        print(f"  Last Verification Email Sent: {user.last_verification_email_sent}")
        print("-" * 50)
    
    # Test verification process
    print("\n=== TESTING VERIFICATION PROCESS ===")
    
    # Get a test user
    test_user = unverified_users.first()
    if test_user:
        print(f"\nTesting with user: {test_user.email}")
        print(f"Before verification:")
        print(f"  email_verified: {test_user.email_verified}")
        print(f"  token: {test_user.email_verification_token}")
        
        # Simulate verification
        test_user.email_verified = True
        test_user.email_verification_token = None
        test_user.email_verification_token_created = None
        test_user.save()
        
        # Reload from database
        test_user.refresh_from_db()
        
        print(f"After verification:")
        print(f"  email_verified: {test_user.email_verified}")
        print(f"  token: {test_user.email_verification_token}")
        
        # Reset for testing
        test_user.email_verified = False
        test_user.email_verification_token = "test_token_123"
        test_user.email_verification_token_created = timezone.now()
        test_user.save()
        
        print(f"Reset for testing:")
        print(f"  email_verified: {test_user.email_verified}")
        print(f"  token: {test_user.email_verification_token}")
    
    print("\n=== VERIFICATION ENDPOINT TEST ===")
    print("To test the verification endpoint manually:")
    print("1. Get a token from above")
    print("2. Test the endpoint:")
    print(f"   GET /api/verify-email/?token=TOKEN_HERE")
    print("3. Check if email_verified changes to True")

if __name__ == "__main__":
    debug_email_verification()
