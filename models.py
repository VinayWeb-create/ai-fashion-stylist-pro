"""
MongoDB Models for AI Fashion Stylist
Defines database schemas and helper functions
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
# MONGODB CONNECTION
# ============================================================================

client = None
db = None
users_collection = None
wardrobe_collection = None
insights_collection = None
MONGODB_CONNECTED = False

try:
    logger.info(f"📝 MONGODB_URI (first 80 chars): {Config.MONGODB_URI[:80]}")
    logger.info(f"📝 DATABASE_NAME: {Config.DATABASE_NAME}")
    
    logger.info("🔗 Creating MongoDB connection...")
    
    client = MongoClient(
        Config.MONGODB_URI,
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
    
    logger.info("🔄 Testing connection with ping...")
    client.admin.command('ping')
    logger.info("✅ Ping successful!")
    
    logger.info(f"📦 Getting database: {Config.DATABASE_NAME}")
    db = client[Config.DATABASE_NAME]
    
    logger.info("✅ Creating collection references...")
    users_collection = db['users']
    wardrobe_collection = db['wardrobe']
    insights_collection = db['insights']
    
    logger.info("✅ MongoDB connection successful!")
    MONGODB_CONNECTED = True
    
except Exception as e:
    logger.error("=" * 80)
    logger.error(f"❌ MONGODB CONNECTION FAILED")
    logger.error("=" * 80)
    logger.error(f"Error Type: {type(e).__name__}")
    logger.error(f"Error Message: {str(e)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    logger.error("=" * 80)
    MONGODB_CONNECTED = False

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

_db_initialized = False

def init_db():
    """Initialize database indexes"""
    global _db_initialized
    
    if _db_initialized or not MONGODB_CONNECTED:
        logger.warning("⚠️ Skipping DB initialization (not connected or already done)")
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
        logger.info(f"[User.create] Creating user: {email}")
        
        if not MONGODB_CONNECTED or not users_collection:
            logger.error("[User.create] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
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
            
            logger.info(f"[User.create] Inserting user data into collection...")
            result = users_collection.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            
            logger.info(f"[User.create] ✅ User created successfully: {email}")
            return user_data
        
        except Exception as e:
            logger.error(f"[User.create] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[User.create] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        logger.info(f"[User.find_by_email] Searching for: {email}")
        
        if not MONGODB_CONNECTED or not users_collection:
            logger.error("[User.find_by_email] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
        try:
            logger.info(f"[User.find_by_email] Querying collection...")
            result = users_collection.find_one({'email': email.lower()})
            
            if result:
                logger.info(f"[User.find_by_email] ✅ User found: {email}")
            else:
                logger.info(f"[User.find_by_email] User not found: {email}")
            
            return result
        
        except Exception as e:
            logger.error(f"[User.find_by_email] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[User.find_by_email] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        logger.info(f"[User.find_by_id] Searching for ID: {user_id}")
        
        if not MONGODB_CONNECTED or not users_collection:
            logger.error("[User.find_by_id] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
        try:
            from bson import ObjectId
            logger.info(f"[User.find_by_id] Querying collection...")
            result = users_collection.find_one({'_id': ObjectId(user_id)})
            
            if result:
                logger.info(f"[User.find_by_id] ✅ User found")
            else:
                logger.info(f"[User.find_by_id] User not found")
            
            return result
        
        except Exception as e:
            logger.error(f"[User.find_by_id] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[User.find_by_id] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user profile"""
        logger.info(f"[User.update_profile] Updating profile for: {user_id}")
        
        if not MONGODB_CONNECTED or not users_collection:
            logger.error("[User.update_profile] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
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
            logger.info(f"[User.update_profile] ✅ Profile updated")
            return User.find_by_id(user_id)
        
        except Exception as e:
            logger.error(f"[User.update_profile] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[User.update_profile] Traceback:\n{traceback.format_exc()}")
            raise

# ============================================================================
# WARDROBE ITEM MODEL
# ============================================================================

class WardrobeItem:
    """Wardrobe item model"""
    
    @staticmethod
    def create(user_id, item_data):
        """Add item to wardrobe"""
        logger.info(f"[WardrobeItem.create] Creating item: {item_data.get('name')}")
        
        if not MONGODB_CONNECTED or not wardrobe_collection:
            logger.error("[WardrobeItem.create] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
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
            logger.info(f"[WardrobeItem.create] ✅ Item created")
            return wardrobe_item
        
        except Exception as e:
            logger.error(f"[WardrobeItem.create] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeItem.create] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def get_user_wardrobe(user_id, filters=None):
        """Get all wardrobe items for a user"""
        logger.info(f"[WardrobeItem.get_user_wardrobe] Fetching items for user: {user_id}")
        
        if not MONGODB_CONNECTED or not wardrobe_collection:
            logger.error("[WardrobeItem.get_user_wardrobe] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
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
            logger.info(f"[WardrobeItem.get_user_wardrobe] ✅ Found {len(items)} items")
            return items
        
        except Exception as e:
            logger.error(f"[WardrobeItem.get_user_wardrobe] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeItem.get_user_wardrobe] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def mark_owned(item_id, owned_status):
        """Mark item as owned or not owned"""
        logger.info(f"[WardrobeItem.mark_owned] Marking item: {item_id}")
        
        if not MONGODB_CONNECTED or not wardrobe_collection:
            logger.error("[WardrobeItem.mark_owned] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
        try:
            from bson import ObjectId
            wardrobe_collection.update_one(
                {'_id': ObjectId(item_id)},
                {'$set': {'owned': owned_status}}
            )
            logger.info(f"[WardrobeItem.mark_owned] ✅ Updated")
        
        except Exception as e:
            logger.error(f"[WardrobeItem.mark_owned] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeItem.mark_owned] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def remove_item(item_id, user_id):
        """Remove item from wardrobe"""
        logger.info(f"[WardrobeItem.remove_item] Removing item: {item_id}")
        
        if not MONGODB_CONNECTED or not wardrobe_collection:
            logger.error("[WardrobeItem.remove_item] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
        try:
            from bson import ObjectId
            result = wardrobe_collection.delete_one({
                '_id': ObjectId(item_id),
                'user_id': ObjectId(user_id)
            })
            logger.info(f"[WardrobeItem.remove_item] ✅ Deleted: {result.deleted_count} items")
        
        except Exception as e:
            logger.error(f"[WardrobeItem.remove_item] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeItem.remove_item] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def get_wardrobe_stats(user_id):
        """Get wardrobe statistics"""
        logger.info(f"[WardrobeItem.get_wardrobe_stats] Calculating stats for: {user_id}")
        
        if not MONGODB_CONNECTED or not wardrobe_collection:
            logger.error("[WardrobeItem.get_wardrobe_stats] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
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
            logger.info(f"[WardrobeItem.get_wardrobe_stats] ✅ Calculated stats")
            return stats
        
        except Exception as e:
            logger.error(f"[WardrobeItem.get_wardrobe_stats] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeItem.get_wardrobe_stats] Traceback:\n{traceback.format_exc()}")
            raise

# ============================================================================
# INSIGHTS MODEL
# ============================================================================

class WardrobeInsights:
    """Wardrobe insights and gap analysis cache"""
    
    @staticmethod
    def save_insights(user_id, insights_data):
        """Save or update insights for a user"""
        logger.info(f"[WardrobeInsights.save_insights] Saving insights for: {user_id}")
        
        if not MONGODB_CONNECTED or not insights_collection:
            logger.error("[WardrobeInsights.save_insights] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
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
            logger.info(f"[WardrobeInsights.save_insights] ✅ Insights saved")
        
        except Exception as e:
            logger.error(f"[WardrobeInsights.save_insights] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeInsights.save_insights] Traceback:\n{traceback.format_exc()}")
            raise
    
    @staticmethod
    def get_insights(user_id):
        """Get cached insights for a user"""
        logger.info(f"[WardrobeInsights.get_insights] Getting insights for: {user_id}")
        
        if not MONGODB_CONNECTED or not insights_collection:
            logger.error("[WardrobeInsights.get_insights] MongoDB not connected!")
            raise Exception("Database connection failed. MongoDB not available.")
        
        try:
            from bson import ObjectId
            result = insights_collection.find_one({'user_id': ObjectId(user_id)})
            logger.info(f"[WardrobeInsights.get_insights] ✅ Retrieved insights")
            return result
        
        except Exception as e:
            logger.error(f"[WardrobeInsights.get_insights] ❌ Error: {type(e).__name__}: {str(e)}")
            logger.error(f"[WardrobeInsights.get_insights] Traceback:\n{traceback.format_exc()}")
            raise

logger.info("=" * 80)
logger.info(f"✅ MODELS MODULE READY (MongoDB Connected: {MONGODB_CONNECTED})")
logger.info("=" * 80)
