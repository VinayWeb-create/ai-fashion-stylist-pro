# MongoDB Database Schema

## Collections

### 1. `users`
Stores user account information and profiles.

```javascript
{
  _id: ObjectId,
  email: String (unique, lowercase),
  password_hash: String,
  profile: {
    body_type: String,  // 'slim', 'regular', 'relaxed'
    skin_tone: String,  // 'fair', 'wheatish', 'dusky', etc.
    undertone: String,  // 'warm', 'cool', 'neutral'
    lifestyle: String,  // 'student', 'office', 'mixed'
    budget_preference: String,  // 'low', 'medium', 'high'
    preferred_colors: [String],
    age_group: String  // 'young', 'adult', 'senior'
  },
  created_at: Date,
  updated_at: Date,
  is_active: Boolean
}
```

**Indexes:**
- `email`: unique ascending

---

### 2. `wardrobe`
Stores individual wardrobe items for each user.

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  name: String,
  category: String,  // 'top', 'bottom', 'footwear', 'outerwear', 'accessory', 'other'
  colors: [String],
  occasions: [String],  // 'casual', 'formal', 'party', 'ethnic'
  season: [String],  // 'spring', 'summer', 'fall', 'winter'
  owned: Boolean,  // true if user owns it, false if it's a wishlist item
  brand: String,
  image_url: String,
  shopping_links: {
    amazon: String,
    flipkart: String,
    meesho: String,
    myntra: String
  },
  outfit_id: String,  // Reference to outfit from recommendations
  added_at: Date
}
```

**Indexes:**
- `user_id`: ascending
- `user_id` + `category`: compound index

---

### 3. `insights`
Caches wardrobe analysis and gap detection results.

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  gaps: [{
    type: String,  // 'occasion_category', 'color_neutral', 'season', 'category_missing', etc.
    occasion: String,
    category: String,
    item_name: String,
    reason: String,  // Human-readable explanation
    priority: String,  // 'high', 'medium', 'low'
    shopping_query: String,
    outfits_unlocked: Number,  // How many outfit combinations this item enables
    shopping_links: Object
  }],
  balance: {
    overall_score: Number,  // 0-100
    occasion_readiness: {
      casual: Number,
      formal: Number,
      party: Number,
      ethnic: Number
    },
    category_balance: {
      top: { count: Number, percentage: Number },
      bottom: { count: Number, percentage: Number },
      footwear: { count: Number, percentage: Number },
      outerwear: { count: Number, percentage: Number },
      accessory: { count: Number, percentage: Number }
    },
    season_coverage: {
      spring: Number,
      summer: Number,
      fall: Number,
      winter: Number
    },
    color_diversity: Number  // 0-100
  },
  recommendations: [Object],
  updated_at: Date
}
```

**Indexes:**
- `user_id`: ascending

---

## Sample Data

### Sample User
```javascript
{
  email: "user@example.com",
  password_hash: "$2b$12$...",
  profile: {
    body_type: "regular",
    skin_tone: "wheatish",
    undertone: "warm",
    lifestyle: "office",
    budget_preference: "medium",
    preferred_colors: ["Blue", "Black", "White"],
    age_group: "adult"
  },
  created_at: ISODate("2026-02-08T12:00:00Z"),
  updated_at: ISODate("2026-02-08T12:00:00Z"),
  is_active: true
}
```

### Sample Wardrobe Item
```javascript
{
  user_id: ObjectId("..."),
  name: "Navy Blue Blazer",
  category: "outerwear",
  colors: ["Navy Blue"],
  occasions: ["formal", "casual"],
  season: ["spring", "fall", "winter"],
  owned: true,
  brand: "Allen Solly",
  image_url: "",
  shopping_links: {
    amazon: "https://www.amazon.in/s?k=navy+blue+blazer",
    flipkart: "https://www.flipkart.com/search?q=navy+blue+blazer"
  },
  outfit_id: "outfit_004",
  added_at: ISODate("2026-02-08T12:30:00Z")
}
```

---

## Setup Instructions

### Local MongoDB
```bash
# Install MongoDB Community Edition
# Start MongoDB service
mongod --dbpath /path/to/data

# The application will automatically create collections and indexes
```

### MongoDB Atlas (Cloud)
1. Create a free account at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create a new cluster (free tier available)
3. Create a database user
4. Whitelist your IP address (or use 0.0.0.0/0 for development)
5. Get your connection string
6. Update `.env` file:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   DATABASE_NAME=fashion_stylist
   ```

---

## Maintenance

### Backup
```bash
# Export database
mongodump --uri="mongodb://localhost:27017/fashion_stylist" --out=/backup/path

# Import database
mongorestore --uri="mongodb://localhost:27017/fashion_stylist" /backup/path/fashion_stylist
```

### Clear Test Data
```javascript
// In MongoDB shell
use fashion_stylist

// Clear all collections
db.users.deleteMany({})
db.wardrobe.deleteMany({})
db.insights.deleteMany({})
```
