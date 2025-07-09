#!/usr/bin/env python3
"""
Test CORS configuration locally on the server
"""

import requests

def test_local_cors():
    """Test CORS headers on local server"""
    
    base_url = "http://localhost"
    endpoints = [
        "/api/users/",
        "/api/profile/talent/",
        "/api/payments/subscription-plans/",
    ]
    
    print("=== Testing Local CORS Headers ===")
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\nTesting: {url}")
        
        try:
            # Test OPTIONS request (preflight)
            response = requests.options(url, timeout=5)
            print(f"  OPTIONS Status: {response.status_code}")
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
            }
            
            for header, value in cors_headers.items():
                print(f"  {header}: {value}")
                
        except Exception as e:
            print(f"  Error: {str(e)}")

if __name__ == "__main__":
    test_local_cors() 