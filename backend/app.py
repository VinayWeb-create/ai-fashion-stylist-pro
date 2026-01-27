"""
AI Fashion Stylist Pro - Flask Backend API
Provides endpoints for clothing classification and style recommendations
"""

import os
import json
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import io
import sys

# Add model directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# =====================================
# Style Classification Database
# =====================================

STYLE_DATABASE = {
    'casual': {
        'accessories': ['Sunglasses', 'Canvas Bag', 'Sneakers', 'Baseball Cap', 'Cross-body Bag'],
        'footwear': ['Sneakers', 'Casual Flats', 'Loafers', 'Slides', 'Canvas Shoes'],
        'hair_styles': ['Ponytail', 'Messy Bun', 'Half-up Hairstyle', 'Beach Waves', 'Natural'],
        'makeup': ['Natural', 'Minimal', 'Light Coverage', 'No-Makeup Makeup'],
        'patterns': ['Stripes', 'Polka Dots', 'Floral', 'Geometric'],
        'fabrics': ['Cotton', 'Denim', 'Canvas', 'Linen', 'Jersey'],
        'tips': [
            'Mix comfort with style',
            'Accessorize with minimal jewelry',
            'Choose breathable fabrics',
            'Layer pieces for a relaxed look'
        ]
    },
    'formal': {
        'accessories': ['Dress Watch', 'Pearl Necklace', 'Leather Gloves', 'Elegant Clutch', 'Dress Shoes'],
        'footwear': ['Heels', 'Formal Dress Shoes', 'Pumps', 'Stilettos', 'Dressy Flats'],
        'hair_styles': ['Updo', 'Slicked Back', 'Elegant Waves', 'Half-up Style', 'Neat Bun'],
        'makeup': ['Bold Lipstick', 'Smokey Eyes', 'Defined Eyebrows', 'Full Coverage'],
        'patterns': ['Solid', 'Subtle Texture', 'Fine Stripes', 'Jacquard'],
        'fabrics': ['Silk', 'Satin', 'Velvet', 'Wool', 'Taffeta'],
        'tips': [
            'Invest in classic pieces',
            'Keep accessories minimal and elegant',
            'Choose quality fabrics',
            'Maintain a polished appearance'
        ]
    },
    'party': {
        'accessories': ['Statement Necklace', 'Sequined Clutch', 'Chandelier Earrings', 'Metallic Bag', 'Bold Bracelet'],
        'footwear': ['High Heels', 'Metallic Heels', 'Strappy Sandals', 'Dressy Boots', 'Platform Shoes'],
        'hair_styles': ['Styled Waves', 'Glamorous Curls', 'Sleek Ponytail', 'Teased Volume', 'Half-up Glam'],
        'makeup': ['Glitter', 'Metallic Eyeshadow', 'Bold Eyeliner', 'Statement Lips', 'Highlighter'],
        'patterns': ['Sequins', 'Shimmer', 'Bold Geometric', 'Metallic', 'Lurex'],
        'fabrics': ['Sequined Fabric', 'Satin', 'Metallic', 'Tulle', 'Lamé'],
        'tips': [
            'Go bold with colors and accessories',
            'Choose statement pieces',
            'Don\'t be afraid of sparkle',
            'Make sure your makeup complements your outfit'
        ]
    },
    'ethnic': {
        'accessories': ['Traditional Jewelry', 'Embroidered Clutch', 'Bangle Set', 'Ethnic Scarf', 'Decorative Belt'],
        'footwear': ['Ethnic Sandals', 'Juttis', 'Embroidered Flats', 'Traditional Heels', 'Embellished Shoes'],
        'hair_styles': ['Braids', 'Half-up with Bindi', 'Curled Waves', 'Side Partition', 'Fishtail Braid'],
        'makeup': ['Bold Eyes', 'Metallic Eyeshadow', 'Defined Eyebrows', 'Natural Lip', 'Bindi'],
        'patterns': ['Embroidery', 'Paisley', 'Geometric Ethnic', 'Block Print', 'Weaving'],
        'fabrics': ['Silk', 'Cotton Blend', 'Handwoven', 'Linen', 'Brocade'],
        'tips': [
            'Embrace traditional elements',
            'Layer jewelry appropriately',
            'Choose complementary colors',
            'Balance ornate pieces with simpler ones'
        ]
    }
}

COLOR_COMBINATIONS = {
    'Black': {
        'compatible': ['White', 'Gold', 'Silver', 'Cream', 'Red'],
        'avoid': []
    },
    'White': {
        'compatible': ['Black', 'Navy', 'Gold', 'Any Color'],
        'avoid': []
    },
    'Navy': {
        'compatible': ['White', 'Light Blue', 'Gold', 'Red', 'Beige'],
        'avoid': ['Black']
    },
    'Red': {
        'compatible': ['Black', 'White', 'Gold', 'Cream', 'Navy'],
        'avoid': []
    },
    'Green': {
        'compatible': ['Cream', 'Gold', 'Brown', 'Beige', 'White'],
        'avoid': []
    },
    'Blue': {
        'compatible': ['White', 'Gold', 'Cream', 'Coral', 'Pink'],
        'avoid': []
    }
}

CLIMATE_RECOMMENDATIONS = {
    'hot': {
        'fabrics': ['Linen', 'Cotton', 'Chambray', 'Voile', 'Jersey'],
        'styles': ['Loose Fit', 'Sleeveless', 'Breathable Fabrics'],
        'colors': ['Light Colors', 'Pastels', 'White', 'Cream']
    },
    'moderate': {
        'fabrics': ['Cotton Blend', 'Wool', 'Linen', 'Silk', 'Polyester'],
        'styles': ['Layerable Pieces', 'Mid-weight Fabrics'],
        'colors': ['Any Colors', 'Jewel Tones', 'Earth Tones']
    },
    'cold': {
        'fabrics': ['Wool', 'Fleece', 'Down', 'Synthetic Blend', 'Cashmere'],
        'styles': ['Layering', 'Long Sleeves', 'Insulated', 'Thermal'],
        'colors': ['Dark Colors', 'Warm Tones', 'Jewel Tones']
    }
}

