"""
MongoDB Models for AI Fashion Stylist
Defines database schemas and helper functions
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from config import Config

# MongoDB Connection with SSL/TLS settings
client = MongoClient(
    Config.MONGODB_URI,
    tls=True,
    tlsAllowInvalidCertificates=False,
    serverSelectionTimeoutMS=2000,
    connectTimeoutMS=2000,
    socketTimeoutMS=5000
)
db = client[Config.DATABASE_NAME]

# Collections
users_collection = db['users']
wardrobe_collection = db['wardrobe']
insights_collection = db['insights']

# Database initialization flag
_db_initialized = False

def init_db():
    """Initialize database indexes lazily to prevent startup timeouts"""
    global _db_initialized
    print("DEBUG: Entering init_db", flush=True)
    if _db_initialized:
        print("DEBUG: init_db already initialized", flush=True)
        return
    
    try:
        # Create indexes
        print("DEBUG: Starting index creation...", flush=True)
        
        # Verify collections are not None before index creation
        if users_collection is not None:
            print("DEBUG: Creating index for users_collection", flush=True)
            users_collection.create_index([('email', ASCENDING)], unique=True)
        if wardrobe_collection is not None:
            print("DEBUG: Creating index for wardrobe_collection", flush=True)
            wardrobe_collection.create_index([('user_id', ASCENDING)])
            wardrobe_collection.create_index([('user_id', ASCENDING), ('category', ASCENDING)])
        if insights_collection is not None:
            print("DEBUG: Creating index for insights_collection", flush=True)
            insights_collection.create_index([('user_id', ASCENDING)])
            
        _db_initialized = True
        print("DEBUG: Database indexes created successfully", flush=True)
    except Exception as e:
        print(f"DEBUG: Error inside models.py init_db: {e}", flush=True)

class User:
    """User model for authentication and profile"""
    
    @staticmethod
    def create(email, password_hash, profile=None):
        """Create a new user"""
        user_data = {
            'email': email.lower(),
            'password_hash': password_hash,
            'profile': profile or {
                'body_type': 'regular',
                'skin_tone': None,
                'undertone': None,
                'lifestyle': 'mixed',  # student, office, mixed
                'budget_preference': 'medium',
                'preferred_colors': [],
                'age_group': 'young'
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }
        result = users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return user_data
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return users_collection.find_one({'email': email.lower()})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        from bson import ObjectId
        return users_collection.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user profile"""
        from bson import ObjectId
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'profile': profile_data,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return User.find_by_id(user_id)

class WardrobeItem:
    """Wardrobe item model"""
    
    @staticmethod
    def create(user_id, item_data):
        """Add item to wardrobe"""
        from bson import ObjectId
        wardrobe_item = {
            'user_id': ObjectId(user_id),
            'name': item_data['name'],
            'category': item_data.get('category', 'other'),  # top, bottom, footwear, outerwear, accessory, other
            'colors': item_data.get('colors', []),
            'occasions': item_data.get('occasions', []),  # casual, formal, party, ethnic
            'season': item_data.get('season', []),  # spring, summer, fall, winter
            'owned': item_data.get('owned', True),
            'brand': item_data.get('brand', ''),
            'image_url': item_data.get('image_url', ''),
            'shopping_links': item_data.get('shopping_links', {}),
            'outfit_id': item_data.get('outfit_id', ''),  # Reference to outfit from recommendations
            'tags': item_data.get('tags', []), # User-defined tags for better organization
            'added_at': datetime.utcnow()
        }
        result = wardrobe_collection.insert_one(wardrobe_item)
        wardrobe_item['_id'] = result.inserted_id
        return wardrobe_item
    
    @staticmethod
    def get_user_wardrobe(user_id, filters=None):
        """Get all wardrobe items for a user"""
        from bson import ObjectId
        query = {'user_id': ObjectId(user_id)}
        
        if filters:
            if 'category' in filters:
                query['category'] = filters['category']
            if 'owned' in filters:
                query['owned'] = filters['owned']
            if 'occasion' in filters:
                query['occasions'] = filters['occasion']
        
        return list(wardrobe_collection.find(query).sort('added_at', DESCENDING))
    
    @staticmethod
    def mark_owned(item_id, owned_status):
        """Mark item as owned or not owned"""
        from bson import ObjectId
        wardrobe_collection.update_one(
            {'_id': ObjectId(item_id)},
            {'$set': {'owned': owned_status}}
        )
    
    @staticmethod
    def remove_item(item_id, user_id):
        """Remove item from wardrobe"""
        from bson import ObjectId
        wardrobe_collection.delete_one({
            '_id': ObjectId(item_id),
            'user_id': ObjectId(user_id)
        })
    
    @staticmethod
    def get_wardrobe_stats(user_id):
        """Get wardrobe statistics"""
        from bson import ObjectId
        wardrobe = WardrobeItem.get_user_wardrobe(user_id)
        
        stats = {
            'total_items': len(wardrobe),
            'owned_items': len([i for i in wardrobe if i.get('owned', True)]),
            'by_category': {},
            'by_occasion': {},
            'by_season': {},
            'colors': set()
        }
        
        for item in wardrobe:
            # Category stats
            category = item.get('category', 'other')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Occasion stats
            for occasion in item.get('occasions', []):
                stats['by_occasion'][occasion] = stats['by_occasion'].get(occasion, 0) + 1
            
            # Season stats
            for season in item.get('season', []):
                stats['by_season'][season] = stats['by_season'].get(season, 0) + 1
            
            # Colors
            for color in item.get('colors', []):
                stats['colors'].add(color)
        
        stats['colors'] = list(stats['colors'])
        return stats

class WardrobeInsights:
    """Wardrobe insights and gap analysis cache"""
    
    @staticmethod
    def save_insights(user_id, insights_data):
        """Save or update insights for a user"""
        from bson import ObjectId
        insights_collection.update_one(
            {'user_id': ObjectId(user_id)},
            {
                '$set': {
                    'user_id': ObjectId(user_id),
                    'gaps': insights_data.get('gaps', []),
                    'balance': insights_data.get('balance', {}),
                    'recommendations': insights_data.get('recommendations', []),
                    'updated_at': datetime.utcnow()
                }
            },
            upsert=True
        )
    
    @staticmethod
    def get_insights(user_id):
        """Get cached insights for a user"""
        from bson import ObjectId
        return insights_collection.find_one({'user_id': ObjectId(user_id)})
