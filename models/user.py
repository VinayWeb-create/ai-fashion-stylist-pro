from datetime import datetime
from bson import ObjectId
from .database import users_collection

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
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return users_collection.find_one({'_id': user_id})
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Update user profile"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        users_collection.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'profile': profile_data,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return User.find_by_id(user_id)
