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

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
GENAI_API_KEY = os.getenv('GEMINI_API_KEY')
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables")

# =====================================
# Gemini Integration
# =====================================

def get_gemini_recommendations(image_part, occasion, climate, clothing_style):
    """
    Get 3 outfit recommendations from Gemini Pro Vision (or 1.5 Flash)
    """
    if not GENAI_API_KEY:
        # Fallback if no key (or better, raise error)
        raise ValueError("Server configuration error: Gemini API Key missing")

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an expert personalized fashion stylist. 
    Analyze the uploaded image of the person (determine skin tone, body type context from image if visible, otherwise focus on general style).
    
    User Preferences:
    - Occasion: {occasion}
    - Climate: {climate}
    - Preferred Style: {clothing_style}

    Task:
    Generate 3 DISTINCT and complete outfit recommendations that would suit this person for the given occasion and climate.
    
    Output strictly in this JSON format:
    {{
        "clothing_type": "Primary clothing item detected or suggested",
        "confidence": 0.95,
        "face_detection": {{
            "detected": true/false,
            "skin_tone": "Estimated Skin Tone",
            "description": "Brief analysis of the person's features if visible"
        }},
        "outfits": [
            {{
                "name": "Outfit Name (e.g., 'Chic Minimalist')",
                "description": "Brief description of the look",
                "items": ["Item 1", "Item 2", "Item 3"],
                "colors": ["Color Hex 1", "Color Hex 2"],
                "accessories": ["Accessory 1", "Accessory 2"],
                "footwear": "Shoe recommendation",
                "reasoning": "Why this fits the user and occasion"
            }},
            {{
                "name": "Outfit Name 2",
                 "description": "Brief description",
                "items": ["Item 1", "Item 2"],
                "colors": ["Color Hex 1", "Color Hex 2"],
                 "accessories": ["Accessory"],
                "footwear": "Shoe",
                "reasoning": "Reasoning"
            }},
            {{
                "name": "Outfit Name 3",
                 "description": "Brief description",
                 "items": ["Item 1", "Item 2"],
                "colors": ["Color Hex 1", "Color Hex 2"],
                 "accessories": ["Accessory"],
                "footwear": "Shoe",
                 "reasoning": "Reasoning"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content([prompt, image_part])
        # Clean up code blocks if present
        text = response.text.replace('```json', '').replace('```', '')
        return json.loads(text)
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return a fallback or re-raise
        raise e

# =====================================
# API Endpoints
# =====================================

@app.route('/', methods=['GET'])
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'success',
        'message': 'AI Fashion Stylist Pro API is running (Gemini Powered)',
        'version': '2.0.0'
    })

@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint using Gemini
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
        
        # Prepare image for Gemini
        # Read file into bytes
        img_bytes = file.read()
        
        # Create image part
        image_part = {
            "mime_type": file.content_type or "image/jpeg",
            "data": img_bytes
        }

        # Call Gemini
        ai_response = get_gemini_recommendations(image_part, occasion, climate, clothing_style)
        
        return jsonify({
            'status': 'success',
            'prediction': ai_response
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in /predict endpoint: {e}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

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
