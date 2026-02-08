"""
MongoDB Models for AI Fashion Stylist
Defines database schemas and helper functions
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from config import Config
import logging
import ssl

logger = logging.getLogger(__name__)

logger.info("Initializing MongoDB connection...")

# ============================================================================
# MONGODB CONNECTION - FIXED SSL/TLS ISSUE
# ============================================================================

try:
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    # Connection string with proper parameters
    mongodb_uri = Config.MONGODB_URI
    
    logger.info(f"Connecting to MongoDB: {mongodb_uri[:50]}...")
    
    client = MongoClient(
        mongodb_uri,
        # SSL/TLS settings
        ssl=True,
        ssl_cert_reqs='CERT_REQUIRED',
        tlsAllowInvalidCertificates=False,
        tlsAllowInvalidHostnames=False,
        
        # Connection timeout settings - INCREASED
        serverSelectionTimeoutMS=10000,  # 10 seconds
        connectTimeoutMS=10000,           # 10 seconds
        socketTimeoutMS=10000,            # 10 seconds
        
        # Retry settings
        retryWrites=True,
        maxPoolSize=50,
        minPoolSize=10,
        
        # Keep alive
        socketKeepAliveMS=30000,
        
        # Application name
        appName='fashion-stylist'
    )
    
    # Test connection
    logger.info("Testing MongoDB connection...")
    client.admin.command('ping')
    logger.info("✅ MongoDB connection successful!")
    
    # Get database
    db = client[Config.DATABASE_NAME]
    logger.info(f"✅ Connected to database: {Config.DATABASE_NAME}")

except Exception as e:
    logger.error(f"❌ MongoDB connection FAILED: {str(e)}")
    logger.error("This is a critical error - please check:")
    logger.error("1. MONGODB_URI environment variable is correct")
    logger.error("2. MongoDB Atlas IP whitelist includes 0.0.0.0/0")
    logger.error("3. Network connectivity is available")
    logger.error("4. SSL/TLS certificates are valid")
    db = None
    client = None

# ============================================================================
# COLLECTIONS
# ============================================================================

users_collection = db['users'] if db else None
wardrobe_collection = db['wardrobe'] if db else None
insights_collection = db['insights'] if db else None

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

_db_initialized = False

def init_db():
    """Initialize database indexes"""
    global _db_initialized
    
    if _db_initialized or not db:
        return
    
    try:
        logger.info("Creating database indexes...")
        
        if users_collection:
            users_collection.create_index([('email', ASCENDING)], unique=True, sparse=True)
            logger.info("✅ Email index created")
        
        if wardrobe_collection:
            wardrobe_collection.create_index([('user_id', ASCENDING)])
            wardrobe_collection.create_index([('user_id', ASCENDING), ('category', ASCENDING)])
            logger.info("✅ Wardrobe indexes created")
        
        if insights_collection:
            insights_collection.create_index([('user_id', ASCENDING)])
            logger.info("✅ Insights index created")
        
        _db_initialized = True
        logger.info("✅ Database initialization complete")
    
    except Exception as e:
        logger.error(f"⚠️ Database initialization failed: {e}")

# ============================================================================
# USER MODEL
# ============================================================================

class User:
    """User model for authentication and profile"""
    
    @staticmethod
    def create(email, password_hash, profile=None):
        """Create a new user"""
        if not users_collection:
            raise Exception("Database connection failed. Check MongoDB configuration.")
        
        try:
            user_data = {
                'email': email.lower(),
                'password_hash': password_hash,
                'profile': profile or {
                    'body_type': 'regular',
                    'skin_tone': None,
                    'undertone': None,
                    'lifestyle': 'mixed',
                    'budget_preference': 'medium',
                    'preferred_colors': [],
                    'age_group': 'adult'
                },
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True
            }
            result = users_collection.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            logger.info(f"✅ User created: {email}")
            return user_data
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        if not users_collection:
            logger.error("Database connection not available")
            return None
        
        try:
            result = users_collection.find_one({'email': email.lower()})
            if result:
                logger.info(f"✅ User found: {email}")
            else:
                logger.info(f"User not found: {email}")
            return result
        except Exception as e:
            logger.error(f"Error finding user by email: {str(e)}")
            raise
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        if not users_collection:
            logger.error("Database connection not available")
            return None
        
        try:
            from bson import ObjectId
            return users_collection.find_one({'_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            raise
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user profile"""
        if not users_collection:
            raise Exception("Database connection failed")
        
        try:
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
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            raise

# ============================================================================
# WARDROBE ITEM MODEL
# ============================================================================

