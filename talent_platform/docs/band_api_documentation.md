# Band API Documentation

This document provides detailed information about the Band API endpoints available in the Talent Platform application.

## Table of Contents

1. [Authentication](#authentication)
2. [Band Management](#band-management)
   - [List All Bands](#list-all-bands)
   - [Get Band Details](#get-band-details)
   - [Create a Band](#create-a-band)
   - [Update a Band](#update-a-band)
   - [Delete a Band](#delete-a-band)
3. [Band Membership](#band-membership)
   - [Join a Band](#join-a-band)
   - [Leave a Band](#leave-a-band)
   - [Update Member Role](#update-member-role)
4. [Band Invitations](#band-invitations)
   - [Generate Invitation](#generate-invitation)
   - [List Invitations](#list-invitations)
   - [Use Invitation](#use-invitation)
   - [List Join Requests](#list-join-requests)
   - [Manage Join Request](#manage-join-request)
5. [Band Media](#band-media)
   - [List and Upload Band Media](#list-and-upload-band-media)
   - [Delete Band Media](#delete-band-media)

## Authentication

All API endpoints require authentication using JWT (JSON Web Token). Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Band Management

### List All Bands

Returns a list of all bands in the system.

- **URL**: `/api/profiles/bands/`
- **Method**: `GET`
- **Authentication Required**: Yes
- **Permissions Required**: Authenticated user

#### Success Response

- **Code**: 200 OK
- **Content Example**:

```json
[
  {
    "id": 1,
    "name": "Rock Stars",
    "description": "A rock band from New York",
    "creator_name": "john_doe",
    "member_count": 3,
    "profile_picture": "http://example.com/media/bands/rockstars.jpg"
  },
  {
    "id": 2,
    "name": "Jazz Ensemble",
    "description": "Jazz musicians collective",
    "creator_name": "jane_smith",
    "member_count": 5,
    "profile_picture": "http://example.com/media/bands/jazz.jpg"
  }
]
```

### Get Band Details

Returns detailed information about a specific band.

- **URL**: `/api/profiles/bands/{id}/`
- **Method**: `GET`
- **URL Parameters**: 
  - `id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Authenticated user

#### Success Response

- **Code**: 200 OK
- **Content Example**:

```json
{
  "id": 1,
  "name": "Rock Stars",
  "description": "A rock band from New York",
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
      "role": "member",
      "position": "Guitarist",
      "date_joined": "2023-01-16T14:30:00Z"
    }
  ],
  "genre": 1,
  "genre_name": "Rock",
  "profile_picture": "http://example.com/media/bands/rockstars.jpg",
  "contact_email": "rockstars@example.com",
  "contact_phone": "+1234567890",
  "location": "New York, USA",
  "website": "http://rockstars.example.com",
  "created_at": "2023-01-15T12:00:00Z",
  "updated_at": "2023-01-20T15:45:00Z"
}
```

#### Error Response

- **Code**: 404 Not Found
- **Content**: `{"detail": "Not found."}`

### Create a Band

Creates a new band with the authenticated user as the creator and admin.

- **URL**: `/api/profiles/bands/create/`
- **Method**: `POST`
- **Authentication Required**: Yes
- **Permissions Required**: Authenticated user with Talent role
- **Data Constraints**:

```json
{
  "name": "[band name]",
  "description": "[band description]",
  "genre": [genre_id],
  "profile_picture": "[optional file upload]",
  "contact_email": "[optional email]",
  "contact_phone": "[optional phone]",
  "location": "[optional location]",
  "website": "[optional website]"
}
```

#### Success Response

- **Code**: 201 Created
- **Content Example**:

```json
{
  "name": "New Band",
  "description": "A new band description",
  "genre": 2,
  "profile_picture": "http://example.com/media/bands/newband.jpg",
  "contact_email": "newband@example.com",
  "contact_phone": "+1987654321",
  "location": "Los Angeles, USA",
  "website": "http://newband.example.com"
}
```

#### Error Response

- **Code**: 400 Bad Request
- **Content**: `{"error": "[error message]"}`

### Update a Band

Updates an existing band's information.

- **URL**: `/api/profiles/bands/{id}/update/`
- **Method**: `PUT`
- **URL Parameters**: 
  - `id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin
- **Data Constraints**: Same as for creating a band

#### Success Response

- **Code**: 200 OK
- **Content**: Updated band details

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"detail": "You do not have permission to update this band."}`

### Delete a Band

Deletes a band. Only the creator can delete a band.

- **URL**: `/api/profiles/bands/{id}/delete/`
- **Method**: `DELETE`
- **URL Parameters**: 
  - `id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Band creator only

#### Success Response

- **Code**: 204 No Content

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"detail": "Only the creator can delete this band."}`

## Band Membership

### Join a Band

Allows a user to join a band directly (without invitation).

- **URL**: `/api/profiles/bands/{band_id}/join/`
- **Method**: `POST`
- **URL Parameters**: 
  - `band_id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Authenticated user with Talent role
- **Data Constraints**:

```json
{
  "position": "[optional position in the band]"
}
```

#### Success Response

- **Code**: 201 Created
- **Content Example**:

```json
{
  "id": 3,
  "username": "new_member",
  "email": "newmember@example.com",
  "role": "member",
  "position": "Drummer",
  "date_joined": "2023-02-01T10:15:00Z"
}
```

#### Error Response

- **Code**: 400 Bad Request
- **Content**: `{"error": "You are already a member of this band."}`

### Leave a Band

Allows a user to leave a band they are a member of. Creators cannot leave their own bands.

- **URL**: `/api/profiles/bands/{band_id}/leave/`
- **Method**: `DELETE`
- **URL Parameters**: 
  - `band_id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Authenticated user with Talent role who is a member of the band

#### Success Response

- **Code**: 204 No Content
- **Content**: `{"message": "You have left the band."}`

#### Error Response

- **Code**: 400 Bad Request
- **Content**: `{"error": "As the creator, you cannot leave the band. You must delete it instead."}`

### Update Member Role

Updates a band member's role (admin or member). Only band admins can update roles.

- **URL**: `/api/profiles/bands/{band_id}/members/{member_id}/update-role/`
- **Method**: `PATCH`
- **URL Parameters**: 
  - `band_id`: The ID of the band
  - `member_id`: The ID of the band membership to update
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin
- **Data Constraints**:

```json
{
  "role": "[admin or member]"
}
```

#### Success Response

- **Code**: 200 OK
- **Content**: Updated membership details

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can update member roles."}`

<!-- Direct member addition functionality has been removed. Members can only join via invitations -->
<!-- Band admins can no longer directly add members to bands. Instead, they must use the invitation system. -->

## Band Invitations

### Generate Invitation

Generates an invitation code for a band that can be used by others to join. Only band admins can generate invitations.

- **URL**: `/api/profiles/bands/{band_id}/invitations/generate/`
- **Method**: `POST`
- **URL Parameters**: 
  - `band_id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin
- **Data Constraints**:

```json
{
  "position": "[optional position for the invited user]"
}
```

#### Success Response

- **Code**: 201 Created
- **Content Example**:

```json
{
  "id": 1,
  "band": 1,
  "band_name": "Rock Stars",
  "created_by_name": "john_doe",
  "invitation_code": "ABC12345",
  "created_at": "2023-02-10T09:30:00Z",
  "expires_at": "2023-02-17T09:30:00Z",
  "is_used": false,
  "position": "Bassist",
  "is_valid": true
}
```

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can generate invitation codes."}`

### List Invitations

Lists all invitations for a band. Only band admins can view invitations.

- **URL**: `/api/profiles/bands/{band_id}/invitations/`
- **Method**: `GET`
- **URL Parameters**: 
  - `band_id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin

#### Success Response

- **Code**: 200 OK
- **Content Example**:

```json
[
  {
    "id": 1,
    "band": 1,
    "band_name": "Rock Stars",
    "created_by_name": "john_doe",
    "invitation_code": "ABC12345",
    "created_at": "2023-02-10T09:30:00Z",
    "expires_at": "2023-02-17T09:30:00Z",
    "is_used": false,
    "position": "Bassist",
    "is_valid": true
  },
  {
    "id": 2,
    "band": 1,
    "band_name": "Rock Stars",
    "created_by_name": "john_doe",
    "invitation_code": "XYZ67890",
    "created_at": "2023-02-11T14:45:00Z",
    "expires_at": "2023-02-18T14:45:00Z",
    "is_used": true,
    "position": "Vocalist",
    "is_valid": false
  }
]
```

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can view invitation codes."}`

### Use Invitation

Allows a user to submit a join request for a band using an invitation code. The request will need to be approved by a band admin.

- **URL**: `/api/profiles/bands/join-by-invitation/`
- **Method**: `POST`
- **Authentication Required**: Yes
- **Permissions Required**: Authenticated user with Talent role
- **Data Constraints**:

```json
{
  "invitation_code": "[the invitation code]"
}
```

#### Success Response

- **Code**: 201 Created
- **Content Example**:

```json
{
  "message": "Your request to join Rock Stars has been submitted and is pending approval.",
  "invitation": {
    "id": 1,
    "band": 1,
    "band_name": "Rock Stars",
    "created_by_name": "john_doe",
    "invitation_code": "ABC12345",
    "created_at": "2023-02-10T09:30:00Z",
    "expires_at": "2023-02-17T09:30:00Z",
    "is_used": true,
    "position": "Bassist",
    "status": "pending"
  }
}
```

#### Error Response

- **Code**: 400 Bad Request
- **Content**: `{"error": "This invitation code has expired."}`
- **Content**: `{"error": "You are already a member of this band."}`
- **Content**: `{"error": "You already have a pending join request for this band."}`

### List Join Requests

Lists all pending join requests for a band. Only band admins can view join requests.

- **URL**: `/api/profiles/bands/{band_id}/join-requests/`
- **Method**: `GET`
- **URL Parameters**: 
  - `band_id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin

#### Success Response

- **Code**: 200 OK
- **Content Example**:

```json
{
  "requests": [
    {
      "id": 1,
      "band": 1,
      "band_name": "Rock Stars",
      "created_by_name": "john_doe",
      "invitation_code": "ABC12345",
      "created_at": "2023-02-10T09:30:00Z",
      "expires_at": "2023-02-17T09:30:00Z",
      "is_used": true,
      "used_by": {
        "id": 3,
        "username": "new_member"
      },
      "position": "Bassist",
      "status": "pending",
      "original_invitation_expired": false,
      "submitted_at": "2023-02-15T11:20:00Z"
    }
  ],
  "new_requests_count": 1,
  "has_new_requests": true
}
```

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can view join requests."}`

### Manage Join Request

Approves or rejects a band join request. Only band admins can manage join requests.

- **URL**: `/api/profiles/bands/join-requests/{invitation_id}/manage/`
- **Method**: `PATCH`
- **URL Parameters**: 
  - `invitation_id`: The ID of the invitation/join request
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin
- **Data Constraints**:

```json
{
  "action": "[approve or reject]"
}
```

#### Success Response (Approve)

- **Code**: 200 OK
- **Content Example**:

```json
{
  "message": "new_member has been added to Rock Stars.",
  "membership": {
    "id": 4,
    "username": "new_member",
    "email": "newmember@example.com",
    "role": "member",
    "position": "Bassist",
    "date_joined": "2023-02-15T11:20:00Z"
  }
}
```

#### Success Response (Reject)

- **Code**: 200 OK
- **Content Example**:

```json
{
  "message": "Join request from new_member has been rejected."
}
```

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can manage join requests."}`
- **Code**: 400 Bad Request
- **Content**: `{"error": "This is not a valid pending join request."}`
- **Content**: `{"error": "Invalid action. Must be 'approve' or 'reject'."}`

## Band Media

### List and Upload Band Media

Allows listing all media for a band and uploading new media files (upload is admin-only).

- **URL**: `/api/profiles/bands/{band_id}/media/`
- **Method**: `GET` (list media), `POST` (upload media)
- **URL Parameters**: 
  - `band_id`: The ID of the band
- **Authentication Required**: Yes
- **Permissions Required**: 
  - For GET: Band member
  - For POST: Band creator or admin
- **Data Constraints** (for POST):

```json
{
  "media_file": "[file upload]",
  "name": "[media name]",
  "media_info": "[optional description]"
}
```

#### Success Response (GET)

- **Code**: 200 OK
- **Content Example**:

```json
[
  {
    "id": 1,
    "name": "Band Photo",
    "media_file": "http://example.com/media/bands/1/photo.jpg",
    "media_type": "image",
    "media_info": "Group photo from our last concert",
    "uploaded_at": "2023-03-15T14:30:00Z"
  },
  {
    "id": 2,
    "name": "Demo Track",
    "media_file": "http://example.com/media/bands/1/demo.mp3",
    "media_type": "audio",
    "media_info": "Our latest song demo",
    "uploaded_at": "2023-03-20T10:15:00Z"
  }
]
```

#### Success Response (POST)

- **Code**: 201 Created
- **Content Example**:

```json
{
  "id": 3,
  "name": "New Video",
  "media_file": "http://example.com/media/bands/1/video.mp4",
  "media_type": "video",
  "media_info": "Behind the scenes footage",
  "uploaded_at": "2023-04-01T09:45:00Z"
}
```

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can upload media."}`
- **Content**: `{"error": "You are not a member of this band."}`

### Delete Band Media

Deletes a specific media item from a band. Only band admins can delete media.

- **URL**: `/api/profiles/bands/{band_id}/media/{media_id}/delete/`
- **Method**: `DELETE`
- **URL Parameters**: 
  - `band_id`: The ID of the band
  - `media_id`: The ID of the media to delete
- **Authentication Required**: Yes
- **Permissions Required**: Band creator or admin

#### Success Response

- **Code**: 204 No Content
- **Content**: `{"message": "Media deleted successfully."}`

#### Error Response

- **Code**: 403 Forbidden
- **Content**: `{"error": "Only band admins can delete media."}`
- **Code**: 404 Not Found
- **Content**: `{"detail": "Not found."}`

---

## Error Codes

- **400 Bad Request**: The request was malformed or contained invalid parameters
- **401 Unauthorized**: Authentication is required but was not provided
- **403 Forbidden**: The authenticated user does not have permission to perform the requested action
- **404 Not Found**: The requested resource was not found
- **500 Internal Server Error**: An unexpected error occurred on the server