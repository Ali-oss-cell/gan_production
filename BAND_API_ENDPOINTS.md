# 🎵 Band API Documentation - Frontend Implementation Guide

## 📋 **Business Logic Overview**

### **Freemium Bands Model:**
- **FREE Users**: Can JOIN existing bands using invitation codes (no subscription required)
- **PAID Users**: Can CREATE bands + generate invitation codes (requires Bands subscription)
- **One Band Rule**: Each user can only be in one band at a time

### **Access Control:**
```
WITHOUT Subscription:  ✅ Join Bands (FREE)  ❌ Create Bands
WITH Subscription:      ✅ Join Bands (FREE)  ✅ Create Bands (PAID)
```

---

## 🔗 **Base URL & Endpoint List**

**Base URL:** `https://api.gan7club.com`

### **All Band Endpoints:**
- `GET /api/profiles/bands/` - Get bands list + subscription status
- `POST /api/profiles/bands/create/` - Create new band (requires subscription)
- `POST /api/profiles/bands/{band_id}/generate-code/` - Generate invitation code (admin only)  
- `POST /api/profiles/bands/join-with-code/` - Join band with invitation code (free)
- `GET /api/profiles/bands/{band_id}/invitations/` - List band invitations (admin only)

**⚠️ CRITICAL:** Use `profiles` (plural) not `profile` (singular)

---

## 🚀 **All Backend Issues Fixed**

The following endpoints are fully functional with standardized responses:

---

## 1. **Get Bands List + Subscription Status**
```
GET /api/profiles/bands/
```

**⚠️ IMPORTANT:** Use `profiles` (plural) not `profile` (singular)

### **Required Headers:**
```
Authorization: Bearer {access_token}
is-talent: true
```

### **Response Format:**
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Rock Stars",
            "description": "Amazing rock band",
            "creator": {
                "id": 123,
                "user": {
                    "email": "creator@example.com"
                }
            },
            "creator_name": "john_doe",
            "members_count": 3,
            "profile_score": 85,
            "is_creator": true,
            "user_role": "admin"
        }
    ],
    "subscription_status": {
        "has_bands_subscription": true,
        "subscription": {
            "id": 456,
            "plan_name": "bands",
            "status": "active",
            "current_period_end": "2025-02-24T14:35:22Z"
        },
        "has_talent_profile": true,
        "is_in_band": true,
        "band_info": {
            "band_name": "Rock Stars",
            "user_role": "admin",
            "position": "Creator"
        },
        "can_create_band": false,
        "can_join_band": false,
        "message": "You are already in a band. You can only be in one band at a time."
    }
}
```

---

## 2. **Create Band**
```
POST /api/profiles/bands/create/
```

### **Required Headers:**
```
Authorization: Bearer {access_token}
is-talent: true
```

### **Request Body:**
```json
{
    "name": "New Band Name",
    "description": "Band description",
    "band_type": "Rock",
    "contact_email": "band@example.com",
    "contact_phone": "+1234567890",
    "location": "New York, NY",
    "website": "https://band.com"
}
```

### **Success Response:**
```json
{
    "success": true,
    "message": "Band 'New Band Name' created successfully!",
    "band": {
        "id": 789,
        "name": "New Band Name",
        "description": "Band description",
        "creator": {
            "id": 123,
            "user": {
                "email": "creator@example.com"
            }
        },
        "creator_name": "john_doe",
        "members_count": 1,
        "profile_score": 45,
        "is_creator": true,
        "user_role": "admin"
    }
}
```

### **Error Responses:**
```json
// No subscription
{
    "success": false,
    "error": "You need an active Bands subscription to create a band."
}

// Already in a band
{
    "success": false,
    "error": "You are already a member of 'Other Band'. Users can only be in one band at a time."
}
```

---

## 3. **Generate Invitation Code**
```
POST /api/profiles/bands/{band_id}/generate-code/
```

### **Required Headers:**
```
Authorization: Bearer {access_token}
is-talent: true
```

### **Request Body:**
```json
{
    "position": "Lead Guitar"  // Optional
}
```

### **Success Response:**
```json
{
    "success": true,
    "message": "Invitation code generated successfully. Valid for 15 minutes until 14:35:22.",
    "invitation": {
        "id": 123,
        "band": 45,
        "band_name": "Rock Stars",
        "created_by_name": "john_doe",
        "invitation_code": "ABC12345",
        "created_at": "2025-01-24T14:20:22Z",
        "expires_at": "2025-01-24T14:35:22Z",
        "is_used": false,
        "position": "Lead Guitar",
        "is_valid": true,
        "status": "pending",
        "used_by_name": null
    }
}
```

### **Error Responses:**
```json
// Not band admin
{
    "error": "Only band admins can generate invitation codes."
}

// Band not found
{
    "error": "Band not found."
}

