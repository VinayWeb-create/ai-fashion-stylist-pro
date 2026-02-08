"""
AI Fashion Stylist Pro - Flask Backend API
Stable, production-ready backend with Gemini + Mock fallback
"""

import os
import json
import re
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv


# =====================================
# App Setup
# =====================================

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp"}



# =====================================
# Helpers
# =====================================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_json_from_text(text: str) -> dict:
    """
    Safely extract JSON object from LLM output
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON found in AI response")
    return json.loads(match.group())


def mock_recommendation(occasion, climate, clothing_style):
    """
    Fallback response when Gemini is unavailable
    """
    return {
        "clothing_type": "Smart Casual",
        "confidence": 0.94,
        "face_detection": {
            "detected": False,
            "skin_tone": "Not analyzed",
            "description": "Mock AI response (Gemini disabled)"
        },
        "outfits": [
            {
                "name": "Everyday Casual",
                "description": "Clean and comfortable everyday style",
                "items": ["T-shirt", "Jeans", "Overshirt"],
                "colors": ["Navy", "White"],
                "accessories": ["Watch"],
                "footwear": "Sneakers",
                "reasoning": "Works well for casual outings and daily wear"
            },
            {
                "name": "Minimal Smart",
                "description": "Simple and modern outfit",
                "items": ["Plain Shirt", "Chinos"],
                "colors": ["Beige", "White"],
                "accessories": ["Belt"],
                "footwear": "Loafers",
                "reasoning": "Professional yet relaxed appearance"
            }
        ]
    }

# =====================================
# Gemini Integration
# =====================================


# =====================================
# Routes
# =====================================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "success",
        "message": "AI Fashion Stylist Pro API running",
        "gemini_enabled": USE_GEMINI
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/predict", methods=["POST"])
def predict():
    try:
        if "image" not in request.files:
            return jsonify({"error": "Image file missing"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Invalid image type"}), 400

        occasion = request.form.get("occasion", "casual")
        climate = request.form.get("climate", "moderate")
        clothing_style = request.form.get("clothing_style", "unisex")

        image_bytes = file.read()

        # Use Gemini or fallback
        if USE_GEMINI:
            prediction = get_gemini_recommendations(
                image_bytes,
                file.content_type,
                occasion,
                climate,
                clothing_style
            )
        else:
            prediction = mock_recommendation(
                occasion, climate, clothing_style
            )

        return jsonify({
            "status": "success",
            "prediction": prediction
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

# =====================================
# Main
# =====================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

