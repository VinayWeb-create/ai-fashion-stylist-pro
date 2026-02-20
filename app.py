from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from urllib.parse import quote_plus
import json
from datetime import datetime
from bson import ObjectId
import secrets

# Import new modules
try:
    from auth import (
        hash_password, verify_password, generate_jwt_token, 
        verify_jwt_token, generate_magic_link_token, verify_magic_link_token,
        send_magic_link_email, token_required, optional_token
    )
    from models import User, WardrobeItem, WardrobeInsights, init_db
    from wardrobe_intelligence import analyze_wardrobe_gaps, calculate_wardrobe_balance
    MONGODB_ENABLED = True
except Exception as e:
    print(f"MongoDB features disabled: {e}")
    MONGODB_ENABLED = False
    # Create dummy decorators when MongoDB is disabled
    def token_required(f):
        return f
    def optional_token(f):
        return f

app = Flask(__name__)
CORS(app)

@app.before_request
def ensure_db_init():
    """Ensure database is initialized before any request, but don't block forever"""
    if MONGODB_ENABLED and not getattr(app, '_db_ready', False):
        try:
            # Check connection with a quick ping
            from pymongo.errors import ServerSelectionTimeoutError
            from models import client
            client.admin.command('ping')
            init_db()
            app._db_ready = True
        except Exception as e:
            app.logger.warning(f"Lazy DB initialization skipped or failed: {e}")
            # We don't set _db_ready to True so it can retry next time

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
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def outfit_exists(outfit_id):
    return any(outfit.get('id') == outfit_id for outfit in OUTFIT_DATABASE)

def normalize_device_id(device_id):
    if not isinstance(device_id, str):
        return ''
    return device_id.strip()[:128]

# ============================================================================
# EXPANDED OUTFIT DATABASE - 63 Premium Outfits
# ============================================================================

