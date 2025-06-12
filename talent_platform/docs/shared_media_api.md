# Shared Media API Documentation

## Overview

The Shared Media API allows dashboard users and admins to share media content from search results to the platform gallery. This creates a Facebook-style post system where admins can curate and highlight content from the platform's users.

## Authentication

All endpoints require authentication. Most endpoints also require dashboard user or admin permissions:
- `IsDashboardUser`: Basic dashboard user access
- `IsAdminDashboardUser`: Admin dashboard user access

## Endpoints

### 1. Share Media

**POST** `/api/dashboard/share-media/`

Share media from search results to the gallery.

**Permissions:** Dashboard users and admins only

**Request Body:**
```json
{
  "content_type": "talent_media",  // Required: Type of content to share
  "object_id": 123,                // Required: ID of the content
  "caption": "Amazing work by our talent!", // Optional: Admin's commentary
  "category": "featured"           // Optional: Category for organization
}
```

**Content Types:**
- `talent_media`: User profile media (photos/videos)
- `band_media`: Band media
- `prop`: Props from background users
- `costume`: Costumes
- `location`: Locations
- `memorabilia`: Memorabilia items
- `vehicle`: Vehicles
- `artistic_material`: Artistic materials
- `music_item`: Music items
- `rare_item`: Rare items

**Categories:**
- `featured`: Featured Work
- `inspiration`: Inspiration
- `trending`: Trending
- `spotlight`: Artist Spotlight
- `general`: General (default)

**Response:**
```json
{
  "message": "Media shared successfully!",
  "shared_post": {
    "id": 1,
    "caption": "Amazing work by our talent!",
    "category": "featured",
    "shared_at": "2024-01-15T10:30:00Z",
    "shared_by_name": "Admin User",
    "shared_by_email": "admin@example.com",
    "content_info": {
      "type": "media",
      "name": "Portrait Photo",
      "media_type": "image",
      "file_url": "/media/uploads/photo.jpg",
      "thumbnail_url": "/media/thumbnails/photo_thumb.jpg"
    },
    "attribution_text": "Originally by John Doe (@john@example.com)",
    "original_owner": {
      "id": 5,
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

**Error Responses:**
- `400`: Invalid data or already shared
- `403`: Permission denied
- `404`: Content not found

---

### 2. List Shared Media (Gallery)

**GET** `/api/dashboard/shared-media/`

Get shared media for gallery display. **PUBLIC ACCESS** - Available to everyone including anonymous users (for landing page).

**Permissions:** No authentication required (public access)

**Query Parameters:**
- `category`: Filter by category (optional)
- `shared_by`: Filter by user ID who shared (optional)
- `page`: Page number for pagination
- `page_size`: Number of results per page

**Example:**
```
GET /api/dashboard/shared-media/?category=featured&page=1&page_size=10
```

**Response:**
```json
{
  "count": 25,
  "next": "http://example.com/api/dashboard/shared-media/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "caption": "Amazing work by our talent!",
      "category": "featured",
      "shared_at": "2024-01-15T10:30:00Z",
      "shared_by_name": "Admin User",
      "content_info": {
        "type": "media",
        "name": "Portrait Photo",
        "media_type": "image",
        "file_url": "/media/uploads/photo.jpg"
      },
      "attribution_text": "Originally by John Doe (@john@example.com)"
    }
  ]
}
```

---

### 3. Get Shared Media Details

**GET** `/api/dashboard/shared-media/{id}/`

Get detailed information about a specific shared media post. **PUBLIC ACCESS** - Available to everyone.

**Permissions:** No authentication required (public access)

**Response:**
```json
{
  "id": 1,
  "caption": "Amazing work by our talent!",
  "category": "featured",
  "shared_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "shared_by_name": "Admin User",
  "shared_by_email": "admin@example.com",
  "content_info": {
    "type": "media",
    "name": "Portrait Photo",
    "media_type": "image",
    "file_url": "/media/uploads/photo.jpg",
    "thumbnail_url": "/media/thumbnails/photo_thumb.jpg"
  },
  "attribution_text": "Originally by John Doe (@john@example.com)",
  "original_owner": {
    "id": 5,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

### 4. Delete Shared Media

**DELETE** `/api/dashboard/shared-media/{id}/delete/`

Delete a shared media post. Users can only delete their own posts, admins can delete any.

**Permissions:** Dashboard users and admins

**Response:**
```json
{
  "message": "Shared media deleted successfully"
}
```

**Error Responses:**
- `403`: Can only delete your own posts
- `404`: Shared media not found

---

### 5. My Shared Media

**GET** `/api/dashboard/my-shared-media/`

Get all shared media posts by the current user.

**Permissions:** Dashboard users and admins

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "caption": "Amazing work by our talent!",
      "category": "featured",
      "shared_at": "2024-01-15T10:30:00Z",
      "shared_by_name": "Admin User",
      "shared_by_email": "admin@example.com",
      "content_info": {...},
      "attribution_text": "Originally by John Doe (@john@example.com)",
      "original_owner": {...}
    }
  ]
}
```

---

### 6. Shared Media Statistics

**GET** `/api/dashboard/shared-media/stats/`

Get statistics about shared media (admin only).

**Permissions:** Admin dashboard users only

**Response:**
```json
{
  "total_shared": 42,
  "by_category": {
    "featured": 15,
    "inspiration": 10,
    "trending": 8,
    "spotlight": 5,
    "general": 4
  },
  "by_content_type": {
    "talentmedia": 25,
    "bandmedia": 10,
    "prop": 4,
    "costume": 3
  },
  "top_sharers": [
    {
      "shared_by__first_name": "Admin",
      "shared_by__last_name": "User",
      "shared_by__email": "admin@example.com",
      "count": 15
    }
  ]
}
```

---

## Integration with Search Results

When dashboard users perform searches, the search results automatically include share information for each media item:

```json
{
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "media_items": [
        {
          "id": 123,
          "name": "Portrait Photo",
          "media_type": "image",
          "media_file": "/media/uploads/photo.jpg",
          "share_info": {
            "can_share": true,
            "content_type": "talent_media",
            "object_id": 123,
            "share_url": "/api/dashboard/share-media/"
          }
        }
      ]
    }
  ]
}
```

## Usage Examples

### Frontend Implementation

#### Sharing from Search Results
```javascript
// Share media from search results
async function shareMedia(contentType, objectId, caption, category = 'general') {
  const response = await fetch('/api/dashboard/share-media/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      content_type: contentType,
      object_id: objectId,
      caption: caption,
      category: category
    })
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log('Shared successfully:', data);
  }
}

// Usage in search results
shareMedia('talent_media', 123, 'Amazing portrait work!', 'featured');
```

#### Gallery Display
```javascript
// Get shared media for gallery
async function getGalleryPosts(category = null, page = 1) {
  let url = `/api/dashboard/shared-media/?page=${page}`;
  if (category) {
    url += `&category=${category}`;
  }
  
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// Display in gallery
const galleryPosts = await getGalleryPosts('featured');
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `201`: Created (for sharing)
- `400`: Bad Request (validation errors)
- `403`: Forbidden (permission denied)
- `404`: Not Found
- `500`: Internal Server Error

Error responses include descriptive messages:

```json
{
  "error": "You have already shared this media"
}
```

## Rate Limiting

Shared media endpoints are subject to the platform's rate limiting:
- Dashboard users: 200 requests/hour
- Admin dashboard users: 300 requests/hour

## Notes

- Shared posts use soft deletion (marked as `is_active=False`)
- Each user can only share the same content once
- Original media files are not duplicated
- Attribution to original creators is automatically generated
- All shared content maintains links to original owners 