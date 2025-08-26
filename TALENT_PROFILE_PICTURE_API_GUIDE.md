# Talent Profile Picture Upload API Guide

## Overview
The `TalentUserProfileView` now supports profile picture uploads with automatic cleanup of old profile pictures.

## API Endpoint
```
POST /api/profile/talent/
```

## Authentication Requirements
- **Required Header**: `Authorization: Bearer {jwt_token}`
- **Required Header**: `is-talent: true`
- **Content-Type**: `multipart/form-data` (for file uploads)

## Profile Picture Upload

### Request Format
```
POST /api/profile/talent/
Headers:
  Authorization: Bearer {jwt_token}
  is-talent: true
  Content-Type: multipart/form-data

Body (FormData):
  profile_picture: [image_file]
  # Optional: other profile fields
  first_name: "John"
  last_name: "Doe"
  aboutyou: "Description about yourself"
```

### Supported File Types
- **Images**: JPG, JPEG, PNG, GIF, WEBP
- **Max Size**: Check the `file_limits` in the GET response

### Frontend Implementation Examples

#### Using FormData (Recommended)
```javascript
const uploadProfilePicture = async (imageFile, otherData = {}) => {
  const formData = new FormData();
  formData.append('profile_picture', imageFile);
  
  // Add other profile fields if needed
  Object.keys(otherData).forEach(key => {
    formData.append(key, otherData[key]);
  });

  const response = await fetch('/api/profile/talent/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      'is-talent': 'true'
      // Don't set Content-Type - let browser set it with boundary
    },
    body: formData
  });

  return response.json();
};

// Usage
const fileInput = document.getElementById('profile-picture-input');
const file = fileInput.files[0];
if (file) {
  const result = await uploadProfilePicture(file, {
    first_name: 'John',
    aboutyou: 'Updated description'
  });
  console.log('Profile updated:', result);
}
```

#### Using HTML Form
```html
<form action="/api/profile/talent/" method="post" enctype="multipart/form-data">
  <input type="file" name="profile_picture" accept="image/*" required>
  <input type="text" name="first_name" placeholder="First Name">
  <input type="text" name="last_name" placeholder="Last Name">
  <textarea name="aboutyou" placeholder="About yourself"></textarea>
  <button type="submit">Update Profile</button>
</form>
```

### Response Format

#### Success Response (200)
```json
{
  "message": "Profile updated successfully",
  "profile": {
    "id": 123,
    "user": {
      "id": 456,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "profile_picture": "https://gan7club-spaces.fra1.cdn.digitaloceanspaces.com/media/profile_pictures/user_123_profile.jpg",
    "aboutyou": "Description about yourself",
    "city": "New York",
    "country": "USA",
    "gender": "Male",
    "date_of_birth": "1990-01-01",
    "phone": "+1234567890",
    "is_verified": false,
    "profile_complete": true,
    "account_type": "free",
    "profile_score": 85
  }
}
```

#### Error Response (400)
```json
{
  "profile_picture": ["Upload a valid image. The file you uploaded was either not an image or a corrupted image."]
}
```

## Features

### DigitalOcean Spaces Storage
- Profile pictures are automatically stored in DigitalOcean Spaces (same as other media)
- CDN delivery for fast global access
- Storage path: `media/profile_pictures/filename.jpg`
- CDN URLs: `https://gan7club-spaces.fra1.cdn.digitaloceanspaces.com/media/profile_pictures/`

### Automatic File Cleanup
- When a user uploads a new profile picture, the old one is automatically deleted
- Prevents storage buildup and saves disk space in Spaces
- Graceful error handling if old file deletion fails

### File Validation
- Automatic image validation by Django's ImageField
- File size limits enforced
- File type validation

### Debug Logging
- Server logs profile picture operations for troubleshooting
- Shows file paths and operation status

## Get Current Profile (Including Profile Picture)

### Request
```
GET /api/profile/talent/
Headers:
  Authorization: Bearer {jwt_token}
  is-talent: true
```

### Response
```json
{
  "id": 123,
  "profile_picture": "https://gan7club-spaces.fra1.cdn.digitaloceanspaces.com/media/profile_pictures/user_123_profile.jpg",
  "file_limits": {
    "max_image_size": 5242880,
    "max_video_size": 104857600,
    "allowed_image_types": ["jpg", "jpeg", "png", "gif", "webp"],
    "allowed_video_types": ["mp4", "mov", "avi"]
  },
  // ... other profile data
}
```

## Update Only Profile Picture

To update only the profile picture without changing other fields:

```javascript
const updateOnlyProfilePicture = async (imageFile) => {
  const formData = new FormData();
  formData.append('profile_picture', imageFile);

  const response = await fetch('/api/profile/talent/?partial=true', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
      'is-talent': 'true'
    },
    body: formData
  });

  return response.json();
};
```

## Error Handling

### Common Errors
1. **File too large**: Check `file_limits` from GET response
2. **Invalid file type**: Only images are accepted
3. **Missing authentication**: Ensure JWT token is provided
4. **Permission denied**: User must be a talent user

### Example Error Handling
```javascript
try {
  const result = await uploadProfilePicture(file);
  console.log('Success:', result);
} catch (error) {
  if (error.response?.status === 400) {
    // Validation errors
    console.error('Validation errors:', error.response.data);
  } else if (error.response?.status === 401) {
    // Authentication failed
    console.error('Please log in again');
  } else if (error.response?.status === 403) {
    // Permission denied
    console.error('Access denied');
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## Notes

- Profile picture uploads use `multipart/form-data` content type
- Other profile updates can use `application/json` content type
- The `partial=true` query parameter allows updating only specific fields
- Profile picture URLs are absolute URLs accessible from the frontend
- Old profile pictures are automatically cleaned up to save storage space

---

**Backend URL**: `POST /api/profile/talent/`  
**Content Type**: `multipart/form-data`  
**Authentication**: Required (JWT + is-talent header)  
**File Field**: `profile_picture`  
**Auto Cleanup**: ✅ Enabled  
**Debug Logging**: ✅ Enabled
