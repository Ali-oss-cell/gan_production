# Background Profile Picture Upload API Guide

## Overview
Background users can now upload and manage profile pictures using the same storage system as talent users (DigitalOcean Spaces with CDN delivery).

## API Endpoint
```
GET/POST /api/profile/background/
```

## Authentication Requirements
- **Required Header**: `Authorization: Bearer {jwt_token}`
- **Required Header**: `is-background: true`
- **Content-Type**: `multipart/form-data` (for file uploads)

## Get Background Profile (including profile picture)

### Request
```
GET /api/profile/background/
Headers:
  Authorization: Bearer {jwt_token}
  is-background: true
```

### Response
```json
{
  "profile": {
    "id": 123,
    "email": "background@example.com",
    "username": "background@example.com",
    "profile_picture": "https://gan7club-spaces.fra1.cdn.digitaloceanspaces.com/media/background_profile_pictures/user_123_bg.jpg",
    "country": "USA",
    "date_of_birth": "1985-05-15",
    "gender": "Male",
    "account_type": "back_ground_jobs",
    "profile_score": 75
  },
  "profile_score": {
    "total": 75,
    "account_tier": 25,
    "profile_completion": 30,
    "item_diversity": 15,
    "item_quantity": 5,
    "details": {...}
  },
  "subscription_status": {
    "has_subscription": true,
    "can_access_features": true,
    "message": "Active subscription",
    "subscription": {...}
  },
  "restrictions": {...}
}
```

## Upload/Update Profile Picture

### Request
```
POST /api/profile/background/
Headers:
  Authorization: Bearer {jwt_token}
  is-background: true
  Content-Type: multipart/form-data

Body (FormData):
  profile_picture: [image_file]
  # Optional: other profile fields
  country: "Canada"
  gender: "Female"
```

### Response
```json
{
  "message": "Background profile updated successfully",
  "profile": {
    "id": 123,
    "email": "background@example.com",
    "username": "background@example.com",
    "profile_picture": "https://gan7club-spaces.fra1.cdn.digitaloceanspaces.com/media/background_profile_pictures/user_123_bg_new.jpg",
    "country": "Canada",
    "date_of_birth": "1985-05-15",
    "gender": "Female",
    "account_type": "back_ground_jobs",
    "profile_score": 80
  }
}
```

## Frontend Implementation

### Get Profile Picture
```javascript
const getBackgroundProfile = async () => {
  const response = await fetch('/api/profile/background/', {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      'is-background': 'true'
    }
  });
  
  const data = await response.json();
  const profilePictureUrl = data.profile.profile_picture;
  
  if (profilePictureUrl) {
    document.getElementById('bg-profile-img').src = profilePictureUrl;
  } else {
    document.getElementById('bg-profile-img').src = '/default-background-avatar.png';
  }
  
  return data;
};
```

### Upload Profile Picture
```javascript
const uploadBackgroundProfilePicture = async (imageFile, otherData = {}) => {
  const formData = new FormData();
  formData.append('profile_picture', imageFile);
  
  // Add other profile fields if needed
  Object.keys(otherData).forEach(key => {
    formData.append(key, otherData[key]);
  });

  const response = await fetch('/api/profile/background/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      'is-background': 'true'
      // Don't set Content-Type - let browser set it with boundary
    },
    body: formData
  });

  return response.json();
};

// Usage example
const fileInput = document.getElementById('bg-profile-picture-input');
const file = fileInput.files[0];
if (file) {
  const result = await uploadBackgroundProfilePicture(file, {
    country: 'Canada',
    gender: 'Female'
  });
  console.log('Background profile updated:', result);
}
```

### Update Only Profile Picture
```javascript
const updateOnlyBackgroundProfilePicture = async (imageFile) => {
  const formData = new FormData();
  formData.append('profile_picture', imageFile);

  const response = await fetch('/api/profile/background/?partial=true', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      'is-background': 'true'
    },
    body: formData
  });

  return response.json();
};
```

## Features

### DigitalOcean Spaces Storage
- Profile pictures are automatically stored in DigitalOcean Spaces
- CDN delivery for fast global access
- Storage path: `media/background_profile_pictures/filename.jpg`
- CDN URLs: `https://gan7club-spaces.fra1.cdn.digitaloceanspaces.com/media/background_profile_pictures/`

### Automatic File Cleanup
- When a user uploads a new profile picture, the old one is automatically deleted
- Prevents storage buildup and saves disk space in Spaces
- Graceful error handling if old file deletion fails

### File Validation
- Automatic image validation by Django's ImageField
- File size limits enforced (same as other media files)
- File type validation

### Debug Logging
- Server logs profile picture operations for troubleshooting
- Shows file paths and operation status

## Updatable Fields

Background users can update the following fields along with profile picture:

- `profile_picture`: Image file (JPG, PNG, GIF, etc.)
- `country`: Country name (string)
- `date_of_birth`: Date in YYYY-MM-DD format
- `gender`: "Male", "Female", or "Other"

## Error Handling

### Common Errors
1. **File too large**: Check file size limits
2. **Invalid file type**: Only images are accepted
3. **Missing authentication**: Ensure JWT token is provided
4. **Permission denied**: User must be a background user (`is-background: true`)

### Example Error Response
```json
{
  "profile_picture": ["Upload a valid image. The file you uploaded was either not an image or a corrupted image."]
}
```

## Comparison with Talent Users

| Feature | Talent Users | Background Users |
|---------|-------------|------------------|
| **Endpoint** | `/api/profile/talent/` | `/api/profile/background/` |
| **Header** | `is-talent: true` | `is-background: true` |
| **Storage Path** | `profile_pictures/` | `background_profile_pictures/` |
| **Auto Cleanup** | ✅ Yes | ✅ Yes |
| **CDN Delivery** | ✅ Yes | ✅ Yes |
| **File Validation** | ✅ Yes | ✅ Yes |

## Migration Required

**Important**: After deploying this update, you need to run the migration on your server:

```bash
cd /var/www/gan7club/talent_platform
python manage.py migrate profiles
```

This will add the `profile_picture` field to the `BackGroundJobsProfile` table.

## Testing

### Test Profile Picture Upload
```bash
# Test with curl
curl -X POST "/api/profile/background/" \
  -H "Authorization: Bearer YOUR_BACKGROUND_USER_TOKEN" \
  -H "is-background: true" \
  -F "profile_picture=@test_image.jpg" \
  -F "country=Canada"
```

### Test Profile Retrieval
```bash
# Get profile including picture
curl -X GET "/api/profile/background/" \
  -H "Authorization: Bearer YOUR_BACKGROUND_USER_TOKEN" \
  -H "is-background: true"
```

---

**Backend URL**: `GET/POST /api/profile/background/`  
**Content Type**: `multipart/form-data` (for uploads)  
**Authentication**: Required (JWT + is-background header)  
**File Field**: `profile_picture`  
**Storage**: DigitalOcean Spaces (`background_profile_pictures/`)  
**Auto Cleanup**: ✅ Enabled  
**Debug Logging**: ✅ Enabled
