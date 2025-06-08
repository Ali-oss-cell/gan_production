# Talent Specializations API Documentation

## Overview

The Talent Specializations API allows talent users to manage their specializations. Talents can have one or more of the following specialization types:

- **Visual Worker**: For visual artists, photographers, designers, etc.
- **Expressive Worker**: For actors, models, dancers, etc.
- **Hybrid Worker**: For stunt performers, motion capture artists, etc.

## Endpoints

### Get Talent Specializations

```
GET /api/profile/specializations/
```

**Authentication Required**: Yes (JWT Token)

**Permissions**: Must be a talent user

**Response Format**:

```json
{
  "visual_worker": {
    "id": 1,
    "primary_category": "photographer",
    "years_experience": 5,
    "experience_level": "intermediate",
    "portfolio_link": "https://example.com/portfolio",
    "availability": "weekends",
    "rate_range": "$50-100/hr",
    "willing_to_relocate": true,
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z"
  },
  "expressive_worker": {
    "id": 2,
    "performer_type": "actor",
    "years_experience": 3,
    "height": 180,
    "weight": 75,
    "hair_color": "brown",
    "hair_type": "straight",
    "skin_tone": "medium",
    "eye_color": "blue",
    "eye_size": "medium",
    "eye_pattern": "solid",
    "face_shape": "oval",
    "forehead_shape": "medium",
    "lip_shape": "full",
    "eyebrow_pattern": "arched",
    "beard_color": null,
    "beard_length": null,
    "mustache_color": null,
    "mustache_length": null,
    "distinctive_facial_marks": "none",
    "distinctive_body_marks": "small tattoo on arm",
    "voice_type": "baritone",
    "body_type": "athletic",
    "availability": "full-time",
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z"
  },
  "hybrid_worker": {
    "id": 3,
    "hybrid_type": "stunt_performer",
    "years_experience": 7,
    "height": 175,
    "weight": 70,
    "hair_color": "black",
    "eye_color": "brown",
    "skin_tone": "light",
    "body_type": "athletic",
    "fitness_level": "excellent",
    "risk_levels": "high",
    "availability": "project-based",
    "willing_to_relocate": true,
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z"
  },
  "profile_complete": true
}
```

**Notes**:
- The response will only include specializations that the user has added to their profile
- The `profile_complete` field indicates whether the user has at least one specialization

### Create or Update Specializations

```
POST /api/profile/specializations/
```

**Authentication Required**: Yes (JWT Token)

**Permissions**: Must be a talent user

**Request Format**:

```json
{
  "visual_worker": {
    "primary_category": "photographer",
    "years_experience": 5,
    "experience_level": "intermediate",
    "portfolio_link": "https://example.com/portfolio",
    "availability": "weekends",
    "rate_range": "$50-100/hr",
    "willing_to_relocate": true
  },
  "expressive_worker": {
    "performer_type": "actor",
    "years_experience": 3,
    "height": 180,
    "weight": 75,
    "hair_color": "brown",
    "hair_type": "straight",
    "skin_tone": "medium",
    "eye_color": "blue",
    "eye_size": "medium",
    "eye_pattern": "solid",
    "face_shape": "oval",
    "forehead_shape": "medium",
    "lip_shape": "full",
    "eyebrow_pattern": "arched",
    "beard_color": null,
    "beard_length": null,
    "mustache_color": null,
    "mustache_length": null,
    "distinctive_facial_marks": "none",
    "distinctive_body_marks": "small tattoo on arm",
    "voice_type": "baritone",
    "body_type": "athletic",
    "availability": "full-time"
  },
  "hybrid_worker": {
    "hybrid_type": "stunt_performer",
    "years_experience": 7,
    "height": 175,
    "weight": 70,
    "hair_color": "black",
    "eye_color": "brown",
    "skin_tone": "light",
    "body_type": "athletic",
    "fitness_level": "excellent",
    "risk_levels": "high",
    "availability": "project-based",
    "willing_to_relocate": true
  },
  "test_videos": [
    {
      "media_file": "[base64 encoded file or file object]",
      "name": "Test Video 1",
      "media_info": "First test video",
      "is_test_video": true,
      "test_video_number": 1
    },
    {
      "media_file": "[base64 encoded file or file object]",
      "name": "Test Video 2",
      "media_info": "Second test video",
      "is_test_video": true,
      "test_video_number": 2
    },
    {
      "media_file": "[base64 encoded file or file object]",
      "name": "Test Video 3",
      "media_info": "Third test video",
      "is_test_video": true,
      "test_video_number": 3
    },
    {
      "media_file": "[base64 encoded file or file object]",
      "name": "Test Video 4",
      "media_info": "Fourth test video",
      "is_test_video": true,
      "test_video_number": 4
    }
  ],
  "about_yourself_video": {
    "media_file": "[base64 encoded file or file object]",
    "name": "About Yourself",
    "media_info": "Talk about yourself",
    "is_test_video": true,
    "is_about_yourself_video": true,
    "test_video_number": 5
  }
}
```

