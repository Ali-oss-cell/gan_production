#!/usr/bin/env python3

def fix_indentation():
    """Fix indentation issues in profiles/models.py"""
    with open('talent_platform/profiles/models.py', 'r') as f:
        content = f.read()
    
    # Replace tabs with 4 spaces
    content = content.expandtabs(4)
    
    with open('talent_platform/profiles/models.py', 'w') as f:
        f.write(content)
    
    print("Indentation fixed in profiles/models.py")

if __name__ == "__main__":
    fix_indentation() 