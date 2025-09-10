#!/usr/bin/env python3
"""
Simple script to set environment variable for production settings.
Run this on your production server to ensure the correct settings are loaded.
"""
import os

def set_production_environment():
    """Set environment variable to use production settings"""
    # Create/update the .env file in production
    env_file = '/var/www/gan7club/.env'
    
    # Read existing .env file
    env_content = ''
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Check if PRODUCTION is already set
    if 'PRODUCTION=' not in env_content:
        # Add PRODUCTION=true
        if env_content and not env_content.endswith('\n'):
            env_content += '\n'
        env_content += 'PRODUCTION=true\n'
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ Added PRODUCTION=true to .env file")
    else:
        print("✅ PRODUCTION variable already exists in .env file")
    
    # Also set in current environment
    os.environ['PRODUCTION'] = 'true'
    print("✅ Set PRODUCTION=true in current environment")

if __name__ == '__main__':
    set_production_environment()
