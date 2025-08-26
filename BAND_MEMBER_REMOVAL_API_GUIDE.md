# Band Member Removal API Integration Guide

## Overview
This document explains how to properly integrate with the band member removal API to avoid token mismatch errors. The backend has been enhanced with detailed error logging to help debug authentication and authorization issues.

## API Endpoint
```
PATCH /api/bands/{band_id}/
```

## Authentication Requirements
- **Required Header**: `Authorization: Bearer {jwt_token}`
- **Required Header**: `is-talent: true`
- **Content-Type**: `application/json`

## Permission Rules
- **ONLY** the band creator can remove members
- The JWT token MUST belong to the user who created the band
- Band creators cannot remove themselves
- Members cannot remove other members

## Request Format

### Remove Single Member
```json
{
  "members_to_remove": [123]
}
```

### Remove Multiple Members
```json
{
  "members_to_remove": [123, 456, 789]
}
```

Where the numbers are `BandMembership.id` values, NOT user IDs.

## Frontend Validation Checklist

### 1. Pre-Request Validation
Before making the API call, verify:
```
✅ Current user is authenticated (has valid JWT token)
✅ Current user ID matches band creator ID
✅ Band data is loaded and contains creator information
✅ Member to remove is not the band creator
✅ Membership ID exists in current band data
```

### 2. Required Data Flow
```
1. Load current authenticated user info
2. Load band details (including creator info and members list)
3. Compare current user ID with band.creator.id
4. If match: Show member management UI
5. If no match: Hide member removal buttons/show permission error
```

## Example API Calls

### Get Current User Info
```
GET /api/auth/user/
Headers:
  Authorization: Bearer {token}
  is-talent: true
```

### Get Band Details
```
GET /api/bands/{band_id}/
Headers:
  Authorization: Bearer {token}
  is-talent: true

Response includes:
- band.creator.id
- band.creator.username  
- band.members_data[] with membership IDs
```

### Remove Member
```
PATCH /api/bands/{band_id}/
Headers:
  Authorization: Bearer {token}
  is-talent: true
  Content-Type: application/json

Body:
{
  "members_to_remove": [membership_id]
}
```

## Error Handling

### Token Mismatch Scenarios

#### Scenario 1: Wrong User Token
```
Current Token User: john_doe (ID: 123)
Band Creator: jane_smith (ID: 456)
Result: 403 Permission Denied
```

#### Scenario 2: Missing Talent Profile
```
User exists but no TalentUserProfile record
Result: 403 Permission Denied
```

#### Scenario 3: Invalid Membership ID
```
Membership ID doesn't exist in the band
Result: 400 Bad Request
```

### Expected Error Responses

#### Permission Denied (403)
```json
{
  "error": "Permission denied",
  "detail": "Only the band creator can update the band details and manage member roles. Current user: john_doe, Band creator: jane_smith"
}
```

#### Authentication Failed (401)
```json
{
  "error": "Authentication credentials were not provided"
}
```

#### Validation Error (400)
```json
{
  "error": "Member with ID 123 not found in this band"
}
```

## Debug Information

### Backend Logging
The backend now logs detailed information for debugging:
```
[DEBUG] Band update request - User: john_doe (ID: 123)
[DEBUG] Permission denied for band update: {
  "current_user_username": "john_doe",
  "band_creator_username": "jane_smith",
  "band_id": 5,
  "band_name": "Rock Stars"
}
```

### Frontend Debug Checks
Add these validations to your frontend:

```
console.log('Current User:', currentUser);
console.log('Band Creator:', band.creator);
console.log('User IDs Match:', currentUser.id === band.creator.id);
console.log('JWT Token:', token.substring(0, 20) + '...');
```

## Common Issues & Solutions

### Issue 1: "Token belongs to wrong user"
**Cause**: Frontend cached old token or user switched accounts
**Solution**: Refresh user authentication state before band operations

### Issue 2: "User is not band creator"
**Cause**: Non-creator trying to remove members
**Solution**: Only show member removal UI to band creators

### Issue 3: "Talent profile not found" 
**Cause**: User exists but TalentUserProfile missing
**Solution**: Ensure user has completed talent profile setup

### Issue 4: "CORS header 'is-talent' not allowed"
**Cause**: Missing custom header in CORS configuration
**Solution**: Header is now added to backend CORS_ALLOW_HEADERS

## Implementation Validation

### Test Cases to Implement

1. **Happy Path**: Band creator removes a member
   - Load band with creator token
   - Verify UI shows removal buttons
   - Remove member successfully
   - Verify member removed from list

2. **Permission Denied**: Non-creator tries to remove member
   - Load band with non-creator token
   - Verify UI hides removal buttons
   - API call should return 403 if attempted

3. **Invalid Membership**: Try to remove non-existent member
   - Send invalid membership ID
   - Should return 400 validation error

4. **Creator Self-Removal**: Creator tries to remove themselves
   - Should return validation error
   - Creator cannot be removed

### Required Frontend Components

1. **User Authentication State Management**
   - Store and validate JWT tokens
   - Fetch and cache current user info
   - Handle token expiration/refresh

2. **Permission-Based UI Rendering**
   - Show/hide member management based on creator status
   - Display clear permission messages

3. **Error Handling & User Feedback**
   - Distinguish between auth (401) and permission (403) errors
   - Show meaningful error messages to users
   - Log debug information for troubleshooting

4. **Data Consistency**
   - Refresh band data after member removal
   - Ensure UI state matches backend state

## API Response Examples

### Successful Member Removal
```json
{
  "message": "Band updated successfully",
  "band": {
    "id": 5,
    "name": "Rock Stars",
    "creator": {
      "id": 456,
      "username": "jane_smith"
    },
    "members_data": [
      {
        "id": 789,
        "username": "remaining_member",
        "role": "member"
      }
    ],
    "is_creator": true
  }
}
```

### Error Response
```json
{
  "error": "Only the band creator can update the band details and manage member roles. Current user: john_doe, Band creator: jane_smith"
}
```

## Security Notes

- Always validate permissions on both frontend AND backend
- JWT tokens should be stored securely (httpOnly cookies preferred)
- Never trust frontend-only permission checks
- Log all permission-denied attempts for security monitoring
- Implement rate limiting on member removal operations

---

**Implementation Priority:**
1. Implement user authentication validation
2. Add permission-based UI controls
3. Implement proper error handling
4. Add debug logging for troubleshooting
5. Test all error scenarios thoroughly

This guide ensures proper integration regardless of your frontend technology stack.
