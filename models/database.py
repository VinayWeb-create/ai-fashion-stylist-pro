from pymongo import MongoClient, ASCENDING, DESCENDING
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

_db_initialized = False

def init_db():
    """Initialize database indexes lazily"""
    global _db_initialized
    if _db_initialized:
        return
    
    try:
        # Create indexes
        if users_collection is not None:
            users_collection.create_index([('email', ASCENDING)], unique=True)
        if wardrobe_collection is not None:
            wardrobe_collection.create_index([('user_id', ASCENDING)])
            wardrobe_collection.create_index([('user_id', ASCENDING), ('category', ASCENDING)])
        if insights_collection is not None:
            insights_collection.create_index([('user_id', ASCENDING)])
            
        _db_initialized = True
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
