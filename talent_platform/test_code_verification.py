#!/usr/bin/env python
"""
Test script for the new code-based email verification system
"""

import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.utils import timezone
from users.models import BaseUser
from users.serializers import send_verification_code_email
import random

def test_code_verification():
    """
    Test the new code-based email verification
    """
    print("=== CODE-BASED EMAIL VERIFICATION TEST ===\n")
    
    # Get or create a test user
    test_email = "test_code@example.com"
    
    try:
        user = BaseUser.objects.get(email=test_email)
        print(f"Using existing user: {user.email}")
    except BaseUser.DoesNotExist:
        user = BaseUser.objects.create_user(
            email=test_email,
            password='testpass123',
            first_name='Test',
            last_name='CodeUser'
        )
        print(f"Created new user: {user.email}")
    
    # Reset user for testing
    user.email_verified = False
    verification_code = str(random.randint(100000, 999999))
    user.email_verification_code = verification_code
    user.email_verification_code_created = timezone.now()
    user.save()
    
    print(f"Generated verification code: {verification_code}")
    print(f"User status: email_verified={user.email_verified}")
    
    # Test sending verification code email
    print("\n--- Testing Email Sending ---")
    success = send_verification_code_email(user.email, verification_code)
    if success:
        print("✅ Verification code email sent successfully")
    else:
        print("❌ Failed to send verification code email")
    
    # Test the verification endpoint
    print("\n--- Testing Verification Endpoint ---")
    
    verification_url = "http://localhost:8000/api/verify-code/"
    payload = {
        "email": user.email,
        "code": verification_code
    }
    
    try:
        response = requests.post(verification_url, json=payload)
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Check if user is now verified
        user.refresh_from_db()
        print(f"\nAfter verification:")
        print(f"  email_verified: {user.email_verified}")
        print(f"  verification_code: {user.email_verification_code}")
        
        if user.email_verified and user.email_verification_code is None:
            print("✅ CODE VERIFICATION SUCCESSFUL!")
        else:
            print("❌ CODE VERIFICATION FAILED!")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Could not connect to server. Make sure Django server is running on port 8000")
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")

def test_invalid_code():
    """
    Test with invalid verification code
    """
    print("\n=== TESTING INVALID CODE ===")
    
    verification_url = "http://localhost:8000/api/verify-code/"
    payload = {
        "email": "test_code@example.com",
        "code": "999999"  # Invalid code
    }
    
    try:
        response = requests.post(verification_url, json=payload)
        print(f"Invalid code response: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400 and 'Invalid verification code' in response.json().get('message', ''):
            print("✅ Invalid code handling works correctly!")
        else:
            print("❌ Invalid code handling failed!")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Could not connect to server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Starting code-based email verification tests...")
    print("Make sure your Django server is running on port 8000")
    print("=" * 60)
    
    test_code_verification()
    test_invalid_code()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nNow users will receive emails with 6-digit codes instead of links!")
    print("Frontend should have a form where users enter their email and code.")
