from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Count, Q
from .models import SharedMediaPost
import hashlib
import json

# Cache timeouts
CACHE_TIMEOUTS = {
    'sharing_status': 300,  # 5 minutes
    'profile_score': 600,   # 10 minutes
    'media_counts': 1800,   # 30 minutes
    'search_results': 900,  # 15 minutes
    'user_stats': 3600,     # 1 hour
}

def get_cache_key(prefix, *args, **kwargs):
    """
    Generate a consistent cache key from arguments
    """
    key_parts = [prefix] + [str(arg) for arg in args]
    if kwargs:
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
    
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def get_sharing_status(media_obj, cache_key=None):
    """
    Centralized function to get sharing status for any media object.
    Uses caching to improve performance and consistency.
    
    Args:
        media_obj: The media object (TalentMedia, BandMedia, Item, etc.)
        cache_key: Optional custom cache key
    
    Returns:
        dict: Consistent sharing status object
    """
    if not media_obj or not hasattr(media_obj, 'id'):
        return {
            'is_shared': False,
            'shared_post_id': None,
            'shared_by': None,
            'shared_at': None,
            'shared_caption': None,
            'shared_category': None
        }
    
    # Create cache key if not provided
    if not cache_key:
        content_type = ContentType.objects.get_for_model(media_obj)
        cache_key = get_cache_key('sharing_status', content_type.id, media_obj.id)
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        # Get the content type for this media
        content_type = ContentType.objects.get_for_model(media_obj)
        
        # Check if this media is already shared
        shared_post = SharedMediaPost.objects.filter(
            content_type=content_type,
            object_id=media_obj.id,
            is_active=True
        ).select_related('shared_by').first()
        
        if shared_post:
            # Get shared_by name consistently
            shared_by_name = None
            if shared_post.shared_by:
                full_name = f"{shared_post.shared_by.first_name} {shared_post.shared_by.last_name}".strip()
                shared_by_name = full_name if full_name else shared_post.shared_by.email
            
            result = {
                'is_shared': True,
                'shared_post_id': shared_post.id,
                'shared_by': shared_by_name,
                'shared_at': shared_post.shared_at,
                'shared_caption': shared_post.caption,
                'shared_category': shared_post.category
            }
        else:
            result = {
                'is_shared': False,
                'shared_post_id': None,
                'shared_by': None,
                'shared_at': None,
                'shared_caption': None,
                'shared_category': None
            }
        
        # Cache the result
        cache.set(cache_key, result, CACHE_TIMEOUTS['sharing_status'])
        return result
        
    except Exception as e:
        # Always return a valid sharing status, even if there's an error
        result = {
            'is_shared': False,
            'shared_post_id': None,
            'shared_by': None,
            'shared_at': None,
            'shared_caption': None,
            'shared_category': None,
            'error': str(e)
        }
        
        # Cache the error result for a shorter time
        cache.set(cache_key, result, 60)
        return result

def get_profile_score_cached(profile_obj):
    """
    Get profile score with caching for expensive calculations
    """
    if not profile_obj or not hasattr(profile_obj, 'id'):
        return {'total': 0, 'details': {}}
    
    cache_key = get_cache_key('profile_score', profile_obj._meta.model_name, profile_obj.id)
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Calculate profile score
    result = profile_obj.get_profile_score()
    
    # Cache the result
    cache.set(cache_key, result, CACHE_TIMEOUTS['profile_score'])
    return result

def get_media_counts_cached(profile_obj):
    """
    Get media counts with caching
    """
    if not profile_obj or not hasattr(profile_obj, 'id'):
        return {'images': 0, 'videos': 0, 'total': 0}
    
    cache_key = get_cache_key('media_counts', profile_obj._meta.model_name, profile_obj.id)
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    # Calculate media counts
    media_counts = {
        'images': profile_obj.media.filter(media_type='image', is_test_video=False).count(),
        'videos': profile_obj.media.filter(media_type='video', is_test_video=False).count(),
    }
    media_counts['total'] = media_counts['images'] + media_counts['videos']
    
    # Cache the result
    cache.set(cache_key, media_counts, CACHE_TIMEOUTS['media_counts'])
    return media_counts