SKIN_TONE_COLORS = {
    'Fair': ['Silver', 'Icy Tones', 'Pastels', 'Light Colors'],
    'Light': ['Gold', 'Warm Pastels', 'Cream', 'Coral'],
    'Medium': ['Gold', 'Warm Colors', 'Jewel Tones', 'Olive'],
    'Olive': ['Gold', 'Warm Earth Tones', 'Green', 'Bronze'],
    'Dark': ['Warm Gold', 'Deep Colors', 'Jewel Tones', 'Rich Earth Tones'],
    'Very Dark': ['Gold', 'Bright Colors', 'Deep Jewel Tones', 'Dark Jewel Tones']
}

# =====================================
# Utility Functions
# =====================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(file):
    """Process uploaded image and prepare for model"""
    try:
        img = Image.open(io.BytesIO(file.read()))
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize image to model input size
        img = img.resize((224, 224))
        
        # Convert to numpy array and normalize
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        print(f"Error processing image: {e}")
        raise ValueError(f"Invalid image file: {str(e)}")

def get_clothing_classification():
    """
    Simulate CNN model prediction for clothing type
    In production, this would use the actual trained model
    """
    clothing_types = ['T-shirt', 'Dress', 'Formal Shirt', 'Casual Shirt', 'Jacket', 
                      'Blouse', 'Saree', 'Skirt', 'Pants', 'Suit', 'Hoodie', 'Sweater']
    confidence = np.random.uniform(0.75, 0.98)
    clothing_type = np.random.choice(clothing_types)
    return clothing_type, confidence

def get_style_recommendations(occasion, climate):
    """Get style recommendations based on occasion and climate"""
    occasion_lower = occasion.lower() if occasion else 'casual'
    climate_lower = climate.lower() if climate else 'moderate'
    
    # Get recommendations from database
    style_rec = STYLE_DATABASE.get(occasion_lower, STYLE_DATABASE['casual'])
    climate_rec = CLIMATE_RECOMMENDATIONS.get(climate_lower, CLIMATE_RECOMMENDATIONS['moderate'])
    
    return style_rec, climate_rec

def analyze_skin_tone(image_array):
    """
    Simulate face detection and skin tone analysis
    In production, use OpenCV or face_recognition library
    """
    skin_tones = ['Fair', 'Light', 'Medium', 'Olive', 'Dark', 'Very Dark']
    skin_tone = np.random.choice(skin_tones)
    recommended_colors = SKIN_TONE_COLORS.get(skin_tone, ['Gold', 'Warm Tones'])
    
    return {
        'detected': True,
        'skin_tone': skin_tone,
        'color_recommendations': recommended_colors[:2]
    }

# =====================================
# API Endpoints
# =====================================

@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'AI Fashion Stylist Pro API is running',
        'version': '1.0.0'
    })

@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint for outfit analysis
    
    Expected parameters:
    - image: Image file (required)
    - occasion: casual, formal, party, ethnic (optional)
    - climate: hot, moderate, cold (optional)
    - clothing_style: unisex, womens, mens (optional)
    - detect_face: true/false (optional)
    """
    
    try:
        # Validate file upload
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, bmp'}), 400
        
        # Get form parameters
        occasion = request.form.get('occasion', 'casual')
        climate = request.form.get('climate', 'moderate')
        clothing_style = request.form.get('clothing_style', 'unisex')
        detect_face = request.form.get('detect_face', 'false').lower() == 'true'
        
        # Process image
        file.seek(0)  # Reset file pointer
        image_array = process_image(file)
        
        # Get clothing classification (would use actual model in production)
        clothing_type, confidence = get_clothing_classification()
        
        # Get style recommendations
        style_rec, climate_rec = get_style_recommendations(occasion, climate)
        
        # Determine style category
        style_category = occasion.title() if occasion else 'Casual'
        
        # Get color recommendations
        primary_colors = ['Navy Blue', 'Black', 'Cream', 'Gold', 'White']
        colors = np.random.choice(primary_colors, size=4, replace=False).tolist()
        
        # Build response
        response_data = {
            'clothing_type': clothing_type,
            'confidence': float(confidence),
            'style_category': style_category,
            'clothing_style': clothing_style,
            'colors': colors,
            'accessories': style_rec.get('accessories', [])[:5],
            'footwear': style_rec.get('footwear', [])[:4],
            'hair_styles': style_rec.get('hair_styles', [])[:4],
            'makeup': style_rec.get('makeup', [])[:3],
            'patterns': style_rec.get('patterns', [])[:3],
            'fabrics': climate_rec.get('fabrics', [])[:3],
            'style_tips': style_rec.get('tips', [])[:3],
            'climate_notes': climate_rec.get('styles', [])[:2]
        }
        
        # Add face detection results if requested
        if detect_face:
            face_results = analyze_skin_tone(image_array)
            response_data['face_detection'] = face_results
        else:
            response_data['face_detection'] = {'detected': False}
        
        return jsonify({
            'status': 'success',
            'prediction': response_data
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in /predict endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    }), 200

# =====================================
# Error Handlers
# =====================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# =====================================
# Main
# =====================================

if __name__ == '__main__':
    # Note: In production, use a production WSGI server like Gunicorn
    # Example: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    app.run(debug=True, host='0.0.0.0', port=5000)