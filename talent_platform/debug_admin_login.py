#!/usr/bin/env python
"""
Debug script to test admin login flow and identify issues
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings_production')
django.setup()

from users.models import BaseUser
from users.serializers import AdminDashboardLoginSerializer, DashboardLoginSerializer
from rest_framework.test import APIRequestFactory
import json

def debug_admin_login():
    """Debug the admin login flow step by step"""
    
    print("🔍 DEBUGGING ADMIN LOGIN FLOW")
    print("=" * 50)
    
    # 1. Check admin users in database
    print("\n1. CHECKING ADMIN USERS IN DATABASE:")
    admin_users = BaseUser.objects.filter(is_dashboard_admin=True)
    print(f"Found {admin_users.count()} admin users:")
    
    for user in admin_users:
        print(f"  - {user.email}")
        print(f"    is_dashboard: {user.is_dashboard}")
        print(f"    is_dashboard_admin: {user.is_dashboard_admin}")
        print(f"    is_staff: {user.is_staff}")
        print(f"    is_active: {user.is_active}")
        print(f"    is_superuser: {user.is_superuser}")
    
    if not admin_users.exists():
        print("❌ No admin users found!")
        return
    
    # 2. Test with first admin user
    admin_user = admin_users.first()
    print(f"\n2. TESTING WITH ADMIN USER: {admin_user.email}")
    
    # 3. Test password
    test_password = "YourSecurePassword123"
    password_correct = admin_user.check_password(test_password)
    print(f"Password check for '{test_password}': {password_correct}")
    
    if not password_correct:
        print("❌ Password is incorrect!")
        return
    
    # 4. Test serializer directly
    print("\n3. TESTING SERIALIZER DIRECTLY:")
    factory = APIRequestFactory()
    
    # Create request data
    request_data = {
        'email': admin_user.email,
        'password': test_password,
        'admin_login': 'true'
    }
    
    print(f"Request data: {request_data}")
    
    # Test AdminDashboardLoginSerializer
    try:
        serializer = AdminDashboardLoginSerializer(data=request_data)
        if serializer.is_valid():
            print("✅ AdminDashboardLoginSerializer validation passed")
            response_data = serializer.validated_data
            print(f"Response data: {response_data}")
            
            # Check if required fields are present
            required_fields = ['is_dashboard', 'is_dashboard_admin', 'is_staff']
            for field in required_fields:
                value = response_data.get(field)
                print(f"  {field}: {value}")
                
        else:
            print("❌ AdminDashboardLoginSerializer validation failed:")
            print(f"  Errors: {serializer.errors}")
            
    except Exception as e:
        print(f"❌ AdminDashboardLoginSerializer error: {str(e)}")
    
    # 5. Test DashboardLoginSerializer
    print("\n4. TESTING DashboardLoginSerializer:")
    try:
        serializer = DashboardLoginSerializer(data=request_data)
        if serializer.is_valid():
            print("✅ DashboardLoginSerializer validation passed")
            response_data = serializer.validated_data
            print(f"Response data: {response_data}")
        else:
            print("❌ DashboardLoginSerializer validation failed:")
            print(f"  Errors: {serializer.errors}")
            
    except Exception as e:
        print(f"❌ DashboardLoginSerializer error: {str(e)}")
    
    # 6. Test view logic
    print("\n5. TESTING VIEW LOGIC:")
    
    # Simulate the view's serializer selection logic
    admin_login_detected = request_data.get('admin_login') == 'true'
    print(f"Admin login detected: {admin_login_detected}")
    
    if admin_login_detected:
        print("Should use AdminDashboardLoginSerializer")
    else:
        print("Should use DashboardLoginSerializer")
    
    print("\n" + "=" * 50)
    print("🔍 DEBUG COMPLETE")

if __name__ == "__main__":
    debug_admin_login()