def get_user_stats_cached(user_id):
    """
    Get user statistics with caching
    """
    cache_key = get_cache_key('user_stats', user_id)
    
    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result
    
    from profiles.models import TalentUserProfile, BackGroundJobsProfile
    
    # Calculate user stats
    talent_profile = TalentUserProfile.objects.filter(user_id=user_id).first()
    background_profile = BackGroundJobsProfile.objects.filter(user_id=user_id).first()
    
    stats = {
        'has_talent_profile': talent_profile is not None,
        'has_background_profile': background_profile is not None,
        'profile_type': None,
        'account_type': None,
        'is_verified': False,
        'profile_complete': False,
    }
    
    if talent_profile:
        stats.update({
            'profile_type': 'talent',
            'account_type': talent_profile.account_type,
            'is_verified': talent_profile.is_verified,
            'profile_complete': talent_profile.profile_complete,
        })
    elif background_profile:
        stats.update({
            'profile_type': 'background',
            'account_type': background_profile.account_type,
        })
    
    # Cache the result
    cache.set(cache_key, stats, CACHE_TIMEOUTS['user_stats'])
    return stats

def clear_sharing_status_cache(media_obj=None, content_type=None, object_id=None):
    """
    Clear sharing status cache for a specific media object or all objects.
    
    Args:
        media_obj: The media object to clear cache for
        content_type: ContentType object (alternative to media_obj)
        object_id: Object ID (alternative to media_obj)
    """
    if media_obj:
        content_type = ContentType.objects.get_for_model(media_obj)
        object_id = media_obj.id
    
    if content_type and object_id:
        cache_key = get_cache_key('sharing_status', content_type.id, object_id)
        cache.delete(cache_key)
    else:
        # Clear all sharing status cache (use with caution)
        # This is a simple approach - in production you might want a more sophisticated cache invalidation
        pass

def clear_profile_cache(profile_obj):
    """
    Clear all cache related to a profile
    """
    if not profile_obj or not hasattr(profile_obj, 'id'):
        return
    
    # Clear profile score cache
    profile_score_key = get_cache_key('profile_score', profile_obj._meta.model_name, profile_obj.id)
    cache.delete(profile_score_key)
    
    # Clear media counts cache
    media_counts_key = get_cache_key('media_counts', profile_obj._meta.model_name, profile_obj.id)
    cache.delete(media_counts_key)
    
    # Clear user stats cache
    if hasattr(profile_obj, 'user_id'):
        user_stats_key = get_cache_key('user_stats', profile_obj.user_id)
        cache.delete(user_stats_key)

def bulk_get_sharing_status(media_objects):
    """
    Get sharing status for multiple media objects efficiently.
    
    Args:
        media_objects: List of media objects
    
    Returns:
        dict: Mapping of object_id to sharing status
    """
    if not media_objects:
        return {}
    
    # Group by content type for efficient querying
    content_type_groups = {}
    for obj in media_objects:
        if not hasattr(obj, 'id'):
            continue
        content_type = ContentType.objects.get_for_model(obj)
        if content_type not in content_type_groups:
            content_type_groups[content_type] = []
        content_type_groups[content_type].append(obj.id)
    
    # Query all shared posts for these objects
    all_shared_posts = {}
    for content_type, object_ids in content_type_groups.items():
        shared_posts = SharedMediaPost.objects.filter(
            content_type=content_type,
            object_id__in=object_ids,
            is_active=True
        ).select_related('shared_by')
        
        for post in shared_posts:
            all_shared_posts[(content_type.id, post.object_id)] = post
    
    # Build results
    results = {}
    for obj in media_objects:
        if not hasattr(obj, 'id'):
            continue
            
        content_type = ContentType.objects.get_for_model(obj)
        cache_key = get_cache_key('sharing_status', content_type.id, obj.id)
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            results[obj.id] = cached_result
            continue
        
        # Check if shared
        shared_post = all_shared_posts.get((content_type.id, obj.id))
        
        if shared_post:
            shared_by_name = None
            if shared_post.shared_by:
                full_name = f"{shared_post.shared_by.first_name} {shared_post.shared_by.last_name}".strip()
                shared_by_name = full_name if full_name else shared_post.shared_by.email
            
            result = {
                'is_shared': True,
                'shared_post_id': shared_post.id,
                'shared_by': shared_by_name,
                'shared_at': shared_post.shared_at,
                'shared_caption': shared_post.caption,
                'shared_category': shared_post.category
            }
        else:
            result = {
                'is_shared': False,
                'shared_post_id': None,
                'shared_by': None,
                'shared_at': None,
                'shared_caption': None,
                'shared_category': None
            }
        
        # Cache the result
        cache.set(cache_key, result, CACHE_TIMEOUTS['sharing_status'])
        results[obj.id] = result
    
    return results 