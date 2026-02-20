# API Documentation

Base URL: `http://localhost:5000` (development)

All API responses follow this format:
```json
{
  "status": "success" | "error",
  "message": "...",
  "data": { ... }
}
```

---

## Authentication Endpoints

### Register User
**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "profile": {
    "body_type": "regular",
    "lifestyle": "office",
    "budget_preference": "medium",
    "age_group": "adult"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "profile": { ... }
  }
}
```

---

### Login
**POST** `/auth/login`

Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

---

### Request Magic Link
**POST** `/auth/magic-link`

Request a passwordless login link via email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Magic link sent to your email",
  "dev_token": "abc123..." // Only in development mode
}
```

---

### Verify Magic Link
**POST** `/auth/verify-magic`

Verify magic link token and log in.

**Request Body:**
```json
{
  "token": "abc123..."
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

---

### Get Current User
**GET** `/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "profile": { ... }
  }
}
```

---

### Update Profile
**PUT** `/auth/profile`

Update user profile information.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "profile": {
    "body_type": "slim",
    "skin_tone": "wheatish",
    "lifestyle": "mixed",
    "budget_preference": "high"
  }
}
```

---

## Wardrobe Endpoints

### Get Wardrobe Items
**GET** `/wardrobe/items`

Get all wardrobe items for the current user.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Query Parameters:**
- `category` (optional): Filter by category (top, bottom, footwear, etc.)
- `owned` (optional): Filter by owned status (true/false)
- `occasion` (optional): Filter by occasion

**Response:**
```json
{
  "status": "success",
  "items": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "user_id": "507f1f77bcf86cd799439012",
      "name": "Navy Blue Blazer",
      "category": "outerwear",
      "colors": ["Navy Blue"],
      "occasions": ["formal", "casual"],
      "season": ["spring", "fall", "winter"],
      "owned": true,
      "brand": "Allen Solly",
      "shopping_links": { ... },
      "added_at": "2026-02-08T12:30:00Z"
    }
  ],
  "count": 15
}
```

---

### Add Wardrobe Item
**POST** `/wardrobe/add`

Add an item to the wardrobe.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "name": "Navy Blue Blazer",
  "category": "outerwear",
  "colors": ["Navy Blue"],
  "occasions": ["formal", "casual"],
  "season": ["spring", "fall", "winter"],
  "owned": true,
  "brand": "Allen Solly",
  "shopping_links": {
    "amazon": "https://www.amazon.in/...",
    "flipkart": "https://www.flipkart.com/..."
  },
  "outfit_id": "outfit_004"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Item added to wardrobe",
  "item": { ... }
}
```

---

### Mark Item as Owned
**PUT** `/wardrobe/mark-owned/<item_id>`

Mark an item as owned or not owned.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "owned": true
}
```

---

### Remove Wardrobe Item
**DELETE** `/wardrobe/remove/<item_id>`

Remove an item from the wardrobe.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Get Wardrobe Statistics
**GET** `/wardrobe/stats`

Get wardrobe statistics and breakdown.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "stats": {
    "total_items": 25,
    "owned_items": 20,
    "by_category": {
      "top": 8,
      "bottom": 6,
      "footwear": 5,
      "outerwear": 3,
      "accessory": 3
    },
    "by_occasion": {
      "casual": 15,
      "formal": 8,
      "party": 2
    },
    "by_season": {
      "spring": 12,
      "summer": 10,
      "fall": 15,
      "winter": 8
    },
    "colors": ["Black", "White", "Navy", "Blue", "Grey"]
  }
}
```

---

## Insights Endpoints (KILLER FEATURE)

### Get Wardrobe Gaps
**GET** `/insights/gaps`

Analyze wardrobe and detect missing essentials.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "gaps": [
    {
      "type": "occasion_category",
      "occasion": "formal",
      "category": "footwear",
      "item_name": "Formal Footwear",
      "reason": "As an office professional, you need proper formal footwear to look polished and professional.",
      "priority": "high",
      "shopping_query": "formal footwear",
      "outfits_unlocked": 24,
      "shopping_links": {
        "amazon": "https://www.amazon.in/s?k=formal+footwear",
        "flipkart": "https://www.flipkart.com/search?q=formal+footwear",
        "meesho": "https://www.meesho.com/search?q=formal+footwear",
        "myntra": "https://www.myntra.com/formal+footwear"
      }
    },
    {
      "type": "color_neutral",
      "item_name": "Neutral Colored Items (Black, White)",
      "reason": "You're missing key neutral colors like Black, White. Neutrals are wardrobe foundations that match with everything and create endless outfit combinations.",
      "priority": "high",
      "shopping_query": "Black basic top",
      "outfits_unlocked": 18,
      "colors_needed": ["Black", "White"],
      "shopping_links": { ... }
    }
  ],
  "count": 8
}
```

