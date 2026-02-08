from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

OUTFIT_DATABASE = [
    {
        "name": "Classic Casual Denim",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age": ["young", "adult"],
        "items": ["Blue Denim Jeans", "White Cotton T-Shirt", "Casual Sneakers"],
        "colors": ["Blue", "White"],
        "accessories": ["Sunglasses", "Wristwatch"],
        "footwear": "Casual Sneakers"
    },
    {
        "name": "Summer Casual Shorts",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["hot"],
        "age": ["young"],
        "items": ["Khaki Shorts", "Polo Shirt", "Canvas Shoes"],
        "colors": ["Khaki", "Navy Blue"],
        "accessories": ["Cap", "Backpack"],
        "footwear": "Canvas Shoes"
    },
    {
        "name": "Business Formal Suit",
        "gender": "mens",
        "occasion": "formal",
        "climate": ["moderate", "cold"],
        "age": ["adult", "senior"],
        "items": ["Navy Blue Suit", "White Dress Shirt", "Black Leather Shoes", "Silk Tie"],
        "colors": ["Navy Blue", "White", "Black"],
        "accessories": ["Leather Belt", "Cufflinks", "Wristwatch"],
        "footwear": "Black Leather Shoes"
    },
    {
        "name": "Smart Casual Blazer",
        "gender": "mens",
        "occasion": "formal",
        "climate": ["moderate"],
        "age": ["young", "adult"],
        "items": ["Grey Blazer", "Chinos", "Oxford Shoes", "Dress Shirt"],
        "colors": ["Grey", "Beige", "Brown"],
        "accessories": ["Leather Watch", "Pocket Square"],
        "footwear": "Oxford Shoes"
    },
    {
        "name": "Winter Casual Layers",
        "gender": "mens",
        "occasion": "casual",
        "climate": ["cold"],
        "age": ["young", "adult"],
        "items": ["Hoodie", "Jeans", "Winter Jacket", "Boots"],
        "colors": ["Black", "Grey", "Brown"],
        "accessories": ["Beanie", "Scarf"],
        "footwear": "Boots"
    },
    {
        "name": "Casual Floral Dress",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age": ["young", "adult"],
        "items": ["Floral Midi Dress", "Sandals", "Denim Jacket"],
        "colors": ["Floral Print", "Blue"],
        "accessories": ["Sunglasses", "Crossbody Bag"],
        "footwear": "Sandals"
    },
    {
        "name": "Summer Breezy Outfit",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["hot"],
        "age": ["young"],
        "items": ["White Linen Top", "High Waisted Shorts", "Espadrilles"],
        "colors": ["White", "Denim Blue"],
        "accessories": ["Straw Hat", "Tote Bag"],
        "footwear": "Espadrilles"
    },
    {
        "name": "Elegant Evening Gown",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["moderate", "cold"],
        "age": ["adult", "senior"],
        "items": ["Black Evening Gown", "Heels", "Clutch"],
        "colors": ["Black"],
        "accessories": ["Pearl Necklace", "Bracelet", "Earrings"],
        "footwear": "Heels"
    },
    {
        "name": "Professional Pantsuit",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["moderate"],
        "age": ["young", "adult"],
        "items": ["Blazer", "Dress Pants", "Blouse", "Pumps"],
        "colors": ["Navy", "White"],
        "accessories": ["Statement Watch", "Tote Bag"],
        "footwear": "Pumps"
    },
    {
        "name": "Cozy Winter Layers",
        "gender": "womens",
        "occasion": "casual",
        "climate": ["cold"],
        "age": ["young", "adult"],
        "items": ["Sweater", "Jeans", "Coat", "Ankle Boots"],
        "colors": ["Burgundy", "Black", "Camel"],
        "accessories": ["Scarf", "Gloves"],
        "footwear": "Ankle Boots"
    },
    {
        "name": "Cocktail Party Dress",
        "gender": "womens",
        "occasion": "formal",
        "climate": ["hot", "moderate"],
        "age": ["young", "adult"],
        "items": ["Cocktail Dress", "Strappy Heels", "Clutch"],
        "colors": ["Red", "Gold"],
        "accessories": ["Drop Earrings", "Bracelet"],
        "footwear": "Strappy Heels"
    },
    {
        "name": "Basic Unisex Casual",
        "gender": "unisex",
        "occasion": "casual",
        "climate": ["hot", "moderate"],
        "age": ["young", "adult"],
        "items": ["Plain T-Shirt", "Jeans", "Sneakers"],
        "colors": ["Black", "Blue"],
        "accessories": ["Backpack"],
        "footwear": "Sneakers"
    },
    {
        "name": "Athleisure Comfort",
        "gender": "unisex",
        "occasion": "casual",
        "climate": ["hot", "moderate", "cold"],
        "age": ["young", "adult"],
        "items": ["Joggers", "Hoodie", "Running Shoes"],
        "colors": ["Grey", "Black"],
        "accessories": ["Sports Watch", "Gym Bag"],
        "footwear": "Running Shoes"
    },
    {
        "name": "Smart Casual Neutrals",
        "gender": "unisex",
        "occasion": "formal",
        "climate": ["moderate"],
        "age": ["adult"],
        "items": ["Blazer", "Trousers", "Loafers", "Button Up Shirt"],
        "colors": ["Beige", "White", "Brown"],
        "accessories": ["Leather Belt", "Watch"],
        "footwear": "Loafers"
    }
]

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

def filter_outfits(occasion, climate, clothing_style, age_group):
    filtered = []
    
    for outfit in OUTFIT_DATABASE:
        if outfit["occasion"] != occasion:
            continue
        
        if climate not in outfit["climate"]:
            continue
        
        if age_group not in outfit["age"]:
            continue
        
        if clothing_style == "mens" and outfit["gender"] == "womens":
            continue
        
        if clothing_style == "womens" and outfit["gender"] == "mens":
            continue
        
        if clothing_style in ["mens", "womens"] and outfit["gender"] not in [clothing_style, "unisex"]:
            continue
        
        filtered.append(outfit)
    
    return filtered[:3]

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "running",
        "message": "Fashion Recommendation API is active"
    })

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
    
    matching_outfits = filter_outfits(occasion, climate, clothing_style, age_group)
    
    result_outfits = []
    for outfit in matching_outfits:
        outfit_copy = outfit.copy()
        outfit_copy["shopping_links"] = generate_shopping_links(outfit["items"])
        result_outfits.append(outfit_copy)
    
    return jsonify({
        "status": "success",
        "prediction": {
            "confidence": 0.95,
            "outfits": result_outfits
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
