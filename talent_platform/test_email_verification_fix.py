#!/usr/bin/env python
"""
Test script to verify email verification fix is working
"""

import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from users.models import BaseUser
import secrets

def test_email_verification():
    """
    Test the email verification functionality
    """
    print("=== EMAIL VERIFICATION FIX TEST ===\n")
    
    # Get a test user with a valid token
    test_users = BaseUser.objects.filter(
        email_verified=False,
        email_verification_token__isnull=False
    )[:3]  # Get first 3 users
    
    if not test_users.exists():
        print("No unverified users found. Creating a test user...")
        # Create a test user
        test_user = BaseUser.objects.create_user(
            email='test_verification@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        test_user.email_verification_token = secrets.token_urlsafe(32)
        test_user.email_verification_token_created = timezone.now()
        test_user.save()
        test_users = [test_user]
    
    for user in test_users:
        print(f"\nTesting verification for: {user.email}")
        print(f"Current status: email_verified={user.email_verified}")
        print(f"Token: {user.email_verification_token}")
        
        # Test the verification endpoint
        verification_url = f"http://localhost:8000/api/verify-email/?token={user.email_verification_token}"
        print(f"Testing URL: {verification_url}")
        
        try:
            # Make request to verification endpoint
            response = requests.get(verification_url)
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.json()}")
            
            # Check if user is now verified
            user.refresh_from_db()
            print(f"After verification: email_verified={user.email_verified}")
            print(f"Token cleared: {user.email_verification_token is None}")
            
            if user.email_verified and user.email_verification_token is None:
                print("✅ VERIFICATION SUCCESSFUL!")
            else:
                print("❌ VERIFICATION FAILED!")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Could not connect to server. Make sure Django server is running on port 8000")
        except Exception as e:
            print(f"❌ Error during test: {str(e)}")
        
        print("-" * 60)
        
        # Reset user for next test if needed
        if user.email_verified:
            user.email_verified = False
            user.email_verification_token = secrets.token_urlsafe(32)
            user.email_verification_token_created = timezone.now()
            user.save()
            print(f"Reset user {user.email} for future testing")

def test_invalid_token():
    """
    Test with invalid token
    """
    print("\n=== TESTING INVALID TOKEN ===")
    
    invalid_token = "invalid_token_123"
    verification_url = f"http://localhost:8000/api/verify-email/?token={invalid_token}"
    
    try:
        response = requests.get(verification_url)
        print(f"Invalid token response: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400 and 'Invalid verification token' in response.json().get('message', ''):
            print("✅ Invalid token handling works correctly!")
        else:
            print("❌ Invalid token handling failed!")
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Could not connect to server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_expired_token():
    """
    Test with expired token
    """
    print("\n=== TESTING EXPIRED TOKEN ===")
    
    # Create user with expired token
    try:
        expired_user = BaseUser.objects.create_user(
            email='expired_test@example.com',
            password='testpass123',
            first_name='Expired',
            last_name='Test'
        )
        expired_user.email_verification_token = secrets.token_urlsafe(32)
        expired_user.email_verification_token_created = timezone.now() - timedelta(hours=25)  # Expired
        expired_user.save()
        
        verification_url = f"http://localhost:8000/api/verify-email/?token={expired_user.email_verification_token}"
        
        response = requests.get(verification_url)
        print(f"Expired token response: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400 and 'expired' in response.json().get('message', '').lower():
            print("✅ Expired token handling works correctly!")
        else:
            print("❌ Expired token handling failed!")
            
        # Clean up
        expired_user.delete()
        
    except requests.exceptions.ConnectionError:
        print("⚠️  Could not connect to server")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Starting email verification tests...")
    print("Make sure your Django server is running on port 8000")
    print("=" * 60)
    
    test_email_verification()
    test_invalid_token()
    test_expired_token()
    
    print("\n" + "=" * 60)
    print("Test completed!")