---

### Get Wardrobe Balance
**GET** `/insights/balance`

Get wardrobe balance metrics and readiness scores.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "balance": {
    "overall_score": 72,
    "occasion_readiness": {
      "casual": 100,
      "formal": 67,
      "party": 33,
      "ethnic": 0
    },
    "category_balance": {
      "top": { "count": 8, "percentage": 32.0 },
      "bottom": { "count": 6, "percentage": 24.0 },
      "footwear": { "count": 5, "percentage": 20.0 },
      "outerwear": { "count": 3, "percentage": 12.0 },
      "accessory": { "count": 3, "percentage": 12.0 }
    },
    "season_coverage": {
      "spring": 80,
      "summer": 67,
      "fall": 100,
      "winter": 53
    },
    "color_diversity": 62
  }
}
```

---

## Recommendation Endpoint

### Get Outfit Recommendations
**POST** `/predict`

Generate outfit recommendations (works with or without authentication).

**Form Data:**
- `image`: Image file (required)
- `occasion`: casual | formal | party | ethnic
- `occasion_subtype`: Varies by occasion
- `climate`: hot | moderate | cold
- `clothing_style`: mens | womens | unisex
- `age_group`: young | adult | senior
- `body_type`: slim | regular | relaxed
- `budget`: low | medium | high
- `detect_face`: true | false
- `skin_tone`: fair | wheatish | dusky
- `undertone`: warm | cool | neutral

**Headers (optional):**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "status": "success",
  "prediction": {
    "confidence": 0.95,
    "clothing_type": "Uploaded Garment",
    "outfits": [
      {
        "id": "outfit_001",
        "name": "Classic Casual Denim",
        "description": "A timeless casual look perfect for everyday wear",
        "reasoning": "This outfit combines comfort with style, ideal for relaxed settings",
        "items": ["Blue Denim Jeans", "White Cotton T-Shirt", "Casual Sneakers"],
        "colors": ["Blue", "White"],
        "accessories": ["Sunglasses", "Wristwatch"],
        "footwear": "Casual Sneakers",
        "shopping_links": [
          {
            "item": "Blue Denim Jeans",
            "links": {
              "amazon": "https://www.amazon.in/s?k=...",
              "flipkart": "https://www.flipkart.com/search?q=...",
              "meesho": "https://www.meesho.com/search?q=..."
            }
          }
        ],
        "average_rating": 4.5
      }
    ],
    "style_tips": [
      "Choose breathable fabrics like cotton and linen for maximum comfort",
      "Light colors reflect heat better and keep you cooler",
      "Keep your look sharp with well-fitted clothing"
    ]
  },
  "user_context": {
    "authenticated": true,
    "has_wardrobe": true
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "status": "error",
  "message": "Error description"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `201`: Created
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (invalid/missing token)
- `404`: Not Found
- `500`: Internal Server Error

---

## Authentication

Include JWT token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens expire after 7 days. Refresh by logging in again.

---

## Rate Limiting

Currently no rate limiting implemented. Will be added in production.

---

## CORS

CORS is enabled for all origins in development. Configure appropriately for production.

---

## Outfit Engagement Endpoints

### Get Outfit Rating
**GET** `/outfits/<outfit_id>/rating`

Get average rating and rating count for a specific outfit.

**Response:**
```json
{
  "status": "success",
  "outfit_id": "outfit_001",
  "average_rating": 4.5,
  "total_ratings": 12
}
```

### Add Outfit Rating
**POST** `/outfits/<outfit_id>/rating`

Submit a rating from 1 to 5.

**Request Body:**
```json
{
  "rating": 5
}
```

### Get Favorites
**GET** `/outfits/favorites?device_id=<device_id>`

Get all favorited outfits associated with a client `device_id`.

### Add Favorite
**POST** `/outfits/<outfit_id>/favorite`

Add an outfit to favorites.

**Request Body:**
```json
{
  "device_id": "web-user-123"
}
```

### Remove Favorite
**DELETE** `/outfits/<outfit_id>/favorite`

Remove an outfit from favorites.

**Request Body:**
```json
{
  "device_id": "web-user-123"
}
```