OUTFIT_DATABASE = [
    # Original 20 outfits
    {
        "id": "outfit_001",
        "name": "Classic Casual Denim",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["college", "daily", "travel"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
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
        "occasion_subtype": ["travel", "daily"],
        "climate": ["hot"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["office", "meeting", "interview"],
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "body_type": ["regular", "relaxed"],
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
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["college", "daily"],
        "climate": ["cold"],
        "age_group": ["young", "adult"],
        "body_type": ["regular", "relaxed"],
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
        "occasion_subtype": ["college", "daily"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["travel", "daily"],
        "climate": ["hot"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
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
        "occasion": "party",
        "occasion_subtype": ["wedding", "night"],
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "body_type": ["regular", "relaxed"],
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
        "occasion_subtype": ["office", "meeting", "interview"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["college", "daily"],
        "climate": ["cold"],
        "age_group": ["young", "adult"],
        "body_type": ["regular", "relaxed"],
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
        "occasion": "party",
        "occasion_subtype": ["night", "festival"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["college", "daily"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
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
        "occasion_subtype": ["college", "travel"],
        "climate": ["hot", "moderate", "cold"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
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
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["adult"],
        "body_type": ["regular", "relaxed"],
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
        "occasion_subtype": ["college", "daily"],
        "climate": ["hot", "moderate"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["college", "daily"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
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
        "occasion_subtype": ["travel", "daily"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
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
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["adult"],
        "body_type": ["slim", "regular"],
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
    },
    {
        "id": "outfit_019",
        "name": "Traditional Ethnic Wear",
        "gender": "womens",
        "occasion": "ethnic",
        "occasion_subtype": ["traditional", "festive"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult", "senior"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Silk Saree", "Blouse", "Traditional Jewelry", "Heels"],
        "colors": ["Red", "Gold"],
        "accessories": ["Bangles", "Earrings", "Necklace"],
        "footwear": "Heels",
        "budget": "high",
        "brands": ["FabIndia", "Sabyasachi", "Ritu Kumar"],
        "style_tags": ["traditional", "elegant", "festive"],
        "season": ["spring", "summer", "fall", "winter"],
        "description": "Classic traditional ethnic attire",
        "reasoning": "Timeless elegance for cultural celebrations"
    },
    {
        "id": "outfit_020",
        "name": "Festive Kurta Set",
        "gender": "mens",
        "occasion": "ethnic",
        "occasion_subtype": ["traditional", "festive"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult", "senior"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Kurta", "Churidar", "Nehru Jacket", "Mojari"],
        "colors": ["Cream", "Gold"],
        "accessories": ["Watch", "Pocket Square"],
        "footwear": "Mojari",
        "budget": "medium",
        "brands": ["Manyavar", "FabIndia", "Soch"],
        "style_tags": ["traditional", "festive", "elegant"],
        "season": ["spring", "summer", "fall", "winter"],
        "description": "Traditional festive attire for men",
        "reasoning": "Perfect blend of tradition and contemporary style"
    },
    
    # =========================================================================
    # NEW EXPANDED OUTFITS (021-063)
    # =========================================================================
    
    {
        "id": "outfit_021",
        "name": "Street Style Bomber",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["college", "daily"],
        "climate": ["moderate", "cold"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Black Bomber Jacket", "White T-Shirt", "Black Skinny Jeans", "White Sneakers"],
        "colors": ["Black", "White"],
        "accessories": ["Baseball Cap", "Minimalist Watch"],
        "footwear": "White Sneakers",
        "budget": "medium",
        "brands": ["Zara", "H&M", "Adidas"],
        "style_tags": ["streetwear", "urban", "trendy"],
        "season": ["fall", "winter", "spring"],
        "description": "Modern street style with bomber jacket",
        "reasoning": "Trendy urban look perfect for college students and young adults"
    },
    {
        "id": "outfit_022",
        "name": "Preppy Campus Look",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["college", "daily"],
        "climate": ["moderate"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Oxford Shirt", "Khaki Chinos", "Boat Shoes", "Sweater"],
        "colors": ["Light Blue", "Khaki", "Navy"],
        "accessories": ["Leather Belt", "Canvas Backpack"],
        "footwear": "Boat Shoes",
        "budget": "medium",
        "brands": ["Gant", "Tommy Hilfiger", "Sperry"],
        "style_tags": ["preppy", "collegiate", "smart-casual"],
        "season": ["spring", "fall"],
        "description": "Classic preppy style for campus",
        "reasoning": "Timeless college look that's both comfortable and put-together"
    },
    {
        "id": "outfit_023",
        "name": "Athleisure Comfort",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "travel"],
        "climate": ["moderate", "hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Track Jacket", "Athletic T-Shirt", "Joggers", "Running Shoes"],
        "colors": ["Grey", "Black", "Navy"],
        "accessories": ["Sports Watch", "Gym Bag"],
        "footwear": "Running Shoes",
        "budget": "low",
        "brands": ["Nike", "Adidas", "Puma"],
        "style_tags": ["athleisure", "sporty", "comfortable"],
        "season": ["spring", "summer", "fall"],
        "description": "Comfortable athleisure for everyday wear",
        "reasoning": "Perfect blend of athletic wear and casual style"
    },
    {
        "id": "outfit_024",
        "name": "Minimalist Monochrome",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "college"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Black Turtleneck", "Grey Wool Pants", "Black Chelsea Boots"],
        "colors": ["Black", "Grey"],
        "accessories": ["Silver Chain", "Minimalist Watch"],
        "footwear": "Chelsea Boots",
        "budget": "medium",
        "brands": ["COS", "Uniqlo", "Zara"],
        "style_tags": ["minimalist", "modern", "sophisticated"],
        "season": ["fall", "winter"],
        "description": "Sleek minimalist aesthetic",
        "reasoning": "Clean, modern look with emphasis on silhouette and texture"
    },
    {
        "id": "outfit_025",
        "name": "Denim on Denim",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "travel"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Light Denim Jacket", "White Henley", "Dark Denim Jeans", "Brown Boots"],
        "colors": ["Light Blue", "White", "Dark Blue", "Brown"],
        "accessories": ["Leather Bracelet", "Aviator Sunglasses"],
        "footwear": "Brown Boots",
        "budget": "medium",
        "brands": ["Levis", "Wrangler", "Diesel"],
        "style_tags": ["denim", "rugged", "classic"],
        "season": ["spring", "fall"],
        "description": "Classic double denim done right",
        "reasoning": "Timeless denim combination with contrasting shades"
    },
    {
        "id": "outfit_026",
        "name": "Beach Vacation Casual",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["travel", "daily"],
        "climate": ["hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Linen Shirt", "Cotton Shorts", "Flip Flops"],
        "colors": ["White", "Beige", "Tan"],
        "accessories": ["Straw Hat", "Sunglasses", "Beach Bag"],
        "footwear": "Flip Flops",
        "budget": "low",
        "brands": ["Uniqlo", "Gap", "Old Navy"],
        "style_tags": ["vacation", "breezy", "relaxed"],
        "season": ["summer"],
        "description": "Ultimate beach and resort wear",
        "reasoning": "Light, breathable fabrics perfect for tropical destinations"
    },
    {
        "id": "outfit_027",
        "name": "Flannel Lumberjack",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "college"],
        "climate": ["cold", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["regular", "relaxed"],
        "items": ["Plaid Flannel Shirt", "Grey T-Shirt", "Dark Jeans", "Work Boots"],
        "colors": ["Red", "Black", "Grey", "Brown"],
        "accessories": ["Beanie", "Backpack"],
        "footwear": "Work Boots",
        "budget": "low",
        "brands": ["Carhartt", "Dickies", "Timberland"],
        "style_tags": ["rugged", "outdoorsy", "casual"],
        "season": ["fall", "winter"],
        "description": "Rugged outdoor-inspired style",
        "reasoning": "Warm, practical, and effortlessly stylish"
    },
    {
        "id": "outfit_028",
        "name": "Smart Casual Weekend",
        "gender": "mens",
        "occasion": "casual",
        "occasion_subtype": ["daily"],
        "climate": ["moderate"],
        "age_group": ["adult"],
        "body_type": ["regular", "relaxed"],
        "items": ["Knit Polo", "Tailored Shorts", "Loafers"],
        "colors": ["Navy", "Beige", "Brown"],
        "accessories": ["Leather Watch", "Sunglasses"],
        "footwear": "Loafers",
        "budget": "medium",
        "brands": ["Lacoste", "Ralph Lauren", "Brooks Brothers"],
        "style_tags": ["smart-casual", "refined", "weekend"],
        "season": ["spring", "summer"],
        "description": "Elevated casual for weekend outings",
        "reasoning": "Polished yet relaxed for social occasions"
    },
    {
        "id": "outfit_029",
        "name": "Tech Industry Professional",
        "gender": "mens",
        "occasion": "formal",
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Dark Blazer", "Premium T-Shirt", "Dark Jeans", "Minimalist Sneakers"],
        "colors": ["Black", "Grey", "Navy"],
        "accessories": ["Apple Watch", "Laptop Bag"],
        "footwear": "Minimalist Sneakers",
        "budget": "medium",
        "brands": ["Everlane", "Theory", "Common Projects"],
        "style_tags": ["tech", "modern", "smart-casual"],
        "season": ["spring", "summer", "fall"],
        "description": "Modern tech professional attire",
        "reasoning": "Silicon Valley meets sophistication"
    },
    {
        "id": "outfit_030",
        "name": "Classic Three-Piece Suit",
        "gender": "mens",
        "occasion": "formal",
        "occasion_subtype": ["interview", "meeting", "office"],
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "body_type": ["slim", "regular"],
        "items": ["Charcoal Suit", "White Dress Shirt", "Vest", "Leather Oxford", "Silk Tie"],
        "colors": ["Charcoal", "White", "Burgundy"],
        "accessories": ["Pocket Square", "Cufflinks", "Leather Belt"],
        "footwear": "Leather Oxford",
        "budget": "high",
        "brands": ["Hugo Boss", "Armani", "Canali"],
        "style_tags": ["formal", "executive", "powerful"],
        "season": ["fall", "winter", "spring"],
        "description": "Power dressing with three-piece sophistication",
        "reasoning": "Maximum professionalism for high-stakes situations"
    },
    {
        "id": "outfit_031",
        "name": "Summer Business Casual",
        "gender": "mens",
        "occasion": "formal",
        "occasion_subtype": ["office"],
        "climate": ["hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Linen Blazer", "Cotton Shirt", "Chinos", "Loafers"],
        "colors": ["Beige", "Light Blue", "Khaki"],
        "accessories": ["Woven Belt", "Sunglasses"],
        "footwear": "Loafers",
        "budget": "medium",
        "brands": ["Massimo Dutti", "Banana Republic", "J.Crew"],
        "style_tags": ["business-casual", "summer", "breathable"],
        "season": ["summer"],
        "description": "Professional yet comfortable for hot weather",
        "reasoning": "Breathable fabrics maintain professionalism in heat"
    },
    {
        "id": "outfit_032",
        "name": "Creative Professional",
        "gender": "mens",
        "occasion": "formal",
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Patterned Blazer", "Black Turtleneck", "Dark Trousers", "Monk Strap Shoes"],
        "colors": ["Navy Pattern", "Black", "Grey"],
        "accessories": ["Designer Watch", "Leather Briefcase"],
        "footwear": "Monk Strap Shoes",
        "budget": "high",
        "brands": ["Ted Baker", "Paul Smith", "Reiss"],
        "style_tags": ["creative", "fashion-forward", "sophisticated"],
        "season": ["fall", "winter", "spring"],
        "description": "Fashion-forward professional attire",
        "reasoning": "Expresses creativity while maintaining professionalism"
    },
    {
        "id": "outfit_033",
        "name": "Banking & Finance Formal",
        "gender": "mens",
        "occasion": "formal",
        "occasion_subtype": ["office", "meeting", "interview"],
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "body_type": ["regular", "relaxed"],
        "items": ["Navy Pinstripe Suit", "White Dress Shirt", "Conservative Tie", "Cap-toe Oxford"],
        "colors": ["Navy", "White", "Red"],
        "accessories": ["Leather Belt", "Classic Watch", "Briefcase"],
        "footwear": "Cap-toe Oxford",
        "budget": "high",
        "brands": ["Brooks Brothers", "Ralph Lauren", "Brioni"],
        "style_tags": ["conservative", "formal", "traditional"],
        "season": ["fall", "winter", "spring"],
        "description": "Traditional banking attire",
        "reasoning": "Conservative elegance for financial sectors"
    },
    {
        "id": "outfit_034",
        "name": "Black Tie Tuxedo",
        "gender": "mens",
        "occasion": "party",
        "occasion_subtype": ["wedding", "night"],
        "climate": ["moderate", "cold"],
        "age_group": ["young", "adult", "senior"],
        "body_type": ["slim", "regular"],
        "items": ["Black Tuxedo", "White Dress Shirt", "Bow Tie", "Patent Leather Shoes"],
        "colors": ["Black", "White"],
        "accessories": ["Cufflinks", "Pocket Square", "Cummerbund"],
        "footwear": "Patent Leather Shoes",
        "budget": "high",
        "brands": ["Giorgio Armani", "Tom Ford", "Hugo Boss"],
        "style_tags": ["black-tie", "formal", "elegant"],
        "season": ["fall", "winter", "spring"],
        "description": "Classic black tie elegance",
        "reasoning": "Timeless sophistication for formal events"
    },
    {
        "id": "outfit_035",
        "name": "Cocktail Party Smart",
        "gender": "mens",
        "occasion": "party",
        "occasion_subtype": ["night", "festival"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Velvet Blazer", "Black Dress Shirt", "Dark Jeans", "Chelsea Boots"],
        "colors": ["Burgundy", "Black"],
        "accessories": ["Statement Watch", "Pocket Square"],
        "footwear": "Chelsea Boots",
        "budget": "medium",
        "brands": ["Zara", "Topman", "ASOS"],
        "style_tags": ["cocktail", "stylish", "night-out"],
        "season": ["fall", "winter"],
        "description": "Stylish cocktail party attire",
        "reasoning": "Balances formality with personality"
    },
    {
        "id": "outfit_036",
        "name": "Festival Streetwear",
        "gender": "mens",
        "occasion": "party",
        "occasion_subtype": ["festival"],
        "climate": ["hot", "moderate"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Graphic Band T-Shirt", "Ripped Jeans", "High-top Sneakers", "Denim Jacket"],
        "colors": ["Black", "Vintage Wash", "White"],
        "accessories": ["Festival Wristbands", "Sunglasses", "Crossbody Bag"],
        "footwear": "High-top Sneakers",
        "budget": "low",
        "brands": ["Urban Outfitters", "Pull&Bear", "Converse"],
        "style_tags": ["festival", "edgy", "youthful"],
        "season": ["spring", "summer"],
        "description": "Edgy festival-ready outfit",
        "reasoning": "Comfortable yet statement-making for music festivals"
    },
    {
        "id": "outfit_037",
        "name": "Wedding Guest Summer",
        "gender": "mens",
        "occasion": "party",
        "occasion_subtype": ["wedding"],
        "climate": ["hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Light Grey Suit", "Pastel Shirt", "Brown Leather Shoes"],
        "colors": ["Light Grey", "Pastel Blue", "Brown"],
        "accessories": ["Sunglasses", "Watch"],
        "footwear": "Brown Leather Shoes",
        "budget": "medium",
        "brands": ["Suit Supply", "Charles Tyrwhitt", "Clarks"],
        "style_tags": ["wedding", "summer", "elegant-casual"],
        "season": ["summer"],
        "description": "Summer wedding guest attire",
        "reasoning": "Elegant yet breathable for outdoor ceremonies"
    },
    {
        "id": "outfit_038",
        "name": "Classic Kurta Pajama",
        "gender": "mens",
        "occasion": "ethnic",
        "occasion_subtype": ["traditional", "festive"],
        "climate": ["moderate", "hot"],
        "age_group": ["young", "adult", "senior"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Cotton Kurta", "Churidar Pajama", "Ethnic Mojari"],
        "colors": ["White", "Cream", "Gold"],
        "accessories": ["Ethnic Watch", "Shawl"],
        "footwear": "Ethnic Mojari",
        "budget": "medium",
        "brands": ["Manyavar", "Fabindia", "Ethnix"],
        "style_tags": ["traditional", "ethnic", "comfortable"],
        "season": ["spring", "summer", "fall"],
        "description": "Traditional Indian comfort",
        "reasoning": "Classic ethnic wear suitable for festivals and family gatherings"
    },
    {
        "id": "outfit_039",
        "name": "Royal Sherwani",
        "gender": "mens",
        "occasion": "ethnic",
        "occasion_subtype": ["festive"],
        "climate": ["moderate", "cold"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Embroidered Sherwani", "Churidar", "Ethnic Jutis", "Turban"],
        "colors": ["Maroon", "Gold", "Cream"],
        "accessories": ["Brooch", "Sherwani Buttons", "Stole"],
        "footwear": "Ethnic Jutis",
        "budget": "high",
        "brands": ["Manyavar", "Raymond Ethnix", "Sabyasachi"],
        "style_tags": ["royal", "festive", "luxurious"],
        "season": ["fall", "winter"],
        "description": "Regal ethnic grandeur",
        "reasoning": "Perfect for weddings and major celebrations"
    },
    {
        "id": "outfit_040",
        "name": "Contemporary Nehru Jacket",
        "gender": "mens",
        "occasion": "ethnic",
        "occasion_subtype": ["festive", "traditional"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Nehru Jacket", "White Kurta", "Straight Pants", "Leather Jutis"],
        "colors": ["Navy", "White", "Black"],
        "accessories": ["Pocket Square", "Watch"],
        "footwear": "Leather Jutis",
        "budget": "medium",
        "brands": ["Fabindia", "AND Designs", "Peter England Elite"],
        "style_tags": ["contemporary", "fusion", "sophisticated"],
        "season": ["fall", "winter", "spring"],
        "description": "Modern ethnic fusion",
        "reasoning": "Blend of traditional and contemporary styling"
    },
    {
        "id": "outfit_041",
        "name": "Casual Denim & Tee",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "college"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Graphic T-Shirt", "High-Waisted Jeans", "White Sneakers"],
        "colors": ["White", "Blue", "Various"],
        "accessories": ["Crossbody Bag", "Hoop Earrings"],
        "footwear": "White Sneakers",
        "budget": "low",
        "brands": ["Zara", "Forever 21", "H&M"],
        "style_tags": ["casual", "effortless", "everyday"],
        "season": ["spring", "summer", "fall"],
        "description": "Classic casual comfort",
        "reasoning": "Timeless and versatile for everyday wear"
    },
    {
        "id": "outfit_042",
        "name": "Boho Chic Maxi",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "travel"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Flowy Maxi Dress", "Sandals", "Denim Jacket"],
        "colors": ["Floral Print", "Earth Tones"],
        "accessories": ["Layered Necklaces", "Floppy Hat", "Tote Bag"],
        "footwear": "Sandals",
        "budget": "medium",
        "brands": ["Free People", "Anthropologie", "Mango"],
        "style_tags": ["boho", "free-spirited", "feminine"],
        "season": ["spring", "summer"],
        "description": "Bohemian elegance",
        "reasoning": "Effortlessly stylish and comfortable"
    },
    {
        "id": "outfit_043",
        "name": "Athleisure Chic",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "college"],
        "climate": ["moderate", "hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Sports Bra", "Leggings", "Oversized Hoodie", "Running Shoes"],
        "colors": ["Black", "Grey", "White"],
        "accessories": ["Smartwatch", "Gym Bag"],
        "footwear": "Running Shoes",
        "budget": "low",
        "brands": ["Lululemon", "Athleta", "Nike"],
        "style_tags": ["athleisure", "comfortable", "sporty"],
        "season": ["spring", "summer", "fall"],
        "description": "Athletic meets casual",
        "reasoning": "Perfect blend of comfort and style"
    },
    {
        "id": "outfit_044",
        "name": "Preppy Skirt Set",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["college", "daily"],
        "climate": ["moderate"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Knit Sweater", "Pleated Mini Skirt", "Mary Jane Shoes"],
        "colors": ["Cream", "Plaid Pattern", "Black"],
        "accessories": ["Headband", "Small Handbag"],
        "footwear": "Mary Jane Shoes",
        "budget": "medium",
        "brands": ["Brandy Melville", "Urban Outfitters", "Princess Polly"],
        "style_tags": ["preppy", "youthful", "school-chic"],
        "season": ["fall", "spring"],
        "description": "Classic collegiate preppy",
        "reasoning": "Sweet and polished campus style"
    },
    {
        "id": "outfit_045",
        "name": "Minimalist Capsule",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["daily"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["White Button-Up", "Black Wide-Leg Pants", "Mules"],
        "colors": ["White", "Black"],
        "accessories": ["Gold Jewelry", "Structured Bag"],
        "footwear": "Mules",
        "budget": "medium",
        "brands": ["COS", "Everlane", "Arket"],
        "style_tags": ["minimalist", "timeless", "elegant"],
        "season": ["spring", "summer", "fall"],
        "description": "Effortless minimalism",
        "reasoning": "Clean lines and neutral palette"
    },
    {
        "id": "outfit_046",
        "name": "Summer Beach Cover",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["travel", "daily"],
        "climate": ["hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Crochet Cover-Up", "Bikini", "Slide Sandals"],
        "colors": ["White", "Beige", "Colorful Swimwear"],
        "accessories": ["Beach Hat", "Oversized Sunglasses", "Beach Bag"],
        "footwear": "Slide Sandals",
        "budget": "low",
        "brands": ["H&M", "Target", "Aerie"],
        "style_tags": ["beach", "vacation", "relaxed"],
        "season": ["summer"],
        "description": "Perfect beach day outfit",
        "reasoning": "Light, practical, and stylish for beach activities"
    },
    {
        "id": "outfit_047",
        "name": "Cozy Winter Layers",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["daily", "college"],
        "climate": ["cold"],
        "age_group": ["young", "adult"],
        "body_type": ["regular", "relaxed"],
        "items": ["Oversized Sweater", "Leggings", "Puffer Jacket", "Ankle Boots"],
        "colors": ["Cream", "Black", "Brown"],
        "accessories": ["Beanie", "Scarf", "Crossbody Bag"],
        "footwear": "Ankle Boots",
        "budget": "medium",
        "brands": ["Uniqlo", "Gap", "Steve Madden"],
        "style_tags": ["cozy", "winter", "comfortable"],
        "season": ["winter"],
        "description": "Warm and stylish winter layers",
        "reasoning": "Maximum warmth without sacrificing style"
    },
    {
        "id": "outfit_048",
        "name": "Vintage Mom Jeans",
        "gender": "womens",
        "occasion": "casual",
        "occasion_subtype": ["college", "daily"],
        "climate": ["moderate"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Cropped Cardigan", "Mom Jeans", "Platform Sneakers"],
        "colors": ["Pastel", "Light Blue", "White"],
        "accessories": ["90s Sunglasses", "Mini Backpack"],
        "footwear": "Platform Sneakers",
        "budget": "low",
        "brands": ["Thrifted", "Zara", "Pull&Bear"],
        "style_tags": ["vintage", "90s", "trendy"],
        "season": ["spring", "fall"],
        "description": "90s-inspired vintage vibes",
        "reasoning": "Nostalgic and on-trend"
    },
    {
        "id": "outfit_049",
        "name": "Power Suit Executive",
        "gender": "womens",
        "occasion": "formal",
        "occasion_subtype": ["office", "meeting", "interview"],
        "climate": ["moderate", "cold"],
        "age_group": ["adult", "senior"],
        "body_type": ["slim", "regular"],
        "items": ["Tailored Blazer", "Matching Trousers", "Silk Blouse", "Pointed Pumps"],
        "colors": ["Black", "White"],
        "accessories": ["Statement Watch", "Leather Tote"],
        "footwear": "Pointed Pumps",
        "budget": "high",
        "brands": ["Theory", "Hugo Boss", "Max Mara"],
        "style_tags": ["powerful", "executive", "professional"],
        "season": ["fall", "winter", "spring"],
        "description": "Ultimate power dressing",
        "reasoning": "Commands authority and respect"
    },
    {
        "id": "outfit_050",
        "name": "Soft Professional",
        "gender": "womens",
        "occasion": "formal",
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Soft Blazer", "Blouse", "Pencil Skirt", "Block Heels"],
        "colors": ["Beige", "Cream", "Nude"],
        "accessories": ["Delicate Jewelry", "Structured Handbag"],
        "footwear": "Block Heels",
        "budget": "medium",
        "brands": ["Massimo Dutti", "Reiss", "J.Crew"],
        "style_tags": ["sophisticated", "feminine", "professional"],
        "season": ["spring", "summer", "fall"],
        "description": "Feminine professionalism",
        "reasoning": "Approachable yet authoritative"
    },
    {
        "id": "outfit_051",
        "name": "Creative Director",
        "gender": "womens",
        "occasion": "formal",
        "occasion_subtype": ["office", "meeting"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Statement Blazer", "Silk Camisole", "Wide-Leg Trousers", "Designer Loafers"],
        "colors": ["Bold Colors", "Black", "Patterns"],
        "accessories": ["Oversized Glasses", "Designer Bag"],
        "footwear": "Designer Loafers",
        "budget": "high",
        "brands": ["Gucci", "Prada", "Stella McCartney"],
        "style_tags": ["creative", "fashion-forward", "bold"],
        "season": ["spring", "fall"],
        "description": "Fashion meets function",
        "reasoning": "Expresses creativity in professional setting"
    },
    {
        "id": "outfit_052",
        "name": "Summer Office Chic",
        "gender": "womens",
        "occasion": "formal",
        "occasion_subtype": ["office"],
        "climate": ["hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Sleeveless Blouse", "Linen Trousers", "Sandal Heels"],
        "colors": ["White", "Beige", "Pastels"],
        "accessories": ["Simple Jewelry", "Tote Bag"],
        "footwear": "Sandal Heels",
        "budget": "medium",
        "brands": ["Banana Republic", "Ann Taylor", "Loft"],
        "style_tags": ["summer-office", "breathable", "professional"],
        "season": ["summer"],
        "description": "Professional summer comfort",
        "reasoning": "Keeps cool while maintaining professionalism"
    },
    {
        "id": "outfit_053",
        "name": "Monochrome Professional",
        "gender": "womens",
        "occasion": "formal",
        "occasion_subtype": ["office", "interview"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Turtleneck", "Tailored Pants", "Blazer", "Ankle Boots"],
        "colors": ["All Black", "All Navy", "All Grey"],
        "accessories": ["Minimalist Watch", "Structured Bag"],
        "footwear": "Ankle Boots",
        "budget": "medium",
        "brands": ["COS", "& Other Stories", "Zara"],
        "style_tags": ["monochrome", "sleek", "modern"],
        "season": ["fall", "winter"],
        "description": "Sleek monochrome sophistication",
        "reasoning": "Effortlessly chic and professional"
    },
    {
        "id": "outfit_054",
        "name": "Little Black Dress",
        "gender": "womens",
        "occasion": "party",
        "occasion_subtype": ["night", "wedding"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Black Cocktail Dress", "Strappy Heels", "Clutch"],
        "colors": ["Black"],
        "accessories": ["Statement Earrings", "Delicate Necklace"],
        "footwear": "Strappy Heels",
        "budget": "medium",
        "brands": ["ASOS", "Revolve", "Zara"],
        "style_tags": ["classic", "elegant", "timeless"],
        "season": ["spring", "summer", "fall"],
        "description": "Timeless LBD elegance",
        "reasoning": "Can never go wrong with a classic black dress"
    },
    {
        "id": "outfit_055",
        "name": "Sequin Party Glam",
        "gender": "womens",
        "occasion": "party",
        "occasion_subtype": ["night", "festival"],
        "climate": ["moderate"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Sequin Mini Dress", "Platform Heels", "Mini Clutch"],
        "colors": ["Gold", "Silver", "Rose Gold"],
        "accessories": ["Statement Earrings", "Body Glitter"],
        "footwear": "Platform Heels",
        "budget": "low",
        "brands": ["Pretty Little Thing", "Boohoo", "Missguided"],
        "style_tags": ["party", "glamorous", "bold"],
        "season": ["fall", "winter"],
        "description": "Dazzling party ready",
        "reasoning": "Stand out with sparkle and glamour"
    },
    {
        "id": "outfit_056",
        "name": "Wedding Guest Elegance",
        "gender": "womens",
        "occasion": "party",
        "occasion_subtype": ["wedding"],
        "climate": ["moderate", "hot"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Floral Midi Dress", "Block Heels", "Clutch"],
        "colors": ["Pastel Florals", "Soft Colors"],
        "accessories": ["Fascinator", "Pearl Earrings"],
        "footwear": "Block Heels",
        "budget": "medium",
        "brands": ["Reformation", "Ted Baker", "Coast"],
        "style_tags": ["wedding", "elegant", "feminine"],
        "season": ["spring", "summer"],
        "description": "Perfect wedding guest attire",
        "reasoning": "Elegant without upstaging the bride"
    },
    {
        "id": "outfit_057",
        "name": "Cocktail Hour Chic",
        "gender": "womens",
        "occasion": "party",
        "occasion_subtype": ["night"],
        "climate": ["moderate"],
        "age_group": ["adult"],
        "body_type": ["regular", "relaxed"],
        "items": ["Satin Slip Dress", "Heeled Sandals", "Evening Clutch"],
        "colors": ["Emerald", "Burgundy", "Navy"],
        "accessories": ["Gold Jewelry", "Shawl"],
        "footwear": "Heeled Sandals",
        "budget": "medium",
        "brands": ["Anthropologie", "& Other Stories", "Mango"],
        "style_tags": ["sophisticated", "cocktail", "elegant"],
        "season": ["fall", "winter", "spring"],
        "description": "Sophisticated cocktail attire",
        "reasoning": "Effortlessly chic for evening events"
    },
    {
        "id": "outfit_058",
        "name": "Festival Boho Queen",
        "gender": "womens",
        "occasion": "party",
        "occasion_subtype": ["festival"],
        "climate": ["hot"],
        "age_group": ["young"],
        "body_type": ["slim", "regular"],
        "items": ["Crochet Top", "Denim Shorts", "Cowboy Boots", "Kimono"],
        "colors": ["Earth Tones", "Vintage Wash"],
        "accessories": ["Flower Crown", "Layered Jewelry", "Fringe Bag"],
        "footwear": "Cowboy Boots",
        "budget": "low",
        "brands": ["Free People", "Urban Outfitters", "Festival Vendors"],
        "style_tags": ["festival", "boho", "free-spirited"],
        "season": ["summer"],
        "description": "Ultimate festival style",
        "reasoning": "Comfortable and Instagram-ready"
    },
    {
        "id": "outfit_059",
        "name": "Classic Saree Elegance",
        "gender": "womens",
        "occasion": "ethnic",
        "occasion_subtype": ["traditional", "festive"],
        "climate": ["moderate", "hot"],
        "age_group": ["adult", "senior"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Silk Saree", "Matching Blouse", "Petticoat", "Ethnic Sandals"],
        "colors": ["Red", "Gold", "Traditional Colors"],
        "accessories": ["Traditional Jewelry", "Clutch", "Bindi"],
        "footwear": "Ethnic Sandals",
        "budget": "high",
        "brands": ["Sabyasachi", "Raw Mango", "Fabindia"],
        "style_tags": ["traditional", "elegant", "classic"],
        "season": ["fall", "winter", "spring"],
        "description": "Timeless saree beauty",
        "reasoning": "Ultimate traditional Indian elegance"
    },
    {
        "id": "outfit_060",
        "name": "Festive Anarkali",
        "gender": "womens",
        "occasion": "ethnic",
        "occasion_subtype": ["festive"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Embroidered Anarkali", "Churidar", "Dupatta", "Ethnic Jutis"],
        "colors": ["Royal Blue", "Gold", "Pink"],
        "accessories": ["Statement Earrings", "Bangles", "Clutch"],
        "footwear": "Ethnic Jutis",
        "budget": "medium",
        "brands": ["Biba", "W", "Global Desi"],
        "style_tags": ["festive", "graceful", "traditional"],
        "season": ["fall", "winter"],
        "description": "Flowing festive grace",
        "reasoning": "Perfect for celebrations and festivals"
    },
    {
        "id": "outfit_061",
        "name": "Contemporary Kurta Set",
        "gender": "womens",
        "occasion": "ethnic",
        "occasion_subtype": ["traditional", "festive"],
        "climate": ["hot", "moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular", "relaxed"],
        "items": ["Cotton Kurta", "Palazzo Pants", "Dupatta"],
        "colors": ["Pastel", "White", "Block Prints"],
        "accessories": ["Oxidized Jewelry", "Juttis"],
        "footwear": "Ethnic Juttis",
        "budget": "low",
        "brands": ["Fabindia", "Libas", "Aurelia"],
        "style_tags": ["contemporary", "comfortable", "ethnic"],
        "season": ["spring", "summer", "fall"],
        "description": "Modern ethnic comfort",
        "reasoning": "Blend of tradition and contemporary style"
    },
    {
        "id": "outfit_062",
        "name": "Wedding Lehenga",
        "gender": "womens",
        "occasion": "ethnic",
        "occasion_subtype": ["festive"],
        "climate": ["moderate", "cold"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Embroidered Lehenga", "Choli", "Dupatta", "Heels"],
        "colors": ["Red", "Pink", "Gold"],
        "accessories": ["Heavy Jewelry Set", "Clutch", "Maang Tikka"],
        "footwear": "Embellished Heels",
        "budget": "high",
        "brands": ["Sabyasachi", "Manish Malhotra", "Anita Dongre"],
        "style_tags": ["bridal", "luxurious", "festive"],
        "season": ["fall", "winter"],
        "description": "Grand celebration attire",
        "reasoning": "Show-stopping ethnic glamour"
    },
    {
        "id": "outfit_063",
        "name": "Indo-Western Fusion",
        "gender": "womens",
        "occasion": "ethnic",
        "occasion_subtype": ["festive", "traditional"],
        "climate": ["moderate"],
        "age_group": ["young", "adult"],
        "body_type": ["slim", "regular"],
        "items": ["Cape Kurta", "Dhoti Pants", "Heeled Sandals"],
        "colors": ["Monochrome", "Modern Palette"],
        "accessories": ["Contemporary Jewelry", "Clutch"],
        "footwear": "Heeled Sandals",
        "budget": "medium",
        "brands": ["AND Designs", "Label Ritu Kumar", "House of Masaba"],
        "style_tags": ["fusion", "modern", "trendy"],
        "season": ["spring", "fall"],
        "description": "East meets West elegantly",
        "reasoning": "Perfect fusion of cultures"
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

def generate_shopping_links(items, gender="unisex", budget="medium", occasion="casual", occasion_subtype=None):
    links = []
    
    budget_hints = {
        "low": "under 1000",
        "medium": "under 2500",
        "high": "premium"
    }
    
    occasion_contexts = {
        "casual": {"college": "college", "daily": "daily wear", "travel": "travel"},
        "formal": {"office": "office", "meeting": "formal", "interview": "interview"},
        "party": {"night": "party", "wedding": "party wear", "festival": "festive"},
        "ethnic": {"traditional": "traditional", "festive": "festive"}
    }
    
    for item in items:
        gender_prefix = ""
        if gender == "womens":
            gender_prefix = "women "
        elif gender == "mens":
            gender_prefix = "men "
        
        budget_hint = budget_hints.get(budget, "")
        
        occasion_context = ""
        if occasion_subtype and occasion in occasion_contexts:
            occasion_context = occasion_contexts[occasion].get(occasion_subtype, "")
        
        query_parts = [gender_prefix, occasion_context, item, budget_hint]
        qualified_item = " ".join([p for p in query_parts if p]).strip()
        
        encoded_item = quote_plus(qualified_item)
        links.append({
            "item": item,
            "links": {
                "amazon": f"https://www.amazon.in/s?k={encoded_item}",
                "flipkart": f"https://www.flipkart.com/search?q={encoded_item}",
                "meesho": f"https://www.meesho.com/search?q={encoded_item}"
            }
        })
    return links

def calculate_outfit_score(outfit, clothing_style, occasion, occasion_subtype, climate, body_type, budget):
    score = 0
    
    # Critical Match: Gender
    if outfit["gender"] == clothing_style:
        score += 100
    elif outfit["gender"] == "unisex":
        score += 50
    else:
        return 0
    
    # High Priority: Occasion
    if outfit["occasion"] == occasion:
        score += 80
    
    # Sub-occasion match
    if occasion_subtype and occasion_subtype in outfit.get("occasion_subtype", []):
        score += 40
    
    # Climate match
    if climate in outfit["climate"]:
        score += 30
    
    # Medium Priority: Body Type (Enhanced)
    if body_type in outfit.get("body_type", []):
        score += 60
    
    # Medium Priority: Budget (Enhanced)
    if outfit["budget"] == budget:
        score += 40
    elif (budget == "medium" and (outfit["budget"] == "low")) or (budget == "high"):
        score += 20
    
    return score

def rank_and_filter_outfits(occasion, climate, clothing_style, age_group, body_type, budget, occasion_subtype=None):
    scored_outfits = []
    
    for outfit in OUTFIT_DATABASE:
        if age_group not in outfit["age_group"]:
            continue
        
        if clothing_style == "mens" and outfit["gender"] == "womens":
            continue
        if clothing_style == "womens" and outfit["gender"] == "mens":
            continue
        
        score = calculate_outfit_score(outfit, clothing_style, occasion, occasion_subtype, climate, body_type, budget)
        
        if score > 0:
            scored_outfits.append((score, outfit))
    
    scored_outfits.sort(key=lambda x: x[0], reverse=True)
    
    return [outfit for score, outfit in scored_outfits[:3]]

def generate_care_routines(clothing_style, climate, occasion, skin_tone=None, undertone=None, detect_face=False):
    tips = []
    
    fashion_tips_map = {
        "casual_hot": [
            "Choose breathable fabrics like cotton and linen for maximum comfort",
            "Light colors reflect heat better and keep you cooler"
        ],
        "casual_moderate": [
            "Layer with lightweight pieces for versatile styling",
            "Mix textures to add visual interest to your outfit"
        ],
        "casual_cold": [
            "Layer strategically with base, mid, and outer layers",
            "Invest in quality outerwear that complements your wardrobe"
        ],
        "formal_hot": [
            "Opt for lightweight formal fabrics to stay cool and professional",
            "Choose tailored fits that allow air circulation"
        ],
        "formal_moderate": [
            "Classic silhouettes never go out of style",
            "Ensure proper fit for a polished appearance"
        ],
        "formal_cold": [
            "Wool and wool-blend suits provide warmth and sophistication",
            "Layer with dress shirts and vests for added warmth"
        ],
        "party_hot": [
            "Choose statement pieces in breathable fabrics",
            "Bold accessories elevate your party look"
        ],
        "party_moderate": [
            "Balance comfort with glamour for all-night confidence",
            "Metallic accents add festive flair"
        ],
        "party_cold": [
            "Layer with elegant wraps or shawls",
            "Rich fabrics like velvet add luxury"
        ],
        "ethnic_hot": [
            "Choose lightweight traditional fabrics like cotton or linen blends",
            "Traditional silhouettes in breathable materials work best"
        ],
        "ethnic_moderate": [
            "Silk and cotton blends offer comfort and elegance",
            "Traditional jewelry completes the ethnic look"
        ],
        "ethnic_cold": [
            "Layer with traditional shawls or dupattas",
            "Rich fabrics like silk and brocade add warmth"
        ]
    }
    
    key = f"{occasion}_{climate}"
    if key in fashion_tips_map:
        tips.extend(fashion_tips_map[key])
    
    if clothing_style == "mens":
        tips.append("Keep your look sharp with well-fitted clothing")
    elif clothing_style == "womens":
        tips.append("Balance proportions to create a flattering silhouette")
    
    if detect_face and skin_tone:
        if skin_tone in ["fair", "light"]:
            tips.append("Morning: Use a gentle, hydrating face wash suitable for sensitive skin")
            tips.append("Before outing: Apply SPF 50 sunscreen to protect fair skin from UV damage")
            if climate == "cold":
                tips.append("Night care: Use a rich cream moisturizer to combat dryness")
            else:
                tips.append("Daily: A lightweight hydrating moisturizer keeps skin balanced")
        elif skin_tone in ["wheatish", "medium"]:
            tips.append("Morning: A gel-based face wash helps maintain your skin's natural balance")
            tips.append("Before outing: SPF 30+ sunscreen is essential for daily protection")
            if climate == "hot":
                tips.append("Daily: Use an oil-free moisturizer to prevent excess shine")
            else:
                tips.append("Daily: A lightweight moisturizer provides hydration without heaviness")
        elif skin_tone in ["dusky", "deep"]:
            tips.append("Morning: Use a cream-based cleanser to nourish and cleanse deeply")
            tips.append("Before outing: SPF 30 sunscreen helps protect against sun damage")
            tips.append("Daily: A nourishing moisturizer keeps your skin healthy and glowing")
        
        if undertone == "warm" and clothing_style == "womens":
            tips.append("Warm-toned makeup bases complement your natural undertone beautifully")
        elif undertone == "cool" and clothing_style == "womens":
            tips.append("Cool or neutral makeup bases enhance your natural complexion")
        
        if clothing_style == "mens":
            tips.append("Grooming: Keep facial hair well-groomed with regular trimming and beard oil")
        elif clothing_style == "womens":
            tips.append("Makeup: Choose lip and blush shades that harmonize with your outfit colors")
    else:
        tips.append("Maintain good personal hygiene for confidence in any setting")
        if climate == "hot":
            tips.append("Morning: Use a refreshing face wash to stay fresh throughout the day")
        else:
            tips.append("Daily: Keep your skin moisturized to maintain a healthy appearance")
    
    if climate == "cold":
        tips.append("Night care: Don't forget lip balm to prevent chapped lips in cold weather")
    
    if occasion == "formal":
        tips.append("Before outing: A subtle, clean fragrance completes your polished look")
    elif occasion == "party":
        tips.append("Before outing: Choose a signature fragrance that reflects your personality")
    
    if clothing_style == "mens" and climate == "hot":
        tips.append("During day: Use a sweat-resistant face mist to stay fresh")
    
    return tips[:10]

def get_outfit_rating(outfit_id):
    ratings = load_json_file(RATINGS_FILE, {})
    if outfit_id in ratings:
        total = sum(ratings[outfit_id])
        count = len(ratings[outfit_id])
        return round(total / count, 2) if count > 0 else 0
    return 0

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    profile = data.get('profile', {})
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    
    existing_user = User.find_by_email(email)
    if existing_user:
        return jsonify({'status': 'error', 'message': 'User already exists'}), 400
    
    password_hash = hash_password(password)
    user = User.create(email, password_hash, profile)
    
    token = generate_jwt_token(user['_id'], email)
    
    return jsonify({
        'status': 'success',
        'message': 'User registered successfully',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Login with email and password"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required'}), 400
    
    user = User.find_by_email(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    
    if not verify_password(password, user['password_hash']):
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    
    token = generate_jwt_token(user['_id'], email)
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

@app.route('/auth/magic-link', methods=['POST'])
def request_magic_link():
    """Request a magic link for passwordless login"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email is required'}), 400
    
    user = User.find_by_email(email)
    if not user:
        password_hash = hash_password(secrets.token_urlsafe(32))
        user = User.create(email, password_hash)
    
    token = generate_magic_link_token(email)
    send_magic_link_email(email, token)
    
    return jsonify({
        'status': 'success',
        'message': 'Magic link sent to your email',
        'dev_token': token if not os.getenv('SMTP_USER') else None
    })

@app.route('/auth/verify-magic', methods=['POST'])
def verify_magic():
    """Verify magic link token and log in"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    token = data.get('token', '')
    
    if not token:
        return jsonify({'status': 'error', 'message': 'Token is required'}), 400
    
    email = verify_magic_link_token(token)
    if not email:
        return jsonify({'status': 'error', 'message': 'Invalid or expired token'}), 401
    
    user = User.find_by_email(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    jwt_token = generate_jwt_token(user['_id'], email)
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'token': jwt_token,
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

@app.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user info"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    user = User.find_by_id(request.current_user['user_id'])
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    return jsonify({
        'status': 'success',
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

@app.route('/auth/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update user profile"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    profile = data.get('profile', {})
    
    user = User.update_profile(request.current_user['user_id'], profile)
    
    return jsonify({
        'status': 'success',
        'message': 'Profile updated successfully',
        'user': {
            'id': str(user['_id']),
            'email': user['email'],
            'profile': user['profile']
        }
    })

# ============================================================================
# WARDROBE ENDPOINTS
# ============================================================================

@app.route('/wardrobe/items', methods=['GET'])
@token_required
def get_wardrobe_items():
    """Get all wardrobe items for the current user"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
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

@app.route('/wardrobe/add', methods=['POST'])
@token_required
def add_wardrobe_item():
    """Add an item to the wardrobe"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    
    item = WardrobeItem.create(request.current_user['user_id'], data)
    
    item['_id'] = str(item['_id'])
    item['user_id'] = str(item['user_id'])
    
    return jsonify({
        'status': 'success',
        'message': 'Item added to wardrobe',
        'item': item
    }), 201

@app.route('/wardrobe/mark-owned/<item_id>', methods=['PUT'])
@token_required
def mark_item_owned(item_id):
    """Mark an item as owned or not owned"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    data = request.get_json()
    owned = data.get('owned', True)
    
    WardrobeItem.mark_owned(item_id, owned)
    
    return jsonify({
        'status': 'success',
        'message': f'Item marked as {"owned" if owned else "not owned"}'
    })

@app.route('/wardrobe/remove/<item_id>', methods=['DELETE'])
@token_required
def remove_wardrobe_item(item_id):
    """Remove an item from the wardrobe"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    WardrobeItem.remove_item(item_id, request.current_user['user_id'])
    
    return jsonify({
        'status': 'success',
        'message': 'Item removed from wardrobe'
    })

@app.route('/wardrobe/stats', methods=['GET'])
@token_required
def get_wardrobe_stats():
    """Get wardrobe statistics"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    stats = WardrobeItem.get_wardrobe_stats(request.current_user['user_id'])
    
    return jsonify({
        'status': 'success',
        'stats': stats
    })

# ============================================================================
# INSIGHTS ENDPOINTS
# ============================================================================

@app.route('/insights/gaps', methods=['GET'])
@token_required
def get_wardrobe_gaps():
    """Get wardrobe gap analysis"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
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

@app.route('/insights/balance', methods=['GET'])
@token_required
def get_wardrobe_balance():
    """Get wardrobe balance metrics"""
    if not MONGODB_ENABLED:
        return jsonify({'status': 'error', 'message': 'Database not configured'}), 500
    
    balance = calculate_wardrobe_balance(request.current_user['user_id'])
    
    return jsonify({
        'status': 'success',
        'balance': balance
    })

# ============================================================================
# MAIN PREDICTION ENDPOINT
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "running", 
        "message": "Fashion Recommendation API is active",
        "version": "2.0",
        "total_outfits": len(OUTFIT_DATABASE),
        "features": {
            "guest_mode": True,
            "user_accounts": MONGODB_ENABLED,
            "digital_wardrobe": MONGODB_ENABLED,
            "wardrobe_intelligence": MONGODB_ENABLED
        }
    })

@app.route('/outfits/<outfit_id>/rating', methods=['GET'])
def get_rating(outfit_id):
    """Get rating stats for a specific outfit"""
    if not outfit_exists(outfit_id):
        return jsonify({'status': 'error', 'message': 'Outfit not found'}), 404

    ratings = load_json_file(RATINGS_FILE, {})
    outfit_ratings = ratings.get(outfit_id, [])
    avg_rating = get_outfit_rating(outfit_id)

    return jsonify({
        'status': 'success',
        'outfit_id': outfit_id,
        'average_rating': avg_rating,
        'total_ratings': len(outfit_ratings)
    })

@app.route('/outfits/<outfit_id>/rating', methods=['POST'])
def add_rating(outfit_id):
    """Add a rating (1-5) for a specific outfit"""
    if not outfit_exists(outfit_id):
        return jsonify({'status': 'error', 'message': 'Outfit not found'}), 404

    data = request.get_json(silent=True) or {}
    rating = data.get('rating')

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'status': 'error', 'message': 'Rating must be an integer between 1 and 5'}), 400

    ratings = load_json_file(RATINGS_FILE, {})
    ratings.setdefault(outfit_id, []).append(rating)
    save_json_file(RATINGS_FILE, ratings)

    return jsonify({
        'status': 'success',
        'message': 'Rating submitted',
        'outfit_id': outfit_id,
        'average_rating': get_outfit_rating(outfit_id),
        'total_ratings': len(ratings[outfit_id])
    }), 201

@app.route('/outfits/favorites', methods=['GET'])
def get_favorites():
    """Get favorite outfits for a device_id"""
    device_id = normalize_device_id(request.args.get('device_id', ''))
    if not device_id:
        return jsonify({'status': 'error', 'message': 'device_id query parameter is required'}), 400

    favorites = load_json_file(FAVORITES_FILE, {})
    favorite_ids = favorites.get(device_id, [])
    favorite_outfits = [outfit for outfit in OUTFIT_DATABASE if outfit['id'] in favorite_ids]

    return jsonify({
        'status': 'success',
        'device_id': device_id,
        'favorites': favorite_outfits,
        'count': len(favorite_outfits)
    })

@app.route('/outfits/<outfit_id>/favorite', methods=['POST'])
def add_favorite(outfit_id):
    """Add an outfit to favorites for a device_id"""
    if not outfit_exists(outfit_id):
        return jsonify({'status': 'error', 'message': 'Outfit not found'}), 404

    data = request.get_json(silent=True) or {}
    device_id = normalize_device_id(data.get('device_id', ''))
    if not device_id:
        return jsonify({'status': 'error', 'message': 'device_id is required'}), 400

    favorites = load_json_file(FAVORITES_FILE, {})
    existing_favorites = set(favorites.get(device_id, []))
    existing_favorites.add(outfit_id)
    favorites[device_id] = sorted(existing_favorites)
    save_json_file(FAVORITES_FILE, favorites)

    return jsonify({
        'status': 'success',
        'message': 'Outfit added to favorites',
        'device_id': device_id,
        'favorites': favorites[device_id]
    }), 201

@app.route('/outfits/<outfit_id>/favorite', methods=['DELETE'])
def remove_favorite(outfit_id):
    """Remove an outfit from favorites for a device_id"""
    data = request.get_json(silent=True) or {}
    device_id = normalize_device_id(data.get('device_id', ''))
    if not device_id:
        return jsonify({'status': 'error', 'message': 'device_id is required'}), 400

    favorites = load_json_file(FAVORITES_FILE, {})
    existing_favorites = set(favorites.get(device_id, []))
    if outfit_id in existing_favorites:
        existing_favorites.remove(outfit_id)
    favorites[device_id] = sorted(existing_favorites)
    save_json_file(FAVORITES_FILE, favorites)

    return jsonify({
        'status': 'success',
        'message': 'Outfit removed from favorites',
        'device_id': device_id,
        'favorites': favorites[device_id]
    })

@app.route('/predict', methods=['POST'])
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
    
    if MONGODB_ENABLED and hasattr(request, 'current_user') and request.current_user:
        user = User.find_by_id(request.current_user['user_id'])
        if user and user.get('profile'):
            profile = user['profile']
            body_type = profile.get('body_type', body_type)
            budget = profile.get('budget_preference', budget)
            age_group = profile.get('age_group', age_group)
            skin_tone = profile.get('skin_tone', skin_tone)
            undertone = profile.get('undertone', undertone)
    
    if occasion not in ['casual', 'formal', 'party', 'ethnic']:
        occasion = 'casual'
    if climate not in ['hot', 'moderate', 'cold']:
        climate = 'moderate'
    if clothing_style not in ['mens', 'womens', 'unisex']:
        clothing_style = 'unisex'
    if age_group not in ['young', 'adult', 'senior']:
        age_group = 'young'
    if body_type not in ['slim', 'regular', 'relaxed']:
        body_type = 'regular'
    if budget not in ['low', 'medium', 'high']:
        budget = 'medium'
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    matching_outfits = rank_and_filter_outfits(
        occasion, climate, clothing_style, age_group, body_type, budget, 
        occasion_subtype if occasion_subtype else None
    )
    
    result_outfits = []
    for outfit in matching_outfits:
        outfit_copy = outfit.copy()
        outfit_gender = outfit.get("gender", "unisex")
        outfit_budget = outfit.get("budget", "medium")
        outfit_occasion = outfit.get("occasion", "casual")
        outfit_subtype = occasion_subtype if occasion_subtype in outfit.get("occasion_subtype", []) else None
        
        outfit_copy["shopping_links"] = generate_shopping_links(
            outfit["items"], 
            outfit_gender, 
            outfit_budget, 
            outfit_occasion,
            outfit_subtype
        )
        outfit_copy["average_rating"] = get_outfit_rating(outfit["id"])
        
        if MONGODB_ENABLED and hasattr(request, 'current_user') and request.current_user:
            outfit_copy["in_wardrobe"] = False
        
        result_outfits.append(outfit_copy)
    
    style_tips = generate_care_routines(
        clothing_style, 
        climate, 
        occasion, 
        skin_tone if skin_tone else None,
        undertone if undertone else None,
        detect_face
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
    
    if MONGODB_ENABLED and hasattr(request, 'current_user') and request.current_user:
        response_data["user_context"] = {
            "authenticated": True,
            "has_wardrobe": True
        }
    
    return jsonify(response_data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    if MONGODB_ENABLED:
        try:
            init_db()
        except Exception as e:
            print(f"DEBUG: Error in app.py main: {e}", flush=True)
            
    app.run(debug=True, host='0.0.0.0', port=port)

