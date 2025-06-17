from django.urls import reverse


def add_share_info_to_media(request, media_item, media_type):
    """
    Add sharing information to a media item for dashboard users.
    
    Args:
        request: Django request object
        media_item: Dictionary containing media information
        media_type: String indicating the type of media (talent_media, band_media, etc.)
    
    Returns:
        Dictionary with added share information
    """
    # Check if user can share (dashboard user or admin)
    can_share = (
        request.user.is_authenticated and 
        (request.user.is_dashboard or request.user.is_dashboard_admin)
    )
    
    if can_share:
        media_item['share_info'] = {
            'can_share': True,
            'content_type': media_type,
            'object_id': media_item['id'],
            'share_url': request.build_absolute_uri(reverse('dashboard:share-media'))
        }
    else:
        media_item['share_info'] = {
            'can_share': False,
            'reason': 'Dashboard access required'
        }
    
    return media_item


def add_share_info_to_search_results(request, results_data):
    """
    Add sharing information to search results for dashboard users.
    
    Args:
        request: Django request object
        results_data: Response data from search endpoint
    
    Returns:
        Modified response data with share information
    """
    if not isinstance(results_data, dict) or 'results' not in results_data:
        return results_data
    
    # Check if user can share
    can_share = (
        request.user.is_authenticated and 
        (request.user.is_dashboard or request.user.is_dashboard_admin)
    )
    
    if not can_share:
        return results_data
    
    # Add share info to each result
    for result in results_data['results']:
        # Determine media type based on result structure
        if 'media_items' in result:
            # This is a profile with media items
            for media_item in result['media_items']:
                media_type = determine_media_type(result, media_item)
                add_share_info_to_media(request, media_item, media_type)
        
        elif 'image' in result and 'price' in result:
            # This is an item (prop, costume, etc.)
            item_type = determine_item_type(result)
            add_share_info_to_media(request, result, item_type)
    
    return results_data


def determine_media_type(profile_result, media_item):
    """
    Determine the media type based on the profile and media item.
    """
    # Check if this is band media
    if 'band_type' in profile_result or 'member_count' in profile_result:
        return 'band_media'
    
    # Default to talent media for profile-based media
    return 'talent_media'


def determine_item_type(item_result):
    """
    Determine the item type based on the result structure.
    """
    # Map common fields to item types
    if 'material' in item_result or 'used_in_movie' in item_result:
        return 'prop'
    elif 'size' in item_result or 'worn_by' in item_result:
        return 'costume'
    elif 'address' in item_result or 'capacity' in item_result:
        return 'location'
    elif 'signed_by' in item_result:
        return 'memorabilia'
    elif 'make' in item_result or 'model' in item_result:
        return 'vehicle'
    elif 'type' in item_result and 'condition' in item_result:
        return 'artistic_material'
    elif 'instrument_type' in item_result:
        return 'music_item'
    elif 'provenance' in item_result:
        return 'rare_item'
    
    # Default fallback
    return 'prop'


def get_shareable_content_info(content_type, object_id):
    """
    Get information about shareable content for validation.
    
    Args:
        content_type: String type of content
        object_id: ID of the content
    
    Returns:
        Dictionary with content information or None if not found
    """
    from profiles.models import (
        TalentMedia, BandMedia, Prop, Costume, Location, 
        Memorabilia, Vehicle, ArtisticMaterial, MusicItem, RareItem
    )
    
    type_mapping = {
        'talent_media': TalentMedia,
        'band_media': BandMedia,
        'prop': Prop,
        'costume': Costume,
        'location': Location,
        'memorabilia': Memorabilia,
        'vehicle': Vehicle,
        'artistic_material': ArtisticMaterial,
        'music_item': MusicItem,
        'rare_item': RareItem,
    }
    
    model_class = type_mapping.get(content_type)
    if not model_class:
        return None
    
    try:
        obj = model_class.objects.get(id=object_id)
        
        # Get basic info based on model type
        if hasattr(obj, 'media_file'):
            # TalentMedia or BandMedia
            return {
                'name': obj.name,
                'type': obj.media_type,
                'file_url': obj.media_file.url if obj.media_file else None,
                'owner': getattr(obj.talent, 'user', None) or getattr(obj.band, 'creator.user', None)
            }
        elif hasattr(obj, 'image'):
            # Item models
            return {
                'name': obj.name,
                'type': 'item',
                'file_url': obj.image.url if obj.image else None,
                'owner': obj.BackGroundJobsProfile.user if obj.BackGroundJobsProfile else None
            }
            
    except model_class.DoesNotExist:
        pass
    
    return None 