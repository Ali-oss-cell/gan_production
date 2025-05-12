# Unified Search API Documentation

## Overview

The unified search endpoint provides a single entry point for searching all types of profiles and items in the talent platform. Instead of using multiple endpoints for different entity types, this endpoint uses a `profile_type` parameter to determine what kind of entities to search for.

**Base URL:** `/api/dashboard/search/`

## Authentication

All requests to this endpoint require authentication. The endpoint is restricted to:
- Dashboard users (`is_dashboard=True`)
- Admin dashboard users (`is_dashboard=True` AND `is_staff=True`)

## Request Parameters

### Common Parameters

These parameters are used for all search requests:

| Parameter     | Type   | Required | Description                                                  |
|---------------|--------|----------|--------------------------------------------------------------|
| profile_type  | string | Yes      | The type of profile to search for (see options below)        |
| page          | int    | No       | Page number for pagination (defaults to 1)                   |
| page_size     | int    | No       | Number of results per page (defaults to system default)      |

### Profile Types

The `profile_type` parameter accepts the following values:

| Value             | Description                                   |
|-------------------|-----------------------------------------------|
| talent            | Search for TalentUserProfiles (default)       |
| visual            | Search for VisualWorkers                      |
| expressive        | Search for ExpressiveWorkers                  |
| hybrid            | Search for HybridWorkers                      |
| bands             | Search for Bands                              |
| background        | Search for BackGroundJobsProfiles             |
| props             | Search for Props items                        |
| costumes          | Search for Costume items                      |
| locations         | Search for Location items                     |
| memorabilia       | Search for Memorabilia items                  |
| vehicles          | Search for Vehicle items                      |
| artistic_materials| Search for ArtisticMaterial items             |
| music_items       | Search for MusicItem items                    |
| rare_items        | Search for RareItem items                     |

### Type-Specific Filters

Each profile type supports its own set of filters:

#### Talent Profiles (`profile_type=talent`)

| Parameter     | Type    | Description                                |
|---------------|---------|--------------------------------------------|
| gender        | string  | Filter by gender (Male, Female, Other)     |
| city          | string  | Filter by city (partial match)             |
| country       | string  | Filter by country (partial match)          |
| account_type  | string  | Filter by account type (free, silver, gold, platinum) |
| is_verified   | boolean | Filter for verified profiles               |
| age           | int     | Filter by age                              |

#### Visual Workers (`profile_type=visual`)

| Parameter           | Type    | Description                                |
|---------------------|---------|--------------------------------------------|
| primary_category    | string  | Filter by primary category (photographer, director, etc.) |
| experience_level    | string  | Filter by experience level (beginner, intermediate, etc.) |
| min_years_experience| int     | Minimum years of experience                |
| max_years_experience| int     | Maximum years of experience                |
| city                | string  | Filter by city                             |
| country             | string  | Filter by country                          |
| profile_gender      | string  | Filter by gender of associated profile     |
| profile_age         | int     | Filter by age of associated profile        |

#### Expressive Workers (`profile_type=expressive`)

| Parameter           | Type    | Description                                |
|---------------------|---------|--------------------------------------------|
| performer_type      | string  | Filter by performer type (actor, dancer, etc.) |
| min_years_experience| int     | Minimum years of experience                |
| max_years_experience| int     | Maximum years of experience                |
| hair_color          | string  | Filter by hair color                       |
| eye_color           | string  | Filter by eye color                        |
| body_type           | string  | Filter by body type                        |
| city                | string  | Filter by city                             |
| country             | string  | Filter by country                          |
| profile_gender      | string  | Filter by gender of associated profile     |
| profile_age         | int     | Filter by age of associated profile        |

#### Hybrid Workers (`profile_type=hybrid`)

| Parameter           | Type    | Description                                |
|---------------------|---------|--------------------------------------------|
| hybrid_type         | string  | Filter by hybrid type                      |
| min_years_experience| int     | Minimum years of experience                |
| max_years_experience| int     | Maximum years of experience                |
| hair_color          | string  | Filter by hair color                       |
| eye_color           | string  | Filter by eye color                        |
| skin_tone           | string  | Filter by skin tone                        |
| body_type           | string  | Filter by body type                        |
| fitness_level       | string  | Filter by fitness level                    |
| risk_levels         | string  | Filter by risk levels                      |
| city                | string  | Filter by city                             |
| country             | string  | Filter by country                          |

#### Bands (`profile_type=bands`)

| Parameter           | Type    | Description                                |
|---------------------|---------|--------------------------------------------|
| name                | string  | Filter by band name (partial match)        |
| band_type           | string  | Filter by band type (musical, theatrical, etc.) |
| location            | string  | Filter by location (partial match)         |
| min_members         | int     | Minimum number of members                  |
| max_members         | int     | Maximum number of members                  |

#### Background Profiles (`profile_type=background`)

| Parameter           | Type    | Description                                |
|---------------------|---------|--------------------------------------------|
| gender              | string  | Filter by gender                           |
| country             | string  | Filter by country                          |
| account_type        | string  | Filter by account type                     |
| min_age             | date    | Minimum age (as birth date)                |
| max_age             | date    | Maximum age (as birth date)                |

#### Item-based searches (props, costumes, locations, etc.)

Common parameters for all item types:

| Parameter           | Type    | Description                                |
|---------------------|---------|--------------------------------------------|
| name                | string  | Filter by item name (partial match)        |
| description         | string  | Filter by description (partial match)      |
| min_price           | decimal | Minimum price                              |
| max_price           | decimal | Maximum price                              |
| is_for_rent         | boolean | Available for rent                         |
| is_for_sale         | boolean | Available for sale                         |

Plus additional specific filters for each item type (see API for details).

## Response Format

The API returns a consistent response format with the following structure:

```json
{
  "count": 42,              // Total number of matching results
  "next": "URL",            // URL to the next page (null if no next page)
  "previous": "URL",        // URL to the previous page (null if no previous page)
  "results": [              // Array of results for the current page
    {
      "id": 1,              // The entity ID
      "relevance_score": 95, // Relevance score based on match quality (higher is better)
      ...                    // Entity-specific fields
    },
    ...
  ]
}
```

## Relevance Scoring

Results are automatically scored and sorted by relevance to your search criteria. The scoring system takes into account:

- Exact matches on specific fields (higher weight)
- Partial matches on text fields
- Premium account status (paid accounts ranked higher)
- Profile completeness
- Media count
- Verification status

## Examples

### Example 1: Search for female talent in London

```
GET /api/dashboard/search/?profile_type=talent&gender=Female&city=London
```

### Example 2: Search for photographers with at least 5 years experience

```
GET /api/dashboard/search/?profile_type=visual&primary_category=photographer&min_years_experience=5
```

### Example 3: Search for musical bands with at least 3 members

```
GET /api/dashboard/search/?profile_type=bands&band_type=musical&min_members=3
```

### Example 4: Search for costume items that are for rent

```
GET /api/dashboard/search/?profile_type=costumes&is_for_rent=true
```

## Error Handling

If an invalid `profile_type` is provided, the API will return a 400 Bad Request with an error message:

```json
{
  "error": "Invalid profile_type: xyz. Must be one of: talent, visual, expressive, hybrid, background, props, costumes, locations, memorabilia, vehicles, artistic_materials, music_items, rare_items, bands"
}
```

## Implementation Notes

- The search endpoint delegates the search to specialized view classes for each profile type
- Each profile type has its own filtering logic and relevance scoring algorithm
- All results are paginated to improve performance 