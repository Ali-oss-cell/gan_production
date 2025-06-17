# Band Update API Documentation

This document provides detailed information about the Band Update API endpoint available in the Talent Platform application. This endpoint allows band creators to update band information and manage member roles.

## Endpoint Details

- **URL**: `/api/profiles/bands/{id}/update/`
- **Method**: `PUT` or `PATCH` (for partial updates)
- **URL Parameters**: 
  - `id`: The ID of the band to update
- **Authentication Required**: Yes (JWT Token)
- **Permissions Required**: Only the band creator can update band details and manage member roles
- **Content-Type**: `multipart/form-data` (required for profile picture uploads)

## Request Format

The request can include the following fields:

### Basic Band Information

```json
{
  "name": "Updated Band Name",
  "description": "Updated band description",
  "contact_email": "band@example.com",
  "contact_phone": "+1234567890",
  "location": "New York, USA",
  "website": "https://bandwebsite.com"
}
```

### Profile Picture Upload

To update the band's profile picture, include a file in the `profile_picture` field of the form data.

### Member Role Management

To update member roles, include a `members` array with the following structure:

```json
{
  "members": [
    {
      "id": 1,  // The BandMembership ID (not the user ID)
      "role": "admin"  // Can be "admin" or "member"
    },
    {
      "id": 2,
      "role": "member"
    }
  ]
}
```

### Remove Members

To remove members from the band, include a `members_to_remove` array with the membership IDs:

```json
{
  "members_to_remove": [3, 4]  // Array of BandMembership IDs to remove
}
```

## Response Format

### Success Response

- **Code**: 200 OK
- **Content Example**:

```json
{
  "message": "Band updated successfully",
  "band": {
    "id": 1,
    "name": "Updated Band Name",
    "description": "Updated band description",
    "creator_name": "john_doe",
    "members": [
      {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "role": "admin",
        "position": "Creator",
        "date_joined": "2023-01-15T12:00:00Z"
      },
      {
        "id": 2,
        "username": "jane_smith",
        "email": "jane@example.com",
        "role": "admin",
        "position": "Guitarist",
        "date_joined": "2023-01-16T14:30:00Z"
      }
    ],
    "profile_picture": "http://example.com/media/bands/updated_band.jpg",
    "contact_email": "band@example.com",
    "contact_phone": "+1234567890",
    "location": "New York, USA",
    "website": "https://bandwebsite.com",
    "created_at": "2023-01-15T12:00:00Z",
    "updated_at": "2023-06-20T15:45:00Z"
  }
}
```

### Error Responses

#### Not Found

- **Code**: 404 Not Found
- **Content**: `{"detail": "Not found."}`

#### Permission Denied

- **Code**: 403 Forbidden
- **Content**: `{"detail": "Only the band creator can update the band details and manage member roles."}`

#### Validation Error

- **Code**: 400 Bad Request
- **Content Example**:

```json
{
  "error": "Cannot change the band creator's role."
}
```

Or:

```json
{
  "error": "Maximum number of admins (2) reached for this band. Current admin count: 2. Band size: 10 members."
}
```

## Important Notes

1. **Band Creator Restrictions**:
   - The band creator's role cannot be changed
   - The band creator cannot be removed from the band

2. **Admin Role Limits**:
   - Bands with less than 5 members: 1 admin (the creator)
   - Bands with 5-24 members: 2 admins maximum
   - Bands with 25+ members: 3 admins maximum

3. **Band Type**:
   - The `band_type` field cannot be changed after creation

## Examples

### Example 1: Update Basic Band Information

```javascript
const updateBandInfo = async (bandId, token, bandData) => {
  try {
    const response = await fetch(`/api/profiles/bands/${bandId}/update/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: bandData, // FormData object
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error updating band:', error);
    throw error;
  }
};

// Usage
const bandId = 1;
const formData = new FormData();
formData.append('name', 'Updated Band Name');
formData.append('description', 'New description for the band');
formData.append('contact_email', 'band@example.com');

// If you have a profile picture to upload
const fileInput = document.querySelector('input[type="file"]');
if (fileInput.files[0]) {
  formData.append('profile_picture', fileInput.files[0]);
}

updateBandInfo(bandId, userToken, formData);
```

### Example 2: Promote a Member to Admin

```javascript
const promoteMemberToAdmin = async (bandId, token, membershipId) => {
  try {
    const formData = new FormData();
    
    // Create members array with the updated role
    const membersData = JSON.stringify([{
      id: membershipId,
      role: 'admin'
    }]);
    
    formData.append('members', membersData);
    
    const response = await fetch(`/api/profiles/bands/${bandId}/update/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error promoting member:', error);
    throw error;
  }
};

// Usage
promoteMemberToAdmin(1, userToken, 2); // Promote membership with ID 2 to admin
```

### Example 3: Remove Members from Band

```javascript
const removeMembers = async (bandId, token, membershipIds) => {
  try {
    const formData = new FormData();
    
    // Add the members to remove
    formData.append('members_to_remove', JSON.stringify(membershipIds));
    
    const response = await fetch(`/api/profiles/bands/${bandId}/update/`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error removing members:', error);
    throw error;
  }
};

// Usage
removeMembers(1, userToken, [3, 4]); // Remove memberships with IDs 3 and 4
```