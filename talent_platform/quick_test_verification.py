#!/usr/bin/env python
"""
Quick test to verify a specific user from the debug output
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from users.models import BaseUser
from django.test import Client
from django.urls import reverse

def test_specific_user():
    """Test verification for a specific user from your debug output"""
    
    # Using one of the users from your debug output
    test_email = "test@production.com"
    
    try:
        user = BaseUser.objects.get(email=test_email)
        print(f"Testing user: {user.email}")
        print(f"Current status: email_verified={user.email_verified}")
        print(f"Token: {user.email_verification_token}")
        
        if not user.email_verification_token:
            print("No token found for this user")
            return
            
        # Use Django's test client to simulate the request
        client = Client()
        
        # Test the verification endpoint
        url = f"/api/verify-email/?token={user.email_verification_token}"
        print(f"Testing URL: {url}")
        
        response = client.get(url)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        # Refresh user from database
        user.refresh_from_db()
        print(f"After verification:")
        print(f"  email_verified: {user.email_verified}")
        print(f"  token: {user.email_verification_token}")
        
        if user.email_verified and user.email_verification_token is None:
            print("✅ SUCCESS: Email verification worked!")
        else:
            print("❌ FAILED: Email verification did not work")
            
    except BaseUser.DoesNotExist:
        print(f"User {test_email} not found")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_specific_user()
