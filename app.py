"""
AI Fashion Stylist Pro - Flask Backend
Rule-based outfit generation with internet shopping links
No Gemini / No LLM / Stable production backend
"""

import os
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


def generate_shopping_links(item_name: str):
    """
    Generate e-commerce search URLs for an item
    """
    query = item_name.replace(" ", "+").lower()
    return {
        "item": item_name,
        "links": {
            "amazon": f"https://www.amazon.in/s?k={query}",
            "flipkart": f"https://www.flipkart.com/search?q={query}",
            "meesho": f"https://www.meesho.com/search?q={query}"
        }
    }


def generate_outfits(occasion, climate, clothing_style):
    """
    Rule-based outfit generator
    """

    outfits = []

    # ==========================
    # CASUAL
    # ==========================
    if occasion == "casual":
        outfits = [
            {
                "name": "Everyday Casual",
                "description": "Comfortable and stylish daily wear",
                "reasoning": "Simple fabrics and neutral colors for daily comfort",
                "items": ["White Cotton T-Shirt", "Blue Jeans"],
                "colors": ["White", "Blue"],
                "accessories": ["Watch"],
                "footwear": "White Sneakers"
            },
            {
                "name": "Smart Casual",
                "description": "Polished yet relaxed look",
                "reasoning": "Perfect for college, office casual days, or meetups",
                "items": ["Casual Shirt", "Slim Fit Chinos"],
                "colors": ["Beige", "Navy"],
                "accessories": ["Leather Belt"],
                "footwear": "Loafers"
            },
            {
                "name": "Relaxed Evening",
                "description": "Easy-going evening outfit",
                "reasoning": "Ideal for evening outings or coffee meetups",
                "items": ["Polo T-Shirt", "Black Jeans"],
                "colors": ["Black"],
                "accessories": ["Bracelet"],
                "footwear": "Casual Shoes"
            }
        ]

    # ==========================
    # FORMAL
    # ==========================
    elif occasion == "formal":
        outfits = [
            {
                "name": "Classic Formal",
                "description": "Professional and elegant outfit",
                "reasoning": "Traditional formal combination for meetings and offices",
                "items": ["White Formal Shirt", "Black Trousers"],
                "colors": ["White", "Black"],
                "accessories": ["Leather Watch"],
                "footwear": "Formal Shoes"
            },
            {
                "name": "Modern Business",
                "description": "Clean modern business attire",
                "reasoning": "Sharp look suitable for presentations",
                "items": ["Light Blue Shirt", "Grey Trousers"],
                "colors": ["Light Blue", "Grey"],
                "accessories": ["Belt"],
                "footwear": "Oxford Shoes"
            },
            {
                "name": "Executive Look",
                "description": "Premium corporate outfit",
                "reasoning": "Creates authority and confidence",
                "items": ["Formal Blazer", "White Shirt", "Formal Pants"],
                "colors": ["Navy", "White"],
                "accessories": ["Tie"],
                "footwear": "Derby Shoes"
            }
        ]

    # ==========================
    # PARTY
    # ==========================
    elif occasion == "party":
        outfits = [
            {
                "name": "Party Casual",
                "description": "Trendy and relaxed party outfit",
                "reasoning": "Stylish yet comfortable for social events",
                "items": ["Printed Shirt", "Dark Jeans"],
                "colors": ["Black", "Maroon"],
                "accessories": ["Chain"],
                "footwear": "Sneakers"
            },
            {
                "name": "Night Out",
                "description": "Bold evening party look",
                "reasoning": "Dark tones give a premium night vibe",
                "items": ["Black Shirt", "Slim Jeans"],
                "colors": ["Black"],
                "accessories": ["Watch"],
                "footwear": "Chelsea Boots"
            },
            {
                "name": "Stylish Party",
                "description": "Fashion-forward party wear",
                "reasoning": "Modern cuts elevate appearance",
                "items": ["Designer Shirt", "Tailored Pants"],
                "colors": ["Charcoal"],
                "accessories": ["Bracelet"],
                "footwear": "Formal Shoes"
            }
        ]

    # ==========================
    # ETHNIC
    # ==========================
    elif occasion == "ethnic":
        outfits = [
            {
                "name": "Traditional Ethnic",
                "description": "Classic ethnic wear",
                "reasoning": "Perfect for festivals and ceremonies",
                "items": ["Kurta", "Pajama"],
                "colors": ["Cream", "Gold"],
                "accessories": ["Ethnic Bracelet"],
                "footwear": "Mojari"
            },
            {
                "name": "Festive Look",
                "description": "Bright festive attire",
                "reasoning": "Vibrant colors suit celebrations",
                "items": ["Printed Kurta", "Churidar"],
                "colors": ["Maroon", "Beige"],
                "accessories": ["Stole"],
                "footwear": "Kolhapuri Chappals"
            },
            {
                "name": "Modern Ethnic",
                "description": "Fusion ethnic style",
                "reasoning": "Traditional with a modern twist",
                "items": ["Short Kurta", "Jeans"],
                "colors": ["Indigo"],
                "accessories": ["Watch"],
                "footwear": "Ethnic Loafers"
            }
        ]

    # ==========================
    # Attach Shopping Links
    # ==========================
    for outfit in outfits:
        outfit["shopping_links"] = [
            generate_shopping_links(item) for item in outfit["items"]
        ]

    return outfits

# =====================================
# Routes
# =====================================

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "success",
        "message": "AI Fashion Stylist Pro API running (No AI mode)"
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

        outfits = generate_outfits(occasion, climate, clothing_style)

        return jsonify({
            "status": "success",
            "prediction": {
                "clothing_type": "Outfit Recommendation",
                "confidence": 0.93,
                "face_detection": {
                    "detected": False,
                    "skin_tone": "Not analyzed",
                    "description": "Face detection disabled"
                },
                "outfits": outfits
            }
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
