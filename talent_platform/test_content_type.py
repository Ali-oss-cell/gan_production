#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType

print("=== TESTING CONTENT TYPE LOOKUP ===")

# Test the exact lookup that's failing
content_type_str = 'profiles.TalentMedia'
app_label, model_name = content_type_str.split('.')

print(f"Input: {content_type_str}")
print(f"Split into: app_label='{app_label}', model_name='{model_name}'")
print(f"model_name.lower() = '{model_name.lower()}'")

try:
    content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
    print(f"✅ SUCCESS: Found {content_type}")
except ContentType.DoesNotExist:
    print(f"❌ FAILED: ContentType not found")
    
    # Show what content types exist for this app
    print(f"\nAvailable content types for '{app_label}':")
    for ct in ContentType.objects.filter(app_label=app_label).order_by('model'):
        print(f"  - {ct.app_label}.{ct.model} (ID: {ct.id})")

print(f"\n=== DONE ===") 