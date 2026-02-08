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
    occasion_subtype = request.form.get('occasion_subtype', '')
    climate = request.form.get('climate', 'moderate')
    clothing_style = request.form.get('clothing_style', 'unisex')
    age_group = request.form.get('age_group', 'young')
    body_type = request.form.get('body_type', 'regular')
    budget = request.form.get('budget', 'medium')
    detect_face = request.form.get('detect_face', 'false').lower() == 'true'
    skin_tone = request.form.get('skin_tone', '')
    undertone = request.form.get('undertone', '')
    
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
        result_outfits.append(outfit_copy)
    
    style_tips = generate_care_routines(
        clothing_style, 
        climate, 
        occasion, 
        skin_tone if skin_tone else None,
        undertone if undertone else None,
        detect_face
    )
    
    return jsonify({
        "status": "success",
        "prediction": {
            "confidence": 0.95,
            "clothing_type": "Uploaded Garment",
            "outfits": result_outfits,
            "style_tips": style_tips
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
