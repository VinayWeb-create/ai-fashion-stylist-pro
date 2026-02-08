"""
MongoDB Models for AI Fashion Stylist
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from config import Config
import logging
import ssl
import traceback

logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("INITIALIZING MONGODB CONNECTION")
logger.info("=" * 80)

# ============================================================================
# MONGODB CONNECTION - FIXED
# ============================================================================

client = None
db = None
users_collection = None
wardrobe_collection = None
insights_collection = None
MONGODB_CONNECTED = False

def connect_to_mongodb():
    """Connect to MongoDB with error handling"""
    global client, db, users_collection, wardrobe_collection, insights_collection, MONGODB_CONNECTED
    
    try:
        mongodb_uri = Config.MONGODB_URI
        database_name = Config.DATABASE_NAME
        
        if not mongodb_uri:
            raise Exception("MONGODB_URI not configured")
        
        logger.info(f"📝 MongoDB URI: {mongodb_uri[:60]}...")
        logger.info(f"📝 Database: {database_name}")
        logger.info("🔗 Connecting to MongoDB...")
        
        # Create connection
        client = MongoClient(
            mongodb_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            retryWrites=True,
            maxPoolSize=50,
            minPoolSize=10,
            socketKeepAliveMS=30000,
            appName='fashion-stylist'
        )
        
        # Test connection
        logger.info("🔄 Testing connection...")
        client.admin.command('ping')
        logger.info("✅ Connection successful!")
        
        # Get database and collections
        db = client[database_name]
        users_collection = db['users']
        wardrobe_collection = db['wardrobe']
        insights_collection = db['insights']
        
        logger.info("✅ Collections initialized:")
        logger.info(f"   - users_collection: {users_collection}")
        logger.info(f"   - wardrobe_collection: {wardrobe_collection}")
        logger.info(f"   - insights_collection: {insights_collection}")
        
        MONGODB_CONNECTED = True
        logger.info("=" * 80)
        logger.info("✅ MONGODB READY")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ MONGODB CONNECTION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        MONGODB_CONNECTED = False
        return False

# Try to connect
connect_to_mongodb()

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

_db_initialized = False

def init_db():
    """Initialize database indexes"""
    global _db_initialized
    
    if _db_initialized:
        return
    
    if not MONGODB_CONNECTED:
        logger.warning("⚠️ Cannot initialize DB - MongoDB not connected")
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
        logger.info("✅ DB initialization complete")
    
    except Exception as e:
        logger.error(f"⚠️ Index creation failed: {e}")
        logger.error(traceback.format_exc())

# ============================================================================
# USER MODEL
# ============================================================================

class User:
    """User model for authentication and profile"""
    
    @staticmethod
    def create(email, password_hash, profile=None):
        """Create a new user"""
        logger.info(f"[User.create] Email: {email}")
        
        if not MONGODB_CONNECTED:
            logger.error("[User.create] ❌ MongoDB not connected!")
            raise Exception("Database connection failed. Check MongoDB configuration.")
        
        if users_collection is None:
            logger.error("[User.create] ❌ users_collection is None!")
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
            
            logger.info(f"[User.create] Inserting into database...")
            result = users_collection.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            
            logger.info(f"[User.create] ✅ Created: {user_data['_id']}")
            return user_data
        
        except Exception as e:
            logger.error(f"[User.create] ❌ {type(e).__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        logger.info(f"[User.find_by_email] Email: {email}")
        
        if not MONGODB_CONNECTED:
            logger.error("[User.find_by_email] ❌ MongoDB not connected!")
            raise Exception("Database connection failed. Check MongoDB configuration.")
        
        if users_collection is None:
            logger.error("[User.find_by_email] ❌ users_collection is None!")
            raise Exception("Database connection failed. Check MongoDB configuration.")
        
        try:
            logger.info(f"[User.find_by_email] Querying...")
            result = users_collection.find_one({'email': email.lower()})
            
            if result:
                logger.info(f"[User.find_by_email] ✅ Found: {result['_id']}")
            else:
                logger.info(f"[User.find_by_email] Not found")
            
            return result
        
        except Exception as e:
            logger.error(f"[User.find_by_email] ❌ {type(e).__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        logger.info(f"[User.find_by_id] ID: {user_id}")
        
        if not MONGODB_CONNECTED:
            raise Exception("Database connection failed.")
        
        if users_collection is None:
            raise Exception("Database connection failed.")
        
        try:
            from bson import ObjectId
            result = users_collection.find_one({'_id': ObjectId(user_id)})
            return result
        
        except Exception as e:
            logger.error(f"[User.find_by_id] ❌ {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user profile"""
        logger.info(f"[User.update_profile] ID: {user_id}")
        
        if not MONGODB_CONNECTED or users_collection is None:
            raise Exception("Database connection failed.")
        
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
            logger.error(f"[User.update_profile] ❌ {type(e).__name__}: {str(e)}")
            raise

