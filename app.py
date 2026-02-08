from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from urllib.parse import quote_plus
import json
from datetime import datetime
import secrets
import logging
import traceback
import sys
from models import connect_to_mongodb, init_db

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("STARTING FASHION STYLIST API v2.3")
logger.info("=" * 80)

# ============================================================================
# IMPORT MODULES
# ============================================================================

MONGODB_ENABLED = False

try:
    logger.info("📦 Importing auth module...")
    from auth import (
        hash_password, verify_password, generate_jwt_token, 
        verify_jwt_token, generate_magic_link_token, verify_magic_link_token,
        send_magic_link_email, token_required, optional_token
    )
    logger.info("✅ Auth module imported")
except Exception as e:
    logger.error(f"❌ Auth import failed: {e}")
    sys.exit(1)

try:
    logger.info("📦 Importing models module...")
    from models import User, WardrobeItem, WardrobeInsights, init_db
    logger.info("✅ Models module imported")
    MONGODB_ENABLED = True
except Exception as e:
    logger.error(f"❌ Models import failed: {e}")
    MONGODB_ENABLED = False

try:
    logger.info("📦 Importing wardrobe_intelligence module...")
    from wardrobe_intelligence import analyze_wardrobe_gaps, calculate_wardrobe_balance
    logger.info("✅ Wardrobe intelligence module imported")
except Exception as e:
    logger.error(f"❌ Wardrobe intelligence import failed: {e}")

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

logger.info(f"✅ Flask app created")
logger.info(f"✅ MongoDB enabled: {MONGODB_ENABLED}")

# ============================================================================
# FILE MANAGEMENT
# ============================================================================

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
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading {filepath}: {e}")
    return default

