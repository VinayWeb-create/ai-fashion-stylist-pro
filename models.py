"""
MongoDB Models for AI Fashion Stylist
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from config import Config
import logging
import traceback
import os

logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("INITIALIZING MONGODB CONNECTION")
logger.info("=" * 80)

# Check environment variables
logger.info(f"📝 MONGODB_URI env exists: {bool(os.getenv('MONGODB_URI'))}")
logger.info(f"📝 DATABASE_NAME env: {os.getenv('DATABASE_NAME')}")

# ============================================================================
# MONGODB CONNECTION
# ============================================================================

client = None
db = None
users_collection = None
wardrobe_collection = None
insights_collection = None
MONGODB_CONNECTED = False

def connect_to_mongodb():
    """Connect to MongoDB"""
    global client, db, users_collection, wardrobe_collection, insights_collection, MONGODB_CONNECTED
    
    try:
        # Get from environment directly (not Config)
        mongodb_uri = os.getenv('MONGODB_URI','mongodb+srv://avalavinay7:Vinay@fashion.vpiocpj.mongodb.net/?appName=fashion')
        database_name = os.getenv('DATABASE_NAME', 'fashion')
        
        logger.info(f"📝 MONGODB_URI (first 70 chars): {mongodb_uri[:70] if mongodb_uri else 'NOT FOUND'}")
        logger.info(f"📝 DATABASE_NAME: {database_name}")
        
        if not mongodb_uri:
            raise Exception("MONGODB_URI environment variable not set!")
        
        logger.info("🔗 Creating MongoClient...")
        
        client = MongoClient(
            mongodb_uri,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=15000,
            retryWrites=True,
            maxPoolSize=50,
            minPoolSize=10,
            appName='fashion-stylist'
        )
        
        logger.info("🔄 Pinging MongoDB...")
        client.admin.command('ping')
        logger.info("✅ Ping successful!")
        
        logger.info(f"📦 Getting database: {database_name}")
        db = client[database_name]
        
        logger.info("📋 Creating collection references...")
        users_collection = db['users']
        wardrobe_collection = db['wardrobe']
        insights_collection = db['insights']
        
        logger.info(f"✅ users_collection: {users_collection}")
        logger.info(f"✅ wardrobe_collection: {wardrobe_collection}")
        logger.info(f"✅ insights_collection: {insights_collection}")
        
        MONGODB_CONNECTED = True
        logger.info("=" * 80)
        logger.info("✅✅✅ MONGODB CONNECTION SUCCESSFUL ✅✅✅")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ MONGODB CONNECTION FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {type(e).__name__}")
        logger.error(f"Message: {str(e)}")
        logger.error("=" * 80)
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        MONGODB_CONNECTED = False
        return False

# Connect on module load
logger.info("Attempting to connect to MongoDB...")
connect_to_mongodb()

logger.info("=" * 80)
logger.info(f"✅ MODELS INITIALIZED")
logger.info(f"   MONGODB_CONNECTED: {MONGODB_CONNECTED}")
logger.info(f"   client: {client}")
logger.info(f"   db: {db}")
logger.info(f"   users_collection: {users_collection}")
logger.info("=" * 80)

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

_db_initialized = False

def init_db():
    """Initialize database indexes"""
    global _db_initialized
    
    if _db_initialized or not MONGODB_CONNECTED:
        return
    
    try:
        logger.info("Creating indexes...")
        if users_collection:
            users_collection.create_index([('email', ASCENDING)], unique=True, sparse=True)
        if wardrobe_collection:
            wardrobe_collection.create_index([('user_id', ASCENDING)])
        if insights_collection:
            insights_collection.create_index([('user_id', ASCENDING)])
        _db_initialized = True
        logger.info("✅ Indexes created")
    except Exception as e:
        logger.error(f"Index creation error: {e}")

# ============================================================================
# USER MODEL
# ============================================================================

class User:
    """User model"""
    
    @staticmethod
    def create(email, password_hash, profile=None):
        """Create user"""
        if not MONGODB_CONNECTED or users_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            user_data = {
                'email': email.lower(),
                'password_hash': password_hash,
                'profile': profile or {},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True
            }
            result = users_collection.insert_one(user_data)
            user_data['_id'] = result.inserted_id
            logger.info(f"✅ User created: {email}")
            return user_data
        except Exception as e:
            logger.error(f"❌ Create user error: {e}")
            raise
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        if not MONGODB_CONNECTED or users_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            result = users_collection.find_one({'email': email.lower()})
            return result
        except Exception as e:
            logger.error(f"❌ Find user error: {e}")
            raise
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        if not MONGODB_CONNECTED or users_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            return users_collection.find_one({'_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"❌ Find by ID error: {e}")
            raise
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update profile"""
        if not MONGODB_CONNECTED or users_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': {'profile': profile_data, 'updated_at': datetime.utcnow()}}
            )
            return User.find_by_id(user_id)
        except Exception as e:
            logger.error(f"❌ Update profile error: {e}")
            raise

