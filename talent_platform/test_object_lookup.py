#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from profiles.models import TalentMedia

print("=== TESTING OBJECT LOOKUP ===")

# Test the exact steps from the serializer
content_type_str = 'profiles.TalentMedia'
object_id = 10

print(f"Input: content_type_str='{content_type_str}', object_id={object_id}")

try:
    # Step 1: Split the content type string
    app_label, model_name = content_type_str.split('.')
    print(f"Step 1: Split into app_label='{app_label}', model_name='{model_name}'")
    
    # Step 2: Get the ContentType
    content_type = ContentType.objects.get(app_label=app_label, model=model_name.lower())
    print(f"Step 2: Found ContentType: {content_type}")
    
    # Step 3: Get the model class
    model_class = content_type.model_class()
    print(f"Step 3: Model class: {model_class}")
    
    # Step 4: Get the object
    obj = model_class.objects.get(id=object_id)
    print(f"Step 4: Found object: {obj}")
    
    print("✅ SUCCESS: All steps completed!")
    
except Exception as e:
    print(f"❌ FAILED at step: {e}")
    print(f"Error type: {type(e)}")

# Also check what TalentMedia objects exist
print(f"\n=== CHECKING AVAILABLE TALENT MEDIA ===")
try:
    all_media = TalentMedia.objects.all()
    print(f"Total TalentMedia objects: {all_media.count()}")
    
    if all_media.count() > 0:
        print("First 10 TalentMedia objects:")
        for media in all_media[:10]:
            print(f"  - ID {media.id}: {media.media_type} - {media.media_file}")
    else:
        print("No TalentMedia objects found!")
        
except Exception as e:
    print(f"Error checking TalentMedia: {e}")

print(f"\n=== DONE ===") 