class WardrobeItem:
    """Wardrobe item model"""
    
    @staticmethod
    def create(user_id, item_data):
        """Add item to wardrobe"""
        if not wardrobe_collection:
            raise Exception("Database connection failed")
        
        try:
            from bson import ObjectId
            wardrobe_item = {
                'user_id': ObjectId(user_id),
                'name': item_data.get('name', 'Unnamed Item'),
                'category': item_data.get('category', 'other'),
                'colors': item_data.get('colors', []),
                'occasions': item_data.get('occasions', []),
                'season': item_data.get('season', []),
                'owned': item_data.get('owned', True),
                'brand': item_data.get('brand', ''),
                'image_url': item_data.get('image_url', ''),
                'shopping_links': item_data.get('shopping_links', {}),
                'outfit_id': item_data.get('outfit_id', ''),
                'added_at': datetime.utcnow()
            }
            result = wardrobe_collection.insert_one(wardrobe_item)
            wardrobe_item['_id'] = result.inserted_id
            logger.info(f"✅ Wardrobe item created: {item_data.get('name')}")
            return wardrobe_item
        except Exception as e:
            logger.error(f"Error creating wardrobe item: {str(e)}")
            raise
    
    @staticmethod
    def get_user_wardrobe(user_id, filters=None):
        """Get all wardrobe items for a user"""
        if not wardrobe_collection:
            logger.error("Database connection not available")
            return []
        
        try:
            from bson import ObjectId
            query = {'user_id': ObjectId(user_id)}
            
            if filters:
                if 'category' in filters:
                    query['category'] = filters['category']
                if 'owned' in filters:
                    query['owned'] = filters['owned']
                if 'occasion' in filters:
                    query['occasions'] = filters['occasion']
            
            items = list(wardrobe_collection.find(query).sort('added_at', DESCENDING))
            logger.info(f"✅ Found {len(items)} wardrobe items")
            return items
        except Exception as e:
            logger.error(f"Error getting wardrobe: {str(e)}")
            raise
    
    @staticmethod
    def mark_owned(item_id, owned_status):
        """Mark item as owned or not owned"""
        if not wardrobe_collection:
            raise Exception("Database connection failed")
        
        try:
            from bson import ObjectId
            wardrobe_collection.update_one(
                {'_id': ObjectId(item_id)},
                {'$set': {'owned': owned_status}}
            )
            logger.info(f"✅ Item marked as {'owned' if owned_status else 'not owned'}")
        except Exception as e:
            logger.error(f"Error marking item owned: {str(e)}")
            raise
    
    @staticmethod
    def remove_item(item_id, user_id):
        """Remove item from wardrobe"""
        if not wardrobe_collection:
            raise Exception("Database connection failed")
        
        try:
            from bson import ObjectId
            result = wardrobe_collection.delete_one({
                '_id': ObjectId(item_id),
                'user_id': ObjectId(user_id)
            })
            logger.info(f"✅ Item removed (deleted: {result.deleted_count})")
        except Exception as e:
            logger.error(f"Error removing item: {str(e)}")
            raise
    
    @staticmethod
    def get_wardrobe_stats(user_id):
        """Get wardrobe statistics"""
        if not wardrobe_collection:
            logger.error("Database connection not available")
            return {}
        
        try:
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
                category = item.get('category', 'other')
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
                
                for occasion in item.get('occasions', []):
                    stats['by_occasion'][occasion] = stats['by_occasion'].get(occasion, 0) + 1
                
                for season in item.get('season', []):
                    stats['by_season'][season] = stats['by_season'].get(season, 0) + 1
                
                for color in item.get('colors', []):
                    stats['colors'].add(color)
            
            stats['colors'] = list(stats['colors'])
            logger.info(f"✅ Stats calculated: {stats['total_items']} items")
            return stats
        except Exception as e:
            logger.error(f"Error getting wardrobe stats: {str(e)}")
            raise

# ============================================================================
# INSIGHTS MODEL
# ============================================================================

class WardrobeInsights:
    """Wardrobe insights and gap analysis cache"""
    
    @staticmethod
    def save_insights(user_id, insights_data):
        """Save or update insights for a user"""
        if not insights_collection:
            raise Exception("Database connection failed")
        
        try:
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
            logger.info(f"✅ Insights saved")
        except Exception as e:
            logger.error(f"Error saving insights: {str(e)}")
            raise
    
    @staticmethod
    def get_insights(user_id):
        """Get cached insights for a user"""
        if not insights_collection:
            logger.error("Database connection not available")
            return None
        
        try:
            from bson import ObjectId
            return insights_collection.find_one({'user_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"Error getting insights: {str(e)}")
            raise