// Generation failed
{
    "success": false,
    "error": "Failed to generate invitation code: {specific error}"
}
```

---

## 4. **Join Band with Code**
```
POST /api/profiles/bands/join-with-code/
```

### **Required Headers:**
```
Authorization: Bearer {access_token}
is-talent: true
```

### **Request Body:**
```json
{
    "invitation_code": "ABC12345"
}
```

### **Success Response:**
```json
{
    "success": true,
    "message": "You have successfully joined Rock Stars!",
    "membership": {
        "id": 789,
        "band": {
            "id": 45,
            "name": "Rock Stars"
        },
        "talent_user": {
            "id": 123,
            "user": {
                "email": "newmember@example.com"
            }
        },
        "role": "member",
        "position": "Lead Guitar",
        "joined_at": "2025-01-24T14:25:22Z"
    }
}
```

### **Error Responses:**
```json
// Invalid code
{
    "error": "Invalid invitation code."
}

// Expired code
{
    "error": "This invitation code has expired.",
    "expired_at": "2025-01-24T14:35:22Z"
}

// Already in a band
{
    "error": "You are already a member of 'Previous Band'. Users can only be in one band at a time."
}

// Code already used
{
    "error": "This invitation code has already been used."
}

// Join failed
{
    "success": false,
    "error": "Failed to join band: {specific error}"
}
```

---

## 5. **List Band Invitations**
```
GET /api/profiles/bands/{band_id}/invitations/
```

### **Required Headers:**
```
Authorization: Bearer {access_token}
is-talent: true
```

### **Response:**
```json
[
    {
        "id": 123,
        "band": 45,
        "band_name": "Rock Stars",
        "created_by_name": "john_doe",
        "invitation_code": "ABC12345",
        "created_at": "2025-01-24T14:20:22Z",
        "expires_at": "2025-01-24T14:35:22Z",
        "is_used": false,
        "position": "Lead Guitar",
        "is_valid": true,
        "status": "pending",
        "used_by_name": null,
        "time_remaining": "12 minutes"
    },
    {
        "id": 122,
        "invitation_code": "XYZ98765",
        "is_used": true,
        "is_valid": false,
        "status": "approved",
        "used_by_name": "jane@example.com",
        "time_remaining": "Expired"
    }
]
```

---

## 🔑 **Authentication & Permissions**

### **Required Headers for ALL requests:**
```
Authorization: Bearer {access_token}
is-talent: true
```

### **Permission Rules:**
- ✅ **Band Creation**: Requires active bands subscription
- ✅ **Generate Invitation**: Only band creator or admin
- ✅ **View Invitations**: Only band creator or admin  
- ✅ **Join with Code**: Any talent user (not already in a band)
- ✅ **One Band Rule**: Users can only be in one band at a time

---

## 🎯 **Key Fixes Implemented**

### **1. Invitation Generation Fixed:**
- ✅ Added comprehensive error handling
- ✅ Fixed indentation issues
- ✅ Added success/error response standardization

### **2. Bands Count Issue Fixed:**
- ✅ Fixed queryset filtering logic
- ✅ Subscription status correctly returned
- ✅ Username matching now works properly

### **3. Response Format Standardized:**
- ✅ All endpoints return `success: true/false`
- ✅ Consistent error message format
- ✅ Comprehensive data in responses

### **4. Username & Subscription Status:**
- ✅ `creator_name` now matches user's actual username
- ✅ `has_bands_subscription` correctly reflects subscription state
- ✅ Band ownership properly identified

---

## 🎯 **Frontend Implementation Strategy**

### **For FREE Users (No Subscription):**
```javascript
// Show these UI elements:
- "Join Band with Code" button (always enabled)
- "Enter Invitation Code" input field  
- "Subscribe to Create Band" upgrade prompt
- Hide "Create Band" and "Generate Code" buttons

// API calls available:
- POST /api/profiles/bands/join-with-code/ ✅
- GET /api/profiles/bands/ (to check status) ✅
```

### **For PAID Users (With Subscription):**
```javascript
// Show these UI elements:
- "Create New Band" button (enabled if not in band)
- "Generate Invitation Code" button (if band admin)
- "Join Band with Code" button  
- All band management features

// API calls available:
- POST /api/profiles/bands/create/ ✅
- POST /api/profiles/bands/{id}/generate-code/ ✅  
- POST /api/profiles/bands/join-with-code/ ✅
- GET /api/profiles/bands/{id}/invitations/ ✅
```

---

## 🧪 **Testing Scenarios**

### **Test 1: Free User Journey**
1. Free user visits bands page → sees "Join Band" option only
2. Friend sends invitation code → user enters code
3. Successful join → becomes band member
4. Can participate in band activities

### **Test 2: Paid User Journey** 
1. Subscribed user visits bands page → sees "Create Band" option
2. Creates new band → becomes band creator/admin
3. Generates invitation codes → sends to friends
4. Friends join for free using codes

### **Test 3: Subscription Status**
1. Check `has_bands_subscription` flag in API response
2. Show appropriate UI based on subscription status
3. Handle upgrade prompts for free users

---

## 📝 **Implementation Notes**

- All endpoints return `{"success": true/false}` format
- Invitation codes are 8-character alphanumeric (e.g., "ABC12345")
- Codes expire in 15 minutes
- Users can only be in one band at a time
- Band creators automatically become admins
- Only admins can generate invitation codes

---

## ✅ **Backend Status**

All issues have been resolved:
- ✅ Invitation code generation working
- ✅ Band creation with subscription validation  
- ✅ Join band with code functionality
- ✅ Proper subscription status detection
- ✅ Standardized error responses
- ✅ Username matching fixed

**Ready for frontend integration!** 🚀