# ============================================================================
# WARDROBE ITEM MODEL
# ============================================================================

class WardrobeItem:
    """Wardrobe item model"""
    
    @staticmethod
    def create(user_id, item_data):
        """Create wardrobe item"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            item = {
                'user_id': ObjectId(user_id),
                'name': item_data.get('name', 'Item'),
                'category': item_data.get('category', 'other'),
                'colors': item_data.get('colors', []),
                'occasions': item_data.get('occasions', []),
                'season': item_data.get('season', []),
                'owned': item_data.get('owned', True),
                'brand': item_data.get('brand', ''),
                'added_at': datetime.utcnow()
            }
            result = wardrobe_collection.insert_one(item)
            item['_id'] = result.inserted_id
            return item
        except Exception as e:
            logger.error(f"❌ Create wardrobe error: {e}")
            raise
    
    @staticmethod
    def get_user_wardrobe(user_id, filters=None):
        """Get wardrobe"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            query = {'user_id': ObjectId(user_id)}
            if filters:
                if 'category' in filters:
                    query['category'] = filters['category']
                if 'owned' in filters:
                    query['owned'] = filters['owned']
            return list(wardrobe_collection.find(query).sort('added_at', DESCENDING))
        except Exception as e:
            logger.error(f"❌ Get wardrobe error: {e}")
            raise
    
    @staticmethod
    def get_wardrobe_stats(user_id):
        """Get stats"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            wardrobe = WardrobeItem.get_user_wardrobe(user_id)
            return {
                'total_items': len(wardrobe),
                'owned_items': len([i for i in wardrobe if i.get('owned')])
            }
        except Exception as e:
            logger.error(f"❌ Stats error: {e}")
            raise
    
    @staticmethod
    def remove_item(item_id, user_id):
        """Remove item"""
        if not MONGODB_CONNECTED or wardrobe_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            wardrobe_collection.delete_one({
                '_id': ObjectId(item_id),
                'user_id': ObjectId(user_id)
            })
        except Exception as e:
            logger.error(f"❌ Remove error: {e}")
            raise

# ============================================================================
# INSIGHTS MODEL
# ============================================================================

class WardrobeInsights:
    """Insights"""
    
    @staticmethod
    def save_insights(user_id, insights_data):
        """Save"""
        if not MONGODB_CONNECTED or insights_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            insights_collection.update_one(
                {'user_id': ObjectId(user_id)},
                {'$set': {
                    'gaps': insights_data.get('gaps', []),
                    'updated_at': datetime.utcnow()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"❌ Save insights error: {e}")
            raise
    
    @staticmethod
    def get_insights(user_id):
        """Get"""
        if not MONGODB_CONNECTED or insights_collection is None:
            raise Exception("MongoDB not connected")
        
        try:
            from bson import ObjectId
            return insights_collection.find_one({'user_id': ObjectId(user_id)})
        except Exception as e:
            logger.error(f"❌ Get insights error: {e}")
            raise
