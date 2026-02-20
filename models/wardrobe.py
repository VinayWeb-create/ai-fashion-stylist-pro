from datetime import datetime
from bson import ObjectId
from pymongo import DESCENDING
from .database import wardrobe_collection, insights_collection

class WardrobeItem:
    """Wardrobe item model"""
    
    @staticmethod
    def create(user_id, item_data):
        """Add item to wardrobe"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        wardrobe_item = {
            'user_id': user_id,
            'name': item_data['name'],
            'category': item_data.get('category', 'other'),
            'colors': item_data.get('colors', []),
            'occasions': item_data.get('occasions', []),
            'season': item_data.get('season', []),
            'owned': item_data.get('owned', True),
            'brand': item_data.get('brand', ''),
            'image_url': item_data.get('image_url', ''),
            'shopping_links': item_data.get('shopping_links', {}),
            'outfit_id': item_data.get('outfit_id', ''),
            'tags': item_data.get('tags', []),
            'added_at': datetime.utcnow()
        }
        result = wardrobe_collection.insert_one(wardrobe_item)
        wardrobe_item['_id'] = result.inserted_id
        return wardrobe_item
    
    @staticmethod
    def get_user_wardrobe(user_id, filters=None):
        """Get all wardrobe items for a user"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        query = {'user_id': user_id}
        
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
        if isinstance(item_id, str):
            item_id = ObjectId(item_id)
            
        wardrobe_collection.update_one(
            {'_id': item_id},
            {'$set': {'owned': owned_status}}
        )
    
    @staticmethod
    def remove_item(item_id, user_id):
        """Remove item from wardrobe"""
        if isinstance(item_id, str):
            item_id = ObjectId(item_id)
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        wardrobe_collection.delete_one({
            '_id': item_id,
            'user_id': user_id
        })
    
    @staticmethod
    def get_wardrobe_stats(user_id):
        """Get wardrobe statistics"""
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

class WardrobeInsights:
    """Wardrobe insights and gap analysis cache"""
    
    @staticmethod
    def save_insights(user_id, insights_data):
        """Save or update insights for a user"""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        insights_collection.update_one(
            {'user_id': user_id},
            {
                '$set': {
                    'user_id': user_id,
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
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return insights_collection.find_one({'user_id': user_id})
