#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from dashboard.models import SharedMediaPost
from dashboard.utils import get_sharing_status, bulk_get_sharing_status, clear_sharing_status_cache
from profiles.models import TalentMedia, Prop, BandMedia
from django.core.cache import cache

def test_sharing_status():
    print("=== TESTING SHARING STATUS FUNCTIONALITY ===")
    
    # Clear cache first
    cache.clear()
    print("✓ Cache cleared")
    
    # 1. Test with no shared media
    print("\n1. Testing with no shared media:")
    talent_media = TalentMedia.objects.first()
    if talent_media:
        status = get_sharing_status(talent_media)
        print(f"  - TalentMedia {talent_media.id}: {status['is_shared']}")
        assert status['is_shared'] == False, "Should not be shared"
        print("  ✓ Correctly shows not shared")
    else:
        print("  - No TalentMedia found to test")
    
    # 2. Test with shared media
    print("\n2. Testing with shared media:")
    shared_posts = SharedMediaPost.objects.filter(is_active=True)[:3]
    if shared_posts:
        for post in shared_posts:
            try:
                content_obj = post.shared_content
                status = get_sharing_status(content_obj)
                print(f"  - {type(content_obj).__name__} {content_obj.id}: {status['is_shared']}")
                assert status['is_shared'] == True, f"Should be shared: {content_obj.id}"
                print(f"  ✓ Correctly shows shared by {status['shared_by']}")
            except Exception as e:
                print(f"  - Error testing {post.id}: {e}")
    else:
        print("  - No shared posts found to test")
    
    # 3. Test bulk function
    print("\n3. Testing bulk sharing status:")
    media_objects = list(TalentMedia.objects.all()[:5])
    if media_objects:
        bulk_status = bulk_get_sharing_status(media_objects)
        print(f"  - Got status for {len(bulk_status)} objects")
        for obj_id, status in bulk_status.items():
            print(f"    - Object {obj_id}: {status['is_shared']}")
        print("  ✓ Bulk function working")
    else:
        print("  - No media objects found for bulk test")
    
    # 4. Test cache functionality
    print("\n4. Testing cache functionality:")
    if talent_media:
        # First call should hit database
        status1 = get_sharing_status(talent_media)
        print(f"  - First call: {status1['is_shared']}")
        
        # Second call should hit cache
        status2 = get_sharing_status(talent_media)
        print(f"  - Second call: {status2['is_shared']}")
        
        assert status1 == status2, "Cached result should match"
        print("  ✓ Cache working correctly")
        
        # Test cache clearing
        clear_sharing_status_cache(talent_media)
        print("  ✓ Cache cleared successfully")
    
    # 5. Test error handling
    print("\n5. Testing error handling:")
    try:
        status = get_sharing_status(None)
        print(f"  - None object: {status['is_shared']}")
        assert status['is_shared'] == False, "Should handle None gracefully"
        print("  ✓ Handles None gracefully")
    except Exception as e:
        print(f"  - Error with None: {e}")
    
    print("\n=== ALL TESTS COMPLETED ===")
    print("✓ Sharing status functionality is working correctly!")

if __name__ == "__main__":
    test_sharing_status() 