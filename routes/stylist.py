from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from models import User
from auth import optional_token
from services import stylist_service

stylist_bp = Blueprint('stylist', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@stylist_bp.route('/predict', methods=['POST'])
@optional_token
def predict():
    """Generate outfit recommendations"""
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file type"}), 400
    
    # Get form data
    occasion = request.form.get('occasion', 'casual')
    occasion_subtype = request.form.get('occasion_subtype', '')
    climate = request.form.get('climate', 'moderate')
    clothing_style = request.form.get('clothing_style', 'unisex')
    age_group = request.form.get('age_group', 'young')
    body_type = request.form.get('body_type', 'regular')
    budget = request.form.get('budget', 'medium')
    detect_face = request.form.get('detect_face', 'false').lower() == 'true'
    skin_tone = request.form.get('skin_tone', '')
    undertone = request.form.get('undertone', '')
    
    # Override with user profile if authenticated
    if hasattr(request, 'current_user') and request.current_user:
        user = User.find_by_id(request.current_user['user_id'])
        if user and user.get('profile'):
            profile = user['profile']
            body_type = profile.get('body_type', body_type)
            budget = profile.get('budget_preference', budget)
            age_group = profile.get('age_group', age_group)
            skin_tone = profile.get('skin_tone', skin_tone)
            undertone = profile.get('undertone', undertone)
    
    # Validation
    if occasion not in ['casual', 'formal', 'party', 'ethnic']: occasion = 'casual'
    if climate not in ['hot', 'moderate', 'cold']: climate = 'moderate'
    if clothing_style not in ['mens', 'womens', 'unisex']: clothing_style = 'unisex'
    if age_group not in ['young', 'adult', 'senior']: age_group = 'young'
    if body_type not in ['slim', 'regular', 'relaxed']: body_type = 'regular'
    if budget not in ['low', 'medium', 'high']: budget = 'medium'
    
    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Process
    matching_outfits = stylist_service.rank_and_filter_outfits(
        occasion, climate, clothing_style, age_group, body_type, budget, 
        occasion_subtype if occasion_subtype else None
    )
    
    result_outfits = []
    for outfit in matching_outfits:
        outfit_copy = outfit.copy()
        outfit_copy["shopping_links"] = stylist_service.generate_shopping_links(
            outfit["items"], 
            outfit.get("gender", "unisex"), 
            outfit.get("budget", "medium"), 
            outfit.get("occasion", "casual"),
            occasion_subtype if occasion_subtype in outfit.get("occasion_subtype", []) else None
        )
        outfit_copy["average_rating"] = stylist_service.get_outfit_rating(outfit["id"])
        
        if hasattr(request, 'current_user') and request.current_user:
            outfit_copy["in_wardrobe"] = False # Placeholder for check
        
        result_outfits.append(outfit_copy)
    
    style_tips = stylist_service.generate_care_routines(
        clothing_style, climate, occasion, skin_tone or None, undertone or None, detect_face
    )
    
    response_data = {
        "status": "success",
        "prediction": {
            "confidence": 0.95,
            "clothing_type": "Uploaded Garment",
            "outfits": result_outfits,
            "style_tips": style_tips
        }
    }
    
    if hasattr(request, 'current_user') and request.current_user:
        response_data["user_context"] = {"authenticated": True, "has_wardrobe": True}
    
    return jsonify(response_data)
