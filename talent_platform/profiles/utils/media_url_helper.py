def get_media_url(request, media_file):
    """
    Get the proper URL for a media file, handling both relative and absolute URLs.
    
    Args:
        request: Django request object
        media_file: Media file object (can be None)
    
    Returns:
        str: The proper URL for the media file, or None if no file
    """
    if not media_file:
        return None
    
    url = media_file.url
    
    # If the URL is already absolute (starts with http/https), return it as is
    if url.startswith(('http://', 'https://')):
        return url
    
    # If it's a relative URL, make it absolute using the request
    return request.build_absolute_uri(url)


def get_thumbnail_url(request, thumbnail):
    """
    Get the proper URL for a thumbnail, handling both relative and absolute URLs.
    
    Args:
        request: Django request object
        thumbnail: Thumbnail file object (can be None)
    
    Returns:
        str: The proper URL for the thumbnail, or None if no thumbnail
    """
    if not thumbnail:
        return None
    
    url = thumbnail.url
    
    # If the URL is already absolute (starts with http/https), return it as is
    if url.startswith(('http://', 'https://')):
        return url
    
    # If it's a relative URL, make it absolute using the request
    return request.build_absolute_uri(url) 