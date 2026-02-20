from flask import Blueprint, request, jsonify
from urllib.parse import quote_plus
from models import User, WardrobeItem
from auth import token_required
from wardrobe_intelligence import analyze_wardrobe_gaps, calculate_wardrobe_balance

wardrobe_bp = Blueprint('wardrobe', __name__)

@wardrobe_bp.route('/items', methods=['GET'])
@token_required
def get_wardrobe_items():
    """Get all wardrobe items for the current user"""
    category = request.args.get('category')
    owned = request.args.get('owned')
    occasion = request.args.get('occasion')
    
    filters = {}
    if category:
        filters['category'] = category
    if owned is not None:
        filters['owned'] = owned.lower() == 'true'
    if occasion:
        filters['occasion'] = occasion
    
    items = WardrobeItem.get_user_wardrobe(request.current_user['user_id'], filters)
    
    for item in items:
        item['_id'] = str(item['_id'])
        item['user_id'] = str(item['user_id'])
    
    return jsonify({
        'status': 'success',
        'items': items,
        'count': len(items)
    })

@wardrobe_bp.route('/add', methods=['POST'])
@token_required
def add_wardrobe_item():
    """Add an item to the wardrobe"""
    data = request.get_json()
    item = WardrobeItem.create(request.current_user['user_id'], data)
    
    item['_id'] = str(item['_id'])
    item['user_id'] = str(item['user_id'])
    
    return jsonify({
        'status': 'success',
        'message': 'Item added to wardrobe',
        'item': item
    }), 201

@wardrobe_bp.route('/mark-owned/<item_id>', methods=['PUT'])
@token_required
def mark_item_owned(item_id):
    """Mark an item as owned or not owned"""
    data = request.get_json()
    owned = data.get('owned', True)
    
    WardrobeItem.mark_owned(item_id, owned)
    
    return jsonify({
        'status': 'success',
        'message': f'Item marked as {"owned" if owned else "not owned"}'
    })

@wardrobe_bp.route('/remove/<item_id>', methods=['DELETE'])
@token_required
def remove_wardrobe_item(item_id):
    """Remove an item from the wardrobe"""
    WardrobeItem.remove_item(item_id, request.current_user['user_id'])
    
    return jsonify({
        'status': 'success',
        'message': 'Item removed from wardrobe'
    })

@wardrobe_bp.route('/stats', methods=['GET'])
@token_required
def get_wardrobe_stats():
    """Get wardrobe statistics"""
    stats = WardrobeItem.get_wardrobe_stats(request.current_user['user_id'])
    
    return jsonify({
        'status': 'success',
        'stats': stats
    })

# Insights Routes (Moved here for logic grouping)
@wardrobe_bp.route('/insights/gaps', methods=['GET'])
@token_required
def get_wardrobe_gaps():
    """Get wardrobe gap analysis"""
    user = User.find_by_id(request.current_user['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    gaps = analyze_wardrobe_gaps(request.current_user['user_id'], user['profile'])
    
    for gap in gaps:
        query = gap.get('shopping_query', gap.get('item_name', ''))
        encoded_query = quote_plus(query)
        gap['shopping_links'] = {
            'amazon': f"https://www.amazon.in/s?k={encoded_query}",
            'flipkart': f"https://www.flipkart.com/search?q={encoded_query}",
            'meesho': f"https://www.meesho.com/search?q={encoded_query}",
            'myntra': f"https://www.myntra.com/{encoded_query}"
        }
    
    return jsonify({
        'status': 'success',
        'gaps': gaps,
        'count': len(gaps)
    })

@wardrobe_bp.route('/insights/balance', methods=['GET'])
@token_required
def get_wardrobe_balance():
    """Get wardrobe balance metrics"""
    balance = calculate_wardrobe_balance(request.current_user['user_id'])
    
    return jsonify({
        'status': 'success',
        'balance': balance
    })
