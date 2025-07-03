#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'talent_platform.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from dashboard.models import SharedMediaPost
from profiles.models import Prop, Costume, Location, Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem, TalentMedia
from dashboard.serializers import PropDashboardSerializer

def debug_sharing_status():
    print("=== SHARING STATUS DEBUG ===")
    
    # 1. Check all SharedMediaPost records
    print("\n1. Checking SharedMediaPost records:")
    shared_posts = SharedMediaPost.objects.all()
    print(f"Total shared posts: {shared_posts.count()}")
    
    for post in shared_posts[:5]:
        print(f"  - ID: {post.id}, Content Type: {post.content_type}, Object ID: {post.object_id}, Active: {post.is_active}")
        if post.shared_by:
            # Handle BaseUser model correctly
            try:
                full_name = f"{post.shared_by.first_name} {post.shared_by.last_name}".strip()
                if not full_name:
                    full_name = post.shared_by.email
                print(f"    Shared by: {full_name}")
            except Exception as e:
                print(f"    Shared by: {post.shared_by.email} (error getting name: {e})")
    
    # 2. Check TalentMedia (since that's what's actually shared)
    print("\n2. Checking TalentMedia:")
    talent_media = TalentMedia.objects.all()[:5]
    for media in talent_media:
        print(f"  - TalentMedia ID: {media.id}, Name: {media.name}, Type: {media.media_type}")
    
    # 3. Test sharing status logic for TalentMedia
    print("\n3. Testing sharing status logic for TalentMedia:")
    if talent_media:
        test_media = talent_media[0]
        content_type = ContentType.objects.get_for_model(TalentMedia)
        print(f"  - Content type for TalentMedia: {content_type} (ID: {content_type.id})")
        
        # Check without is_active filter first
        all_shares = SharedMediaPost.objects.filter(
            content_type=content_type, 
            object_id=test_media.id
        )
        print(f"  - Test TalentMedia {test_media.id}: Found {all_shares.count()} total shares")
        
        # Check with is_active filter
        active_shares = SharedMediaPost.objects.filter(
            content_type=content_type, 
            object_id=test_media.id, 
            is_active=True
        )
        print(f"  - Test TalentMedia {test_media.id}: Found {active_shares.count()} active shares")
        
        if active_shares.exists():
            shared_post = active_shares.first()
            print(f"    Shared post ID: {shared_post.id}")
            print(f"    Is active: {shared_post.is_active}")
            print(f"    Caption: {shared_post.caption}")
    
    # 4. Check Props (to see if any exist)
    print("\n4. Checking Props:")
    props = Prop.objects.all()[:3]
    print(f"Total Props: {Prop.objects.count()}")
    for prop in props:
        print(f"  - Prop ID: {prop.id}, Name: {prop.name}")
    
    # 5. Test serializer directly for TalentMedia
    print("\n5. Testing TalentMedia sharing status manually:")
    if talent_media:
        test_media = talent_media[0]
        content_type = ContentType.objects.get_for_model(TalentMedia)
        
        # Manually test the sharing status logic
        shared_post = SharedMediaPost.objects.filter(
            content_type=content_type,
            object_id=test_media.id,
            is_active=True
        ).first()
        
        if shared_post:
            print(f"  - TalentMedia {test_media.id} IS SHARED:")
            print(f"    shared_post_id: {shared_post.id}")
            print(f"    shared_by: {shared_post.shared_by.first_name} {shared_post.shared_by.last_name}")
            print(f"    shared_at: {shared_post.created_at}")
            print(f"    shared_caption: {shared_post.caption}")
            print(f"    shared_category: {shared_post.category}")
        else:
            print(f"  - TalentMedia {test_media.id} is NOT SHARED")
    
    # 6. Check what's actually shared
    print("\n6. Checking what's actually shared:")
    for post in shared_posts:
        try:
            content_obj = post.shared_content
            print(f"  - Post {post.id}: {type(content_obj).__name__} (ID: {content_obj.id}) - Active: {post.is_active}")
        except Exception as e:
            print(f"  - Post {post.id}: Error getting content - {e}")
    
    print("\n=== END DEBUG ===")

if __name__ == "__main__":
    debug_sharing_status() 