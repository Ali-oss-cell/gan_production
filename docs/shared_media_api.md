# Shared Media API Documentation

## Overview

The Shared Media API allows dashboard admins to share media content from search results to the platform gallery. This creates a curated gallery where admins can highlight content while maintaining the privacy of the original creators. Companies interested in the media must contact the platform to connect with the talent.

## Authentication

All endpoints require authentication. Most endpoints also require dashboard user or admin permissions:
- `IsDashboardUser`: Basic dashboard user access
- `IsAdminDashboardUser`: Admin dashboard user access

## Endpoints

### 1. Share Media

**POST** `/api/dashboard/share-media/`

Share media from search results to the gallery. Only dashboard admins can share media.

**Permissions:** Dashboard admins only

**Request Body:**
```json
{
  "content_type": "talent_media",  // Required: Type of content to share
  "object_id": 123,                // Required: ID of the content
  "caption": "Amazing work by our talent!", // Optional: Admin's commentary
  "category": "featured",          // Optional: Category for organization
  "attribution": "Talent Platform" // Optional: Attribution text, defaults to "Talent Platform"
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
    "shared_by": {
      "id": 1,
      "email": "admin@example.com",
      "first_name": "Admin",
      "last_name": "User"
    },
    "attribution": "Talent Platform",
    "content_info": {
      "type": "media",
      "name": "Portrait Photo",
      "media_type": "image",
      "file_url": "/media/uploads/photo.jpg",
      "thumbnail_url": "/media/thumbnails/photo_thumb.jpg"
    }
  }
}
```

**Error Responses:**
- `400`: Invalid data or already shared
- `403`: Permission denied (not an admin)
- `404`: Content not found

---

### 2. List Shared Media (Gallery)

**GET** `/api/dashboard/shared-media/`

Get shared media for gallery display. **PUBLIC ACCESS** - Available to everyone including anonymous users (for landing page).

**Permissions:** No authentication required (public access)

**Query Parameters:**
- `category`: Filter by category (optional)
- `shared_by`: Filter by admin ID who shared (optional)
- `content_type`: Filter by content type (optional)
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
      "shared_by": {
        "id": 1,
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User"
      },
      "attribution": "Talent Platform",
      "content_info": {
        "type": "media",
        "name": "Portrait Photo",
        "media_type": "image",
        "file_url": "/media/uploads/photo.jpg"
      }
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
  "shared_by": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User"
  },
  "attribution": "Talent Platform",
  "content_info": {
    "type": "media",
    "name": "Portrait Photo",
    "media_type": "image",
    "file_url": "/media/uploads/photo.jpg",
    "thumbnail_url": "/media/thumbnails/photo_thumb.jpg"
  }
}
```

---

### 4. Delete Shared Media

**DELETE** `/api/dashboard/shared-media/{id}/`

Delete a shared media post. Admins can delete any post.

**Permissions:** Dashboard admins only

**Response:**
```json
{
  "message": "Shared media deleted successfully"
}
```

**Error Responses:**
- `403`: Not authorized to delete this post
- `404`: Shared media not found

---

### 5. My Shared Media

**GET** `/api/dashboard/my-shared-media/`

Get all shared media posts by the current admin.

**Permissions:** Dashboard admins only

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
      "attribution": "Talent Platform",
      "content_info": {
        "type": "media",
        "name": "Portrait Photo",
        "media_type": "image",
        "file_url": "/media/uploads/photo.jpg"
      }
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

When dashboard admins perform searches, the search results automatically include share information for each media item:

```json
{
  "results": [
    {
      "id": 1,
      "name": "Portrait Photo",
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
// Share media from search results (admin only)
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
      category: category,
      attribution: "Talent Platform"
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
  
  const response = await fetch(url);
  
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
- Dashboard admins: 300 requests/hour

## Notes

- Shared posts use soft deletion (marked as `is_active=False`)
- Each admin can only share the same content once
- Original media files are not duplicated
- Original creator information is kept private
- Companies must contact the platform to connect with talent
- All shared content is attributed to the platform 