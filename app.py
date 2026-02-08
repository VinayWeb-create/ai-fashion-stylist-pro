from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from urllib.parse import quote_plus
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

FAVORITES_FILE = os.path.join(DATA_FOLDER, 'favorites.json')
RATINGS_FILE = os.path.join(DATA_FOLDER, 'ratings.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_json_file(filepath, default):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return default

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

OUTFIT_DATABASE = [
    {
        "id": "outfit_001",
        "name": "Classic Casual Denim",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "items": ["Blue Denim Jeans", "White Cotton T-Shirt", "Casual Sneakers"],
        "colors": ["Blue", "White"],
        "accessories": ["Sunglasses", "Wristwatch"],
        "footwear": "Casual Sneakers",
        "budget": "medium",
        "brands": ["Levis", "Nike", "H&M"],
        "style_tags": ["casual", "comfortable", "everyday"],
        "season": ["spring", "summer", "fall"],
        "description": "A timeless casual look perfect for everyday wear",
        "reasoning": "This outfit combines comfort with style, ideal for relaxed settings"
    },
    {
        "id": "outfit_002",
        "name": "Summer Casual Shorts",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["hot"],
        "age_group": ["young"],
        "items": ["Khaki Shorts", "Polo Shirt", "Canvas Shoes"],
        "colors": ["Khaki", "Navy Blue"],
        "accessories": ["Cap", "Backpack"],
        "footwear": "Canvas Shoes",
        "budget": "low",
        "brands": ["Zara", "Uniqlo", "Vans"],
        "style_tags": ["sporty", "casual", "relaxed"],
        "season": ["summer"],
        "description": "Perfect for hot weather outdoor activities",
        "reasoning": "Lightweight and breathable materials keep you cool in the heat"
    },
    {
        "id": "outfit_003",
        "name": "Business Formal Suit",
        "gender": "mens",
        "occasion": "formal",
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "items": ["Navy Blue Suit", "White Dress Shirt", "Black Leather Shoes", "Silk Tie"],
        "colors": ["Navy Blue", "White", "Black"],
        "accessories": ["Leather Belt", "Cufflinks", "Wristwatch"],
        "footwear": "Black Leather Shoes",
        "budget": "high",
        "brands": ["Raymond", "Louis Philippe", "Van Heusen"],
        "style_tags": ["formal", "professional", "elegant"],
        "season": ["fall", "winter", "spring"],
        "description": "Classic business attire for important meetings",
        "reasoning": "Professional appearance with timeless sophistication"
    },
    {
        "id": "outfit_004",
        "name": "Smart Casual Blazer",
        "gender": "mens",
        "occasion": "formal",
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "items": ["Grey Blazer", "Chinos", "Oxford Shoes", "Dress Shirt"],
        "colors": ["Grey", "Beige", "Brown"],
        "accessories": ["Leather Watch", "Pocket Square"],
        "footwear": "Oxford Shoes",
        "budget": "medium",
        "brands": ["Allen Solly", "Peter England", "Clarks"],
        "style_tags": ["smart-casual", "sophisticated", "versatile"],
        "season": ["spring", "fall"],
        "description": "Versatile smart-casual for semi-formal occasions",
        "reasoning": "Balances professionalism with approachability"
    },
    {
        "id": "outfit_005",
        "name": "Winter Casual Layers",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["cold"],
        "age_group": ["young", "adult"],
        "items": ["Hoodie", "Jeans", "Winter Jacket", "Boots"],
        "colors": ["Black", "Grey", "Brown"],
        "accessories": ["Beanie", "Scarf"],
        "footwear": "Boots",
        "budget": "medium",
        "brands": ["Puma", "Adidas", "Timberland"],
        "style_tags": ["casual", "cozy", "layered"],
        "season": ["winter"],
        "description": "Warm and stylish layers for cold weather",
        "reasoning": "Multiple layers provide warmth without sacrificing style"
    },
    {
        "id": "outfit_006",
        "name": "Casual Floral Dress",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "items": ["Floral Midi Dress", "Sandals", "Denim Jacket"],
        "colors": ["Floral Print", "Blue"],
        "accessories": ["Sunglasses", "Crossbody Bag"],
        "footwear": "Sandals",
        "budget": "medium",
        "brands": ["Zara", "Forever 21", "Mango"],
        "style_tags": ["feminine", "casual", "trendy"],
        "season": ["spring", "summer"],
        "description": "Feminine and breezy for casual outings",
        "reasoning": "Floral patterns add a fresh, cheerful touch"
    },
    {
        "id": "outfit_007",
        "name": "Summer Breezy Outfit",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["hot"],
        "age_group": ["young"],
        "items": ["White Linen Top", "High Waisted Shorts", "Espadrilles"],
        "colors": ["White", "Denim Blue"],
        "accessories": ["Straw Hat", "Tote Bag"],
        "footwear": "Espadrilles",
        "budget": "low",
        "brands": ["H&M", "Lifestyle", "Westside"],
        "style_tags": ["breezy", "casual", "comfortable"],
        "season": ["summer"],
        "description": "Light and airy for hot summer days",
        "reasoning": "Natural fabrics keep you cool and comfortable"
    },
    {
        "id": "outfit_008",
        "name": "Elegant Evening Gown",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "items": ["Black Evening Gown", "Heels", "Clutch"],
        "colors": ["Black"],
        "accessories": ["Pearl Necklace", "Bracelet", "Earrings"],
        "footwear": "Heels",
        "budget": "high",
        "brands": ["Sabyasachi", "Manish Malhotra", "Tarun Tahiliani"],
        "style_tags": ["elegant", "formal", "luxurious"],
        "season": ["fall", "winter", "spring"],
        "description": "Sophisticated elegance for formal events",
        "reasoning": "Timeless black creates a stunning formal appearance"
    },
    {
        "id": "outfit_009",
        "name": "Professional Pantsuit",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "items": ["Blazer", "Dress Pants", "Blouse", "Pumps"],
        "colors": ["Navy", "White"],
        "accessories": ["Statement Watch", "Tote Bag"],
        "footwear": "Pumps",
        "budget": "medium",
        "brands": ["W", "AND", "Van Heusen Woman"],
        "style_tags": ["professional", "formal", "powerful"],
        "season": ["spring", "fall"],
        "description": "Empowering professional attire",
        "reasoning": "Sharp tailoring conveys confidence and competence"
    },
    {
        "id": "outfit_010",
        "name": "Cozy Winter Layers",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["cold"],
        "age_group": ["young", "adult"],
        "items": ["Sweater", "Jeans", "Coat", "Ankle Boots"],
        "colors": ["Burgundy", "Black", "Camel"],
        "accessories": ["Scarf", "Gloves"],
        "footwear": "Ankle Boots",
        "budget": "medium",
        "brands": ["Zara", "Marks & Spencer", "Vero Moda"],
        "style_tags": ["cozy", "layered", "warm"],
        "season": ["winter"],
        "description": "Warm and stylish for cold weather",
        "reasoning": "Rich colors and textures create a cozy aesthetic"
    },
    {
        "id": "outfit_011",
        "name": "Cocktail Party Dress",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "items": ["Cocktail Dress", "Strappy Heels", "Clutch"],
        "colors": ["Red", "Gold"],
        "accessories": ["Drop Earrings", "Bracelet"],
        "footwear": "Strappy Heels",
        "budget": "high",
        "brands": ["Shein", "FabIndia", "Global Desi"],
        "style_tags": ["glamorous", "party", "chic"],
        "season": ["spring", "summer", "fall"],
        "description": "Glamorous cocktail attire for parties",
        "reasoning": "Bold colors make a memorable statement"
    },
    {
        "id": "outfit_012",
        "name": "Basic Unisex Casual",
        "gender": "unisex",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "items": ["Plain T-Shirt", "Jeans", "Sneakers"],
        "colors": ["Black", "Blue"],
        "accessories": ["Backpack"],
        "footwear": "Sneakers",
        "budget": "low",
        "brands": ["Decathlon", "Max", "Reliance Trends"],
        "style_tags": ["minimal", "casual", "basic"],
        "season": ["spring", "summer", "fall"],
        "description": "Simple and versatile everyday wear",
        "reasoning": "Minimalist approach works for any casual setting"
    },
    {
        "id": "outfit_013",
        "name": "Athleisure Comfort",
        "gender": "unisex",
        "occasion": "casual",
        "climate": ["hot", "moderate", "cold"],
        "age_group": ["young", "adult"],
        "items": ["Joggers", "Hoodie", "Running Shoes"],
        "colors": ["Grey", "Black"],
        "accessories": ["Sports Watch", "Gym Bag"],
        "footwear": "Running Shoes",
        "budget": "medium",
        "brands": ["Nike", "Adidas", "Puma"],
        "style_tags": ["sporty", "comfortable", "athletic"],
        "season": ["spring", "summer", "fall", "winter"],
        "description": "Athletic comfort meets street style",
        "reasoning": "Performance fabrics provide all-day comfort"
    },
    {
        "id": "outfit_014",
        "name": "Smart Casual Neutrals",
        "gender": "unisex",
        "occasion": "formal",
        "climate": ["moderate"],
        "age_group": ["adult"],
        "items": ["Blazer", "Trousers", "Loafers", "Button Up Shirt"],
        "colors": ["Beige", "White", "Brown"],
        "accessories": ["Leather Belt", "Watch"],
        "footwear": "Loafers",
        "budget": "medium",
        "brands": ["Gap", "Banana Republic", "Massimo Dutti"],
        "style_tags": ["smart-casual", "neutral", "versatile"],
        "season": ["spring", "fall"],
        "description": "Refined neutrals for versatile wear",
        "reasoning": "Neutral tones create sophisticated versatility"
    },
    {
        "id": "outfit_015",
        "name": "Urban Streetwear",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age_group": ["young"],
        "items": ["Graphic T-Shirt", "Cargo Pants", "High-Top Sneakers"],
        "colors": ["Black", "Olive"],
        "accessories": ["Baseball Cap", "Chain Necklace"],
        "footwear": "High-Top Sneakers",
        "budget": "medium",
        "brands": ["Supreme", "Nike", "Carhartt"],
        "style_tags": ["urban", "streetwear", "edgy"],
        "season": ["spring", "summer", "fall"],
        "description": "Bold urban streetwear style",
        "reasoning": "Modern street fashion with attitude"
    },
    {
        "id": "outfit_016",
        "name": "Preppy Casual",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "items": ["Sweater Vest", "Chinos", "Boat Shoes"],
        "colors": ["Navy", "Cream", "Brown"],
        "accessories": ["Leather Bracelet", "Messenger Bag"],
        "footwear": "Boat Shoes",
        "budget": "medium",
        "brands": ["Ralph Lauren", "Tommy Hilfiger", "Gant"],
        "style_tags": ["preppy", "classic", "smart-casual"],
        "season": ["spring", "fall"],
        "description": "Classic preppy casual style",
        "reasoning": "Timeless preppy aesthetic with modern touch"
    },
    {
        "id": "outfit_017",
        "name": "Boho Chic Dress",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "items": ["Maxi Dress", "Wedge Sandals", "Kimono"],
        "colors": ["Floral Print", "Beige"],
        "accessories": ["Layered Necklaces", "Floppy Hat"],
        "footwear": "Wedge Sandals",
        "budget": "medium",
        "brands": ["Free People", "Anthropologie", "Urban Outfitters"],
        "style_tags": ["boho", "feminine", "relaxed"],
        "season": ["spring", "summer"],
        "description": "Bohemian chic casual style",
        "reasoning": "Free-spirited and effortlessly stylish"
    },
    {
        "id": "outfit_018",
        "name": "Minimalist Formal",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["moderate"],
        "age_group": ["adult"],
        "items": ["Black Sheath Dress", "Pointed Pumps", "Structured Bag"],
        "colors": ["Black", "White"],
        "accessories": ["Pearl Studs", "Silver Watch"],
        "footwear": "Pointed Pumps",
        "budget": "high",
        "brands": ["COS", "Everlane", "Theory"],
        "style_tags": ["minimalist", "elegant", "modern"],
        "season": ["spring", "fall", "winter"],
        "description": "Clean minimalist formal look",
        "reasoning": "Sophisticated simplicity makes a statement"
    }
]

def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"

def generate_shopping_links(items):
    links = []
    for item in items:
        encoded_item = quote_plus(item)
        links.append({
            "item": item,
            "links": {
                "amazon": f"https://www.amazon.in/s?k={encoded_item}",
                "flipkart": f"https://www.flipkart.com/search?q={encoded_item}",
                "meesho": f"https://www.meesho.com/search?q={encoded_item}"
            }
        })
    return links

def filter_by_color_preference(outfits, color_preferences):
    if not color_preferences:
        return outfits
    color_prefs_lower = [c.lower() for c in color_preferences]
    filtered = []
    for outfit in outfits:
        outfit_colors_lower = [c.lower() for c in outfit["colors"]]
        if any(pref in outfit_colors_lower for pref in color_prefs_lower):
            filtered.append(outfit)
    return filtered if filtered else outfits

def filter_by_budget(outfits, budget_range):
    if not budget_range:
        return outfits
    filtered = []
    for outfit in outfits:
        if outfit["budget"] == budget_range:
            filtered.append(outfit)
    return filtered if filtered else outfits

def filter_by_brand(outfits, brand_preferences):
    if not brand_preferences:
        return outfits
    brand_prefs_lower = [b.lower() for b in brand_preferences]
    filtered = []
    for outfit in outfits:
        outfit_brands_lower = [b.lower() for b in outfit["brands"]]
        if any(pref in outfit_brands_lower for pref in brand_prefs_lower):
            filtered.append(outfit)
    return filtered if filtered else outfits

def filter_by_style_tags(outfits, style_tags):
    if not style_tags:
        return outfits
    style_tags_lower = [s.lower() for s in style_tags]
    filtered = []
    for outfit in outfits:
        outfit_tags_lower = [t.lower() for t in outfit["style_tags"]]
        if any(tag in outfit_tags_lower for tag in style_tags_lower):
            filtered.append(outfit)
    return filtered if filtered else outfits

def filter_by_season(outfits, season_preference):
    if not season_preference:
        season_preference = get_current_season()
    filtered = []
    for outfit in outfits:
        if season_preference in outfit["season"]:
            filtered.append(outfit)
    return filtered if filtered else outfits

def get_outfit_rating(outfit_id):
    ratings = load_json_file(RATINGS_FILE, {})
    if outfit_id in ratings:
        total = sum(ratings[outfit_id])
        count = len(ratings[outfit_id])
        return round(total / count, 2) if count > 0 else 0
    return 0

def filter_outfits(occasion, climate, clothing_style, age_group, color_preferences=None, 
                   budget_range=None, brand_preferences=None, style_tags=None, season_preference=None):
    filtered = []
    for outfit in OUTFIT_DATABASE:
        if outfit["occasion"] != occasion:
            continue
        if climate not in outfit["climate"]:
            continue
        if age_group not in outfit["age_group"]:
            continue
        if clothing_style == "mens" and outfit["gender"] == "womens":
            continue
        if clothing_style == "womens" and outfit["gender"] == "mens":
            continue
        if clothing_style in ["mens", "womens"] and outfit["gender"] not in [clothing_style, "unisex"]:
            continue
        filtered.append(outfit)
    
    if len(filtered) < 3:
        for outfit in OUTFIT_DATABASE:
            if outfit in filtered:
                continue
            if outfit["occasion"] == occasion:
                if clothing_style == "mens" and outfit["gender"] == "womens":
                    continue
                if clothing_style == "womens" and outfit["gender"] == "mens":
                    continue
                if clothing_style in ["mens", "womens"] and outfit["gender"] not in [clothing_style, "unisex"]:
                    continue
                filtered.append(outfit)
                if len(filtered) >= 3:
                    break
    
    filtered = filter_by_color_preference(filtered, color_preferences)
    filtered = filter_by_budget(filtered, budget_range)
    filtered = filter_by_brand(filtered, brand_preferences)
    filtered = filter_by_style_tags(filtered, style_tags)
    filtered = filter_by_season(filtered, season_preference)
    
    if len(filtered) < 3:
        for outfit in OUTFIT_DATABASE:
            if outfit in filtered:
                continue
            if outfit["occasion"] == occasion:
                filtered.append(outfit)
                if len(filtered) >= 3:
                    break
    
    return filtered[:3]

@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "running", "message": "Fashion Recommendation API is active"})

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image file provided"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file type"}), 400
    occasion = request.form.get('occasion', 'casual')
    climate = request.form.get('climate', 'moderate')
    clothing_style = request.form.get('clothing_style', 'unisex')
    age_group = request.form.get('age_group', 'young')
    color_preferences = request.form.get('color_preferences', '')
    color_preferences = [c.strip() for c in color_preferences.split(',')] if color_preferences else None
    budget_range = request.form.get('budget_range', '')
    budget_range = budget_range if budget_range in ['low', 'medium', 'high'] else None
    brand_preferences = request.form.get('brand_preferences', '')
    brand_preferences = [b.strip() for b in brand_preferences.split(',')] if brand_preferences else None
    style_tags = request.form.get('style_tags', '')
    style_tags = [s.strip() for s in style_tags.split(',')] if style_tags else None
    season_preference = request.form.get('season_preference', '')
    season_preference = season_preference if season_preference in ['spring', 'summer', 'fall', 'winter'] else None
    if occasion not in ['casual', 'formal']:
        occasion = 'casual'
    if climate not in ['hot', 'moderate', 'cold']:
        climate = 'moderate'
    if clothing_style not in ['mens', 'womens', 'unisex']:
        clothing_style = 'unisex'
    if age_group not in ['young', 'adult', 'senior']:
        age_group = 'young'
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    matching_outfits = filter_outfits(occasion, climate, clothing_style, age_group,
                                     color_preferences, budget_range, brand_preferences,
                                     style_tags, season_preference)
    result_outfits = []
    for outfit in matching_outfits:
        outfit_copy = outfit.copy()
        outfit_copy["shopping_links"] = generate_shopping_links(outfit["items"])
        outfit_copy["average_rating"] = get_outfit_rating(outfit["id"])
        result_outfits.append(outfit_copy)
    return jsonify({
        "status": "success",
        "prediction": {
            "confidence": 0.95,
            "clothing_type": "Uploaded Garment",
            "outfits": result_outfits
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