# ============================================================================
# WARDROBE ITEM MODEL
# ============================================================================

class WardrobeItem:
    """Wardrobe item model"""
    
    @staticmethod
    def create(user_id, item_data):
        """Add item to wardrobe"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("Database connection failed.")
        
        try:
            from bson import ObjectId
            wardrobe_item = {
                'user_id': ObjectId(user_id),
                'name': item_data.get('name', 'Unnamed'),
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
            return wardrobe_item
        
        except Exception as e:
            logger.error(f"[WardrobeItem.create] ❌ {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_wardrobe(user_id, filters=None):
        """Get all wardrobe items for a user"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("Database connection failed.")
        
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
            
            return list(wardrobe_collection.find(query).sort('added_at', DESCENDING))
        
        except Exception as e:
            logger.error(f"[WardrobeItem.get_user_wardrobe] ❌ {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def mark_owned(item_id, owned_status):
        """Mark item as owned"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("Database connection failed.")
        
        try:
            from bson import ObjectId
            wardrobe_collection.update_one(
                {'_id': ObjectId(item_id)},
                {'$set': {'owned': owned_status}}
            )
        except Exception as e:
            logger.error(f"[WardrobeItem.mark_owned] ❌ {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def remove_item(item_id, user_id):
        """Remove item from wardrobe"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("Database connection failed.")
        
        try:
            from bson import ObjectId
            wardrobe_collection.delete_one({
                '_id': ObjectId(item_id),
                'user_id': ObjectId(user_id)
            })
        except Exception as e:
            logger.error(f"[WardrobeItem.remove_item] ❌ {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def get_wardrobe_stats(user_id):
        """Get wardrobe statistics"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("Database connection failed.")
        
        try:
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
            return stats
        
        except Exception as e:
            logger.error(f"[WardrobeItem.get_wardrobe_stats] ❌ {type(e).__name__}: {str(e)}")
            raise

# ============================================================================
# INSIGHTS MODEL
# ============================================================================

class WardrobeInsights:
    """Wardrobe insights"""
    
    @staticmethod
    def save_insights(user_id, insights_data):
        """Save insights"""
        if not MONGODB_CONNECTED or insights_collection is None:
            raise Exception("Database connection failed.")
        
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
        except Exception as e:
            logger.error(f"[WardrobeInsights.save_insights] ❌ {type(e).__name__}: {str(e)}")
            raise
    
    @staticmethod
    def get_insights(user_id):
        """Get insights"""
        if not MONGODB_CONNECTED or insights_collection is None:
            raise Exception("Database connection failed.")
        
        try:
            from bson import ObjectId
            return insights_collection.find_one({'user_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"[WardrobeInsights.get_insights] ❌ {type(e).__name__}: {str(e)}")
            raise

logger.info("=" * 80)
logger.info(f"✅ MODELS LOADED (MongoDB: {MONGODB_CONNECTED})")
logger.info("=" * 80)