def save_json_file(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {filepath}: {e}")

# ============================================================================
# OUTFIT DATABASE (20 SAMPLE OUTFITS)
# ============================================================================

OUTFIT_DATABASE = [
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
        "reasoning": "This outfit combines comfort with style, ideal for relaxed settings",
        "average_rating": 4.5
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
        "reasoning": "Lightweight and breathable materials keep you cool in the heat",
        "average_rating": 4.3
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
        "reasoning": "Professional appearance with timeless sophistication",
        "average_rating": 4.7
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
        "reasoning": "Balances professionalism with approachability",
        "average_rating": 4.4
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
        "reasoning": "Multiple layers provide warmth without sacrificing style",
        "average_rating": 4.6
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
        "reasoning": "Floral patterns add a fresh, cheerful touch",
        "average_rating": 4.5
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
        "reasoning": "Natural fabrics keep you cool and comfortable",
        "average_rating": 4.2
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
        "reasoning": "Timeless black creates a stunning formal appearance",
        "average_rating": 4.8
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
        "reasoning": "Sharp tailoring conveys confidence and competence",
        "average_rating": 4.6
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
        "reasoning": "Rich colors and textures create a cozy aesthetic",
        "average_rating": 4.5
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
        "reasoning": "Bold colors make a memorable statement",
        "average_rating": 4.4
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
        "reasoning": "Minimalist approach works for any casual setting",
        "average_rating": 4.0
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
        "reasoning": "Performance fabrics provide all-day comfort",
        "average_rating": 4.3
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
        "reasoning": "Neutral tones create sophisticated versatility",
        "average_rating": 4.5
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
        "reasoning": "Modern street fashion with attitude",
        "average_rating": 4.2
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
        "reasoning": "Timeless preppy aesthetic with modern touch",
        "average_rating": 4.3
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
        "reasoning": "Free-spirited and effortlessly stylish",
        "average_rating": 4.4
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
        "reasoning": "Sophisticated simplicity makes a statement",
        "average_rating": 4.6
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
        "reasoning": "Timeless elegance for cultural celebrations",
        "average_rating": 4.7
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
        "reasoning": "Perfect blend of tradition and contemporary style",
        "average_rating": 4.5
    }
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_current_season():
    """Get current season"""
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
    """Generate shopping links for items"""
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
    """Calculate outfit match score"""
    score = 0
    
    if outfit["gender"] == clothing_style:
        score += 100
    elif outfit["gender"] == "unisex":
        score += 50
    else:
        return 0
    
    if outfit["occasion"] == occasion:
        score += 50
    
    if occasion_subtype and occasion_subtype in outfit.get("occasion_subtype", []):
        score += 30
    
    if climate in outfit["climate"]:
        score += 20
    
    if body_type in outfit.get("body_type", []):
        score += 15
    
    if outfit["budget"] == budget:
        score += 10
    
    return score

def rank_and_filter_outfits(occasion, climate, clothing_style, age_group, body_type, budget, occasion_subtype=None):
    """Rank and filter outfits based on criteria"""
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
    """Generate style tips and care routines"""
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
        tips.append(f"Your {skin_tone} skin tone looks great with warm/cool colors")
    
    tips.append("Maintain good personal hygiene for confidence in any setting")
    
    return tips[:10]

# ============================================================================
# HEALTH & DEBUG ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_status = "connected" if MONGODB_ENABLED else "disabled"
        return jsonify({
            'status': 'ok',
            'message': 'Server is running',
            'database': db_status,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.before_first_request
def startup_db():
    app.logger.info("🔌 Connecting to MongoDB...")
    connected = connect_to_mongodb()

    if connected:
        init_db()
        app.logger.info("✅ MongoDB connected and initialized")
    else:
        app.logger.error("❌ MongoDB connection failed")



# ============================================================================
# FIXED REGISTRATION ENDPOINT
# ============================================================================

@app.route('/auth/register', methods=['POST', 'OPTIONS'])
def register():
    """Register a new user"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("=" * 80)
        logger.info("REGISTER REQUEST")
        logger.info("=" * 80)
        
        # Step 1: Check if request is JSON
        if not request.is_json:
            logger.error(f"Not JSON. Content-Type: {request.content_type}")
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }), 400
        
        # Step 2: Get request data
        data = request.get_json()
        if not data:
            logger.error("Empty request body")
            return jsonify({
                'status': 'error',
                'message': 'Empty request body'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        profile = data.get('profile', {})
        
        logger.info(f"Email: {email}")
        logger.info(f"Has password: {bool(password)}")
        
        # Step 3: Validate input
        if not email or '@' not in email:
            logger.warning(f"Invalid email: {email}")
            return jsonify({
                'status': 'error',
                'message': 'Valid email is required'
            }), 400
        
        if not password or len(password) < 6:
            logger.warning(f"Invalid password (len: {len(password)})")
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 6 characters'
            }), 400
        
        # Step 4: Check MongoDB is enabled
        if not MONGODB_ENABLED:
            logger.error("MongoDB is not enabled!")
            return jsonify({
                'status': 'error',
                'message': 'Database not configured. User accounts unavailable.'
            }), 503
        
        # Step 5: Check if user exists
        logger.info(f"Checking if user exists...")
        try:
            existing_user = User.find_by_email(email)
            if existing_user:
                logger.warning(f"User already exists: {email}")
                return jsonify({
                    'status': 'error',
                    'message': 'Email already registered'
                }), 400
            logger.info("User does not exist - proceeding with registration")
        except Exception as e:
            logger.error(f"Database error checking user: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }), 503
        
        # Step 6: Hash password
        logger.info("Hashing password...")
        try:
            password_hash = hash_password(password)
            logger.info("Password hashed successfully")
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Password processing failed'
            }), 500
        
        # Step 7: Create user in database
        logger.info("Creating user in database...")
        try:
            user = User.create(email, password_hash, profile)
            logger.info(f"User created successfully. ID: {user.get('_id')}")
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'User creation failed: {str(e)}'
            }), 503
        
        # Step 8: Generate JWT token
        logger.info("Generating JWT token...")
        try:
            token = generate_jwt_token(str(user['_id']), email)
            logger.info("JWT token generated")
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Token generation failed'
            }), 500
        
        # Step 9: Return success response
        logger.info("✅ REGISTRATION SUCCESSFUL")
        logger.info("=" * 80)
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'profile': user.get('profile', {})
            }
        }), 201
    
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        logger.error(f"Type: {type(e).__name__}")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        return jsonify({
            'status': 'error',
            'message': 'Server error during registration'
        }), 500


@app.route('/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Login with email and password"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        logger.info("=" * 80)
        logger.info("LOGIN REQUEST")
        logger.info("=" * 80)
        
        if not request.is_json:
            logger.error(f"Not JSON. Content-Type: {request.content_type}")
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        logger.info(f"Login attempt: {email}")
        
        if not email or not password:
            logger.warning("Missing email or password")
            return jsonify({
                'status': 'error',
                'message': 'Email and password required'
            }), 400
        
        if not MONGODB_ENABLED:
            logger.error("MongoDB is not enabled")
            return jsonify({
                'status': 'error',
                'message': 'Database not configured'
            }), 503
        
        # Find user
        logger.info(f"Finding user: {email}")
        try:
            user = User.find_by_email(email)
            if not user:
                logger.warning(f"User not found: {email}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            logger.info("User found")
        except Exception as e:
            logger.error(f"Database error finding user: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'status': 'error',
                'message': f'Database error: {str(e)}'
            }), 503
        
        # Verify password
        logger.info("Verifying password...")
        try:
            if not verify_password(password, user.get('password_hash')):
                logger.warning(f"Invalid password for: {email}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }), 401
            logger.info("Password verified")
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Password verification failed'
            }), 500
        
        # Generate token
        logger.info("Generating token...")
        try:
            token = generate_jwt_token(str(user['_id']), email)
            logger.info("Token generated")
        except Exception as e:
            logger.error(f"Token generation error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Token generation failed'
            }), 500
        
        logger.info("✅ LOGIN SUCCESSFUL")
        logger.info("=" * 80)
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'profile': user.get('profile', {})
            }
        }), 200
    
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ UNEXPECTED ERROR: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error("=" * 80)
        
        return jsonify({
            'status': 'error',
            'message': 'Server error during login'
        }), 500

@app.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current user"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Database not configured'}), 503
        
        user = User.find_by_id(request.current_user['user_id'])
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'profile': user.get('profile', {})
            }
        }), 200
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'status': 'error', 'message': 'Server error'}), 500

@app.route('/auth/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update profile"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Database not configured'}), 503
        
        data = request.get_json()
        profile = data.get('profile', {})
        
        user = User.update_profile(request.current_user['user_id'], profile)
        
        return jsonify({
            'status': 'success',
            'message': 'Profile updated',
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'profile': user.get('profile', {})
            }
        }), 200
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update profile'}), 500

# ============================================================================
# WARDROBE ENDPOINTS
# ============================================================================

@app.route('/wardrobe/items', methods=['GET'])
@token_required
def get_wardrobe_items():
    """Get wardrobe items"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Feature unavailable'}), 503
        
        category = request.args.get('category')
        owned = request.args.get('owned')
        
        filters = {}
        if category:
            filters['category'] = category
        if owned:
            filters['owned'] = owned.lower() == 'true'
        
        items = WardrobeItem.get_user_wardrobe(request.current_user['user_id'], filters)
        
        for item in items:
            item['_id'] = str(item['_id'])
            item['user_id'] = str(item['user_id'])
        
        return jsonify({
            'status': 'success',
            'items': items,
            'count': len(items)
        }), 200
    except Exception as e:
        logger.error(f"Get wardrobe error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed'}), 500

@app.route('/wardrobe/add', methods=['POST'])
@token_required
def add_wardrobe_item():
    """Add wardrobe item"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Feature unavailable'}), 503
        
        data = request.get_json()
        item = WardrobeItem.create(request.current_user['user_id'], data)
        
        item['_id'] = str(item['_id'])
        item['user_id'] = str(item['user_id'])
        
        return jsonify({
            'status': 'success',
            'message': 'Item added',
            'item': item
        }), 201
    except Exception as e:
        logger.error(f"Add item error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed'}), 500

@app.route('/wardrobe/remove/<item_id>', methods=['DELETE'])
@token_required
def remove_wardrobe_item(item_id):
    """Remove item"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Feature unavailable'}), 503
        
        WardrobeItem.remove_item(item_id, request.current_user['user_id'])
        
        return jsonify({
            'status': 'success',
            'message': 'Item removed'
        }), 200
    except Exception as e:
        logger.error(f"Remove error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed'}), 500

@app.route('/wardrobe/stats', methods=['GET'])
@token_required
def get_wardrobe_stats():
    """Get stats"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Feature unavailable'}), 503
        
        stats = WardrobeItem.get_wardrobe_stats(request.current_user['user_id'])
        return jsonify({'status': 'success', 'stats': stats}), 200
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed'}), 500

# ============================================================================
# INSIGHTS ENDPOINTS
# ============================================================================

@app.route('/insights/gaps', methods=['GET'])
@token_required
def get_wardrobe_gaps():
    """Get gaps"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Feature unavailable'}), 503
        
        user = User.find_by_id(request.current_user['user_id'])
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        gaps = analyze_wardrobe_gaps(request.current_user['user_id'], user.get('profile', {}))
        
        for gap in gaps:
            query = gap.get('shopping_query', gap.get('item_name', ''))
            encoded = quote_plus(query)
            gap['shopping_links'] = {
                'amazon': f"https://www.amazon.in/s?k={encoded}",
                'flipkart': f"https://www.flipkart.com/search?q={encoded}",
                'meesho': f"https://www.meesho.com/search?q={encoded}"
            }
        
        return jsonify({'status': 'success', 'gaps': gaps, 'count': len(gaps)}), 200
    except Exception as e:
        logger.error(f"Gaps error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed'}), 500

@app.route('/insights/balance', methods=['GET'])
@token_required
def get_wardrobe_balance():
    """Get balance"""
    try:
        if not MONGODB_ENABLED:
            return jsonify({'status': 'error', 'message': 'Feature unavailable'}), 503
        
        balance = calculate_wardrobe_balance(request.current_user['user_id'])
        return jsonify({'status': 'success', 'balance': balance}), 200
    except Exception as e:
        logger.error(f"Balance error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed'}), 500

# ============================================================================
# PREDICTION ENDPOINT
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """API info"""
    return jsonify({
        "status": "running",
        "message": "AI Fashion Stylist API v2.3",
        "mongodb": MONGODB_ENABLED
    }), 200

@app.route('/predict', methods=['POST'])
def predict():
    """Get predictions"""
    try:
        if 'image' not in request.files:
            return jsonify({"status": "error", "message": "No image"}), 400

        file = request.files['image']
        if not file.filename:
            return jsonify({"status": "error", "message": "No file"}), 400

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid type"}), 400

        occasion = request.form.get('occasion', 'casual')
        climate = request.form.get('climate', 'moderate')
        clothing_style = request.form.get('clothing_style', 'unisex')
        age_group = request.form.get('age_group', 'young')
        body_type = request.form.get('body_type', 'regular')
        budget = request.form.get('budget', 'medium')

        matching = rank_and_filter_outfits(
            occasion, climate, clothing_style, age_group, body_type, budget
        )

        result_outfits = []
        for outfit in matching:
            outfit_copy = outfit.copy()
            outfit_copy["shopping_links"] = generate_shopping_links(
                outfit["items"],
                outfit.get("gender", "unisex"),
                outfit.get("budget", "medium"),
                outfit.get("occasion", "casual")
            )
            result_outfits.append(outfit_copy)

        tips = generate_care_routines(clothing_style, climate, occasion)

        return jsonify({
            "status": "success",
            "prediction": {
                "confidence": 0.95,
                "clothing_type": "Uploaded Garment",
                "outfits": result_outfits,
                "style_tips": tips
            }
        }), 200

    except Exception as e:
        logger.error(f"Predict error: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": "Failed"}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500: {error}\n{traceback.format_exc()}")
    return jsonify({'status': 'error', 'message': 'Server error'}), 500

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    logger.info("=" * 80)
    logger.info(f"Starting API on port {port}")
    logger.info(f"MongoDB: {'ENABLED' if MONGODB_ENABLED else 'DISABLED'}")
    logger.info("=" * 80)
    
    if MONGODB_ENABLED:
        try:
            init_db()
            logger.info("✅ Database ready")
        except Exception as e:
            logger.warning(f"⚠️ DB init: {e}")
    
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)