**Notes**:
- You can include one or more specialization types in a single request
- For actors and comparse, you must include 4 test videos (30 seconds each) and 1 about yourself video (60 seconds)
- Each specialization will be created if it doesn't exist, or updated if it already exists

**Response Format**:

```json
{
  "message": "Specializations updated successfully.",
  "profile_complete": true,
  "test_videos": [
    {
      "id": 1,
      "talent": 1,
      "name": "Test Video 1",
      "media_info": "First test video",
      "media_type": "video",
      "media_file": "/media/talent_media/user_1/test_video_1.mp4",
      "thumbnail": "/media/thumbnails/test_video_1_thumb.jpg",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "is_test_video": true,
      "test_video_number": 1,
      "is_about_yourself_video": false
    },
    // ... other test videos
  ]
}
```

### Delete a Specialization

```
DELETE /api/profile/specializations/?specialization=visual_worker
```

**Authentication Required**: Yes (JWT Token)

**Permissions**: Must be a talent user

**Query Parameters**:
- `specialization`: The specialization type to delete (visual_worker, expressive_worker, or hybrid_worker)

**Response Format**:

```json
{
  "message": "Visual Worker specialization removed successfully.",
  "profile_complete": true
}
```

## Reference Data

To get the available options for each field, use the Reference Data endpoint:

```
GET /api/reference-data/?type=visual_worker
```

**Query Parameters**:
- `type`: The specialization type (visual_worker, expressive_worker, or hybrid_worker)

### Visual Worker Reference Data

```json
{
  "primary_categories": [
    "photographer",
    "videographer",
    "graphic_designer",
    "illustrator",
    "animator",
    "web_designer",
    "ui_ux_designer",
    "3d_artist",
    "vfx_artist",
    "art_director",
    "creative_director",
    "other"
  ],
  "experience_levels": [
    "beginner",
    "intermediate",
    "advanced",
    "expert"
  ],
  "availability_choices": [
    "full-time",
    "part-time",
    "weekends",
    "evenings",
    "project-based"
  ],
  "rate_ranges": [
    "$25-50/hr",
    "$50-100/hr",
    "$100-150/hr",
    "$150-200/hr",
    "$200+/hr",
    "Fixed project rate"
  ]
}
```

### Expressive Worker Reference Data

```json
{
  "performer_types": [
    "actor",
    "model",
    "dancer",
    "singer",
    "musician",
    "comparse",
    "voice_actor",
    "other"
  ],
  "hair_colors": [
    "black",
    "brown",
    "blonde",
    "red",
    "gray",
    "white",
    "other"
  ],
  "hair_types": [
    "straight",
    "wavy",
    "curly",
    "coily",
    "bald"
  ],
  "skin_tones": [
    "very_light",
    "light",
    "medium",
    "medium_dark",
    "dark",
    "very_dark"
  ],
  "eye_colors": [
    "brown",
    "blue",
    "green",
    "hazel",
    "gray",
    "amber",
    "other"
  ],
  // ... other reference data fields
}
```

### Hybrid Worker Reference Data

```json
{
  "hybrid_types": [
    "stunt_performer",
    "motion_capture_artist",
    "special_effects_technician",
    "other"
  ],
  "hair_colors": [
    "black",
    "brown",
    "blonde",
    "red",
    "gray",
    "white",
    "other"
  ],
  "eye_colors": [
    "brown",
    "blue",
    "green",
    "hazel",
    "gray",
    "amber",
    "other"
  ],
  "skin_tones": [
    "very_light",
    "light",
    "medium",
    "medium_dark",
    "dark",
    "very_dark"
  ],
  "body_types": [
    "slim",
    "athletic",
    "muscular",
    "average",
    "full"
  ],
  "fitness_levels": [
    "poor",
    "fair",
    "good",
    "excellent",
    "elite"
  ],
  "risk_levels": [
    "low",
    "medium",
    "high",
    "extreme"
  ]
}
```

## Validation Rules

1. At least one specialization type must be provided when creating/updating specializations
2. For actors and comparse, 4 test videos (30 seconds each) and 1 about yourself video (60 seconds) are required
3. Test videos must be properly numbered from 1-4, and the about yourself video must be numbered 5
4. Field values must match the available options from the reference data endpoint