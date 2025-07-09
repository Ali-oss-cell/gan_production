#!/usr/bin/env python3
"""
Add CSRF_TRUSTED_ORIGINS to .env file
"""

def add_csrf_to_env():
    """Add CSRF_TRUSTED_ORIGINS to .env file if it doesn't exist"""
    
    env_file = '.env'
    
    # Read current .env content
    try:
        with open(env_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {env_file} not found")
        return
    
    # Check if CSRF_TRUSTED_ORIGINS already exists
    if 'CSRF_TRUSTED_ORIGINS=' in content:
        print("CSRF_TRUSTED_ORIGINS already exists in .env file")
        return
    
    # Add CSRF_TRUSTED_ORIGINS to the end of the file
    csrf_line = "\n# CSRF Trusted Origins\nCSRF_TRUSTED_ORIGINS=https://gan7club.com,https://www.gan7club.com,https://api.gan7club.com,https://app.gan7club.com\n"
    
    with open(env_file, 'a') as f:
        f.write(csrf_line)
    
    print("Added CSRF_TRUSTED_ORIGINS to .env file")

if __name__ == "__main__":
    add_csrf_to_env() 