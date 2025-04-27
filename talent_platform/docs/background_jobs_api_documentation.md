# Background Jobs API Documentation

This document provides detailed information about the Background Jobs API endpoints available in the Talent Platform application.

## Table of Contents

1. [Authentication](#authentication)
2. [Background User Profile](#background-user-profile)
   - [Get Background User Profile](#get-background-user-profile)
3. [Background Items](#background-items)
   - [Create Background Items](#create-background-items)
   - [Item Types](#item-types)

## Authentication

All API endpoints require authentication using JWT (JSON Web Token). Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Additionally, these endpoints require the user to have a background user role. Regular talent users cannot access these endpoints.

## Background User Profile

### Get Background User Profile

Returns the profile information for the currently authenticated background user.

- **URL**: `/api/profile/background/`
- **Method**: `GET`
- **Authentication Required**: Yes
- **Permissions Required**: IsBackgroundUser

#### Success Response

- **Code**: 200 OK
- **Content Example**:

```json
{
  "id": 1,
  "email": "background@example.com",
  "username": "background_user",
  "country": "United States",
  "date_of_birth": "1985-05-15",
  "gender": "Male"
}
```

#### Error Response

- **Code**: 404 Not Found
- **Content**:

```json
{
  "detail": "Profile not found. Please create your profile first."
}
```

- **Code**: 403 Forbidden
- **Content**:

```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Background Items

Background users can create and manage various types of items that can be rented or sold to talent users.

### Create Background Items

Creates a new item of a specified type.

- **URL**: `/api/profile/background/items/`
- **Method**: `POST`
- **Authentication Required**: Yes
- **Permissions Required**: IsBackgroundUser
- **Content-Type**: `multipart/form-data` (required for image uploads)

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| item_type | string | Yes | Type of item to create (see [Item Types](#item-types)) |
| name | string | Yes | Name of the item |
| description | string | No | Description of the item |
| price | decimal | Yes | Price of the item |
| genre | integer | No | ID of the genre |
| is_for_rent | boolean | No | Whether the item is available for rent (default: false) |
| is_for_sale | boolean | No | Whether the item is available for sale (default: false) |
| image | file | Yes | Image of the item |

#### Additional Parameters by Item Type

Depending on the `item_type`, additional parameters may be required or optional:

##### Prop

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| material | string | No | Material the prop is made of |
| used_in_movie | string | No | Movie the prop was used in |
| condition | string | No | Condition of the prop |

##### Costume

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| size | string | No | Size of the costume |
| worn_by | string | No | Person who wore the costume |
| era | string | No | Historical era of the costume |

##### Location

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| address | string | No | Address of the location |
| capacity | integer | No | Capacity of the location |
| is_indoor | boolean | No | Whether the location is indoor (default: true) |

##### Memorabilia

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| signed_by | string | No | Person who signed the memorabilia |
| authenticity_certificate | file | No | Certificate of authenticity |

##### Vehicle

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| make | string | No | Make of the vehicle |
| model | string | No | Model of the vehicle |
| year | integer | No | Year of the vehicle |

##### Artistic Material

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | No | Type of artistic material |
| condition | string | No | Condition of the material |

##### Music Item

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| instrument_type | string | No | Type of musical instrument |
| used_by | string | No | Person who used the instrument |

##### Rare Item

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| provenance | string | No | Provenance of the rare item |
| is_one_of_a_kind | boolean | No | Whether the item is one of a kind (default: false) |

#### Success Response

- **Code**: 201 Created
- **Content Example** (for a prop):

```json
{
  "id": 1,
  "name": "Lightsaber Prop",
  "description": "Replica lightsaber from Star Wars",
  "price": "299.99",
  "genre": 1,
  "is_for_rent": true,
  "is_for_sale": true,
  "created_at": "2023-06-15T14:30:00Z",
  "updated_at": "2023-06-15T14:30:00Z",
  "image": "http://example.com/media/item_images/lightsaber.jpg",
  "material": "Aluminum and plastic",
  "used_in_movie": "Star Wars: The Force Awakens",
  "condition": "Excellent"
}
```

#### Error Response

- **Code**: 400 Bad Request
- **Content**:

```json
{
  "name": ["This field is required."],
  "price": ["This field is required."],
  "image": ["No file was submitted."]
}
```

- **Code**: 404 Not Found
- **Content**:

```json
{
  "error": "Back GroundJobs profile not found."
}
```

### Item Types

The following item types are supported:

- `prop`: Props used in film, theater, or other productions
- `costume`: Costumes worn by actors or performers
- `location`: Physical locations for filming or performances
- `memorabilia`: Collectible items related to entertainment
- `vehicle`: Vehicles used in productions
- `artistic_material`: Materials used for artistic creations
- `music_item`: Musical instruments or equipment
- `rare_item`: Rare or unique items of special value

## React Integration Examples

### Fetching Background User Profile

```javascript
import axios from 'axios';

const fetchBackgroundProfile = async () => {
  try {
    const token = localStorage.getItem('token'); // Assuming token is stored in localStorage
    
    const response = await axios.get('http://your-api-domain/api/profile/background/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error fetching background profile:', error);
    throw error;
  }
};
```

### Creating a New Item

```javascript
import axios from 'axios';

const createBackgroundItem = async (itemData, itemImage) => {
  try {
    const token = localStorage.getItem('token');
    
    // Create form data for multipart/form-data request
    const formData = new FormData();
    
    // Add all item data to form
    Object.keys(itemData).forEach(key => {
      formData.append(key, itemData[key]);
    });
    
    // Add image file
    formData.append('image', itemImage);
    
    const response = await axios.post(
      'http://your-api-domain/api/profile/background/items/',
      formData,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error creating background item:', error);
    throw error;
  }
};

// Example usage:
const handleSubmit = async (event) => {
  event.preventDefault();
  
  const itemData = {
    item_type: 'prop',
    name: 'Movie Prop',
    description: 'A prop from a famous movie',
    price: 199.99,
    is_for_rent: true,
    is_for_sale: true,
    material: 'Metal',
    used_in_movie: 'Famous Movie',
    condition: 'Good'
  };
  
  const imageFile = document.getElementById('image-upload').files[0];
  
  try {
    const newItem = await createBackgroundItem(itemData, imageFile);
    console.log('Item created successfully:', newItem);
    // Handle success (e.g., show success message, redirect, etc.)
  } catch (error) {
    // Handle error (e.g., show error message)
  }
};
```