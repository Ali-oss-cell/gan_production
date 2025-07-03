#!/usr/bin/env python
"""
Test script to show the complete JSON structure of background profile endpoint
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from profiles.models import BackGroundJobsProfile
from profiles.utils.subscription_checker import check_background_user_subscription, get_background_user_restrictions
from payments.models import Subscription, SubscriptionPlan
from payments.serializers import SubscriptionSerializer
from profiles.background_serializers import BackGroundJobs

def show_background_profile_json():
    """Show the complete JSON structure of background profile response"""
    
    print("=== BACKGROUND PROFILE JSON STRUCTURE ===\n")
    
    # Example response structure
    example_response = {
        "profile": {
            "id": 1,
            "user": 1,
            "country": "UAE",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "account_type": "free",  # This changes to "back_ground_jobs" after subscription
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "profile_score": {
            "total": 10,
            "account_tier": 10,
            "verification": 0,
            "profile_completion": 0,
            "media_content": 0,
            "specialization": 0,
            "details": {
                "account_tier": "Free account: +10 points",
                "verification": "Not verified: +0 points (get verified for +20 points)",
                "profile_completion": "Profile incomplete: +0 points (complete your profile for +15 points)",
                "media_content": "No general media: +0 points (add portfolio items for up to +15 points)",
                "specialization": "No specialization: +0 points (add a specialization for +20 points)"
            },
            "improvement_tips": [
                "Upgrade to Production Assets Pro for +40 points",
                "Verify your profile for +20 points",
                "Complete your profile for +15 points",
                "Add portfolio items for up to +15 points",
                "Add a specialization for +20 points"
            ]
        },
        "subscription_status": {
            "has_subscription": False,
            "can_access_features": False,
            "message": "Background users must have an active subscription to access features. Please subscribe to the Production Assets Pro plan.",
            "subscription": None
        },
        "restrictions": {
            "restricted": True,
            "restrictions": [
                "Cannot share props, costumes, or other items",
                "Cannot rent or sell items",
                "Cannot access background job processing services",
                "Cannot upload media files",
                "Cannot create listings",
                "Cannot respond to job requests"
            ],
            "subscription_required": True,
            "subscription_message": "Subscribe to Production Assets Pro plan ($300/year) to unlock all features"
        }
    }
    
    print("=== FOR BACKGROUND USERS WITHOUT SUBSCRIPTION ===")
    print("Account Type: free")
    print("Access: Restricted")
    print("JSON Response:")
    import json
    print(json.dumps(example_response, indent=2))
    
    print("\n" + "="*80 + "\n")
    
    # Example response for users WITH subscription
    subscribed_response = {
        "profile": {
            "id": 1,
            "user": 1,
            "country": "UAE",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "account_type": "back_ground_jobs",  # Changed after subscription
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        },
        "profile_score": {
            "total": 50,
            "account_tier": 50,
            "verification": 0,
            "profile_completion": 0,
            "media_content": 0,
            "specialization": 0,
            "details": {
                "account_tier": "Production Assets Pro account: +50 points",
                "verification": "Not verified: +0 points (get verified for +20 points)",
                "profile_completion": "Profile incomplete: +0 points (complete your profile for +15 points)",
                "media_content": "No general media: +0 points (add portfolio items for up to +15 points)",
                "specialization": "No specialization: +0 points (add a specialization for +20 points)"
            },
            "improvement_tips": [
                "Verify your profile for +20 points",
                "Complete your profile for +15 points",
                "Add portfolio items for up to +15 points",
                "Add a specialization for +20 points"
            ]
        },
        "subscription_status": {
            "has_subscription": True,
            "can_access_features": True,
            "message": "Active subscription found",
            "subscription": {
                "id": 1,
                "plan": "background_jobs",
                "plan_name": "Production Assets Pro",
                "plan_price": "300.00",
                "status": "active",
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": None,
                "is_active": True
            }
        },
        "restrictions": {
            "restricted": False,
            "restrictions": [],
            "subscription_required": False
        }
    }
    
    print("=== FOR BACKGROUND USERS WITH SUBSCRIPTION ===")
    print("Account Type: back_ground_jobs")
    print("Access: Full")
    print("JSON Response:")
    print(json.dumps(subscribed_response, indent=2))
    
    print("\n" + "="*80 + "\n")
    
    print("=== KEY FIELDS TO MONITOR IN FRONTEND ===")
    print("1. profile.account_type: 'free' or 'back_ground_jobs'")
    print("2. subscription_status.has_subscription: true/false")
    print("3. subscription_status.can_access_features: true/false")
    print("4. restrictions.restricted: true/false")
    print("5. restrictions.restrictions: array of blocked features")
    print("6. profile_score.total: numerical score (10 for free, 50+ for subscribed)")

if __name__ == "__main__":
    show_background_profile_json() 