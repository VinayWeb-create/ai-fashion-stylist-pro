import os
import json
from datetime import datetime
from urllib.parse import quote_plus

# Base directory for data files
DATA_FOLDER = 'data'
OUTFITS_FILE = os.path.join(DATA_FOLDER, 'outfits.json')
TIPS_FILE = os.path.join(DATA_FOLDER, 'fashion_tips.json')
RATINGS_FILE = os.path.join(DATA_FOLDER, 'ratings.json')

def load_json_file(filepath, default=None):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return default if default is not None else {}
    return default if default is not None else {}

# Singleton-like access to database (or reload if needed)
def get_outfit_database():
    return load_json_file(OUTFITS_FILE, [])

def get_fashion_tips_map():
    return load_json_file(TIPS_FILE, {})

def get_current_season():
    month = datetime.now().month
    if month in [12, 1, 2]: return "winter"
    elif month in [3, 4, 5]: return "spring"
    elif month in [6, 7, 8]: return "summer"
    else: return "fall"

def generate_shopping_links(items, gender="unisex", budget="medium", occasion="casual", occasion_subtype=None):
    links = []
    budget_hints = {"low": "under 1000", "medium": "under 2500", "high": "premium"}
    occasion_contexts = {
        "casual": {"college": "college", "daily": "daily wear", "travel": "travel"},
        "formal": {"office": "office", "meeting": "formal", "interview": "interview"},
        "party": {"night": "party", "wedding": "party wear", "festival": "festive"},
        "ethnic": {"traditional": "traditional", "festive": "festive"}
    }
    
    for item in items:
        gender_prefix = "women " if gender == "womens" else "men " if gender == "mens" else ""
        budget_hint = budget_hints.get(budget, "")
        occasion_context = occasion_contexts.get(occasion, {}).get(occasion_subtype, "") if occasion_subtype else ""
        
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
    
    # Medium Priority: Body Type
    if body_type in outfit.get("body_type", []):
        score += 60
    
    # Medium Priority: Budget
    if outfit["budget"] == budget:
        score += 40
    elif (budget == "medium" and outfit["budget"] == "low") or budget == "high":
        score += 20
    
    return score

def rank_and_filter_outfits(occasion, climate, clothing_style, age_group, body_type, budget, occasion_subtype=None):
    outfits = get_outfit_database()
    scored_outfits = []
    
    for outfit in outfits:
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
    fashion_tips_map = get_fashion_tips_map()
    
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
        val = ratings[outfit_id]
        if isinstance(val, list) and val:
            return round(sum(val) / len(val), 2)
    return 0
