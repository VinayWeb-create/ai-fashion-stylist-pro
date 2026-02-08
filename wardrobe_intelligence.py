"""
Wardrobe Intelligence Module - KILLER FEATURE
Analyzes user wardrobe to detect gaps and provide actionable insights
"""
from models import WardrobeItem
from collections import defaultdict

# Essential wardrobe items by category and occasion
WARDROBE_ESSENTIALS = {
    'casual': {
        'tops': ['Basic T-Shirt', 'Casual Shirt', 'Hoodie'],
        'bottoms': ['Jeans', 'Casual Pants'],
        'footwear': ['Sneakers', 'Casual Shoes'],
        'outerwear': ['Light Jacket']
    },
    'formal': {
        'tops': ['Dress Shirt', 'Blazer'],
        'bottoms': ['Dress Pants', 'Formal Trousers'],
        'footwear': ['Formal Shoes', 'Leather Shoes'],
        'outerwear': ['Suit Jacket']
    },
    'party': {
        'tops': ['Party Shirt', 'Cocktail Top'],
        'bottoms': ['Party Pants', 'Dress Pants'],
        'footwear': ['Heels', 'Dress Shoes'],
        'accessories': ['Statement Jewelry', 'Clutch']
    },
    'ethnic': {
        'tops': ['Kurta', 'Traditional Top'],
        'bottoms': ['Churidar', 'Traditional Bottom'],
        'footwear': ['Mojari', 'Traditional Footwear'],
        'accessories': ['Traditional Jewelry']
    }
}

# Color essentials for a balanced wardrobe
ESSENTIAL_COLORS = {
    'neutrals': ['Black', 'White', 'Grey', 'Beige', 'Navy'],
    'accent': ['Red', 'Blue', 'Green']
}

# Season essentials
SEASON_ESSENTIALS = {
    'winter': ['Coat', 'Sweater', 'Boots', 'Scarf'],
    'summer': ['Light Shirt', 'Shorts', 'Sandals'],
    'spring': ['Light Jacket', 'Casual Shirt'],
    'fall': ['Jacket', 'Long Pants']
}

def analyze_wardrobe_gaps(user_id, user_profile):
    """
    Analyze user's wardrobe and detect missing essentials
    Returns prioritized list of gaps with explanations
    """
    # Get user's wardrobe
    wardrobe = WardrobeItem.get_user_wardrobe(user_id)
    owned_items = [item for item in wardrobe if item.get('owned', True)]
    
    # Get wardrobe stats
    stats = WardrobeItem.get_wardrobe_stats(user_id)
    
    gaps = []
    
    # 1. Analyze by occasion
    occasion_gaps = _analyze_occasion_gaps(owned_items, stats, user_profile)
    gaps.extend(occasion_gaps)
    
    # 2. Analyze color balance
    color_gaps = _analyze_color_gaps(owned_items, stats)
    gaps.extend(color_gaps)
    
    # 3. Analyze seasonal coverage
    season_gaps = _analyze_season_gaps(owned_items, stats)
    gaps.extend(season_gaps)
    
    # 4. Analyze category balance
    category_gaps = _analyze_category_gaps(owned_items, stats)
    gaps.extend(category_gaps)
    
    # Calculate outfit potential for each gap
    for gap in gaps:
        gap['outfits_unlocked'] = _calculate_outfit_potential(gap, owned_items)
    
    # Sort by priority and outfit potential
    gaps.sort(key=lambda x: (
        -_priority_score(x['priority']),
        -x['outfits_unlocked']
    ))
    
    return gaps[:10]  # Return top 10 gaps

def _analyze_occasion_gaps(owned_items, stats, user_profile):
    """Detect missing items for key occasions"""
    gaps = []
    lifestyle = user_profile.get('lifestyle', 'mixed')
    
    # Determine which occasions are important based on lifestyle
    important_occasions = []
    if lifestyle in ['student', 'mixed']:
        important_occasions.append('casual')
    if lifestyle in ['office', 'mixed']:
        important_occasions.extend(['formal', 'casual'])
    if lifestyle == 'mixed':
        important_occasions.append('party')
    
    for occasion in important_occasions:
        if occasion not in WARDROBE_ESSENTIALS:
            continue
        
        occasion_items = [item for item in owned_items if occasion in item.get('occasions', [])]
        
        for category, essentials in WARDROBE_ESSENTIALS[occasion].items():
            # Check if user has items in this category for this occasion
            has_category = any(
                item.get('category') == category.rstrip('s')  # Remove plural
                for item in occasion_items
            )
            
            if not has_category:
                gap = {
                    'type': 'occasion_category',
                    'occasion': occasion,
                    'category': category,
                    'item_name': f"{occasion.title()} {category.title().rstrip('s')}",
                    'reason': _generate_occasion_reason(occasion, category, lifestyle),
                    'priority': 'high' if occasion == 'formal' and lifestyle == 'office' else 'medium',
                    'shopping_query': f"{occasion} {category.rstrip('s')}"
                }
                gaps.append(gap)
    
    return gaps

def _analyze_color_gaps(owned_items, stats):
    """Detect missing essential colors"""
    gaps = []
    owned_colors = set(stats.get('colors', []))
    
    # Check for neutral colors
    missing_neutrals = []
    for neutral in ESSENTIAL_COLORS['neutrals']:
        if neutral not in owned_colors:
            missing_neutrals.append(neutral)
    
    if len(missing_neutrals) >= 2:
        gap = {
            'type': 'color_neutral',
            'item_name': f"Neutral Colored Items ({', '.join(missing_neutrals[:2])})",
            'reason': f"You're missing key neutral colors like {', '.join(missing_neutrals[:2])}. Neutrals are wardrobe foundations that match with everything and create endless outfit combinations.",
            'priority': 'high',
            'shopping_query': f"{missing_neutrals[0]} basic top",
            'colors_needed': missing_neutrals
        }
        gaps.append(gap)
    
    return gaps

def _analyze_season_gaps(owned_items, stats):
    """Detect missing seasonal items"""
    gaps = []
    season_coverage = stats.get('by_season', {})
    
    for season, essentials in SEASON_ESSENTIALS.items():
        season_count = season_coverage.get(season, 0)
        
        if season_count < 2:  # Less than 2 items for this season
            gap = {
                'type': 'season',
                'season': season,
                'item_name': f"{season.title()} Essentials",
                'reason': f"Your wardrobe has limited {season} options. Adding {season}-appropriate items ensures you're prepared year-round.",
                'priority': 'medium',
                'shopping_query': f"{season} clothing",
                'suggestions': essentials[:2]
            }
            gaps.append(gap)
    
    return gaps

def _analyze_category_gaps(owned_items, stats):
    """Detect category imbalances"""
    gaps = []
    category_counts = stats.get('by_category', {})
    
    # Essential categories
    essential_categories = ['top', 'bottom', 'footwear']
    
    for category in essential_categories:
        count = category_counts.get(category, 0)
        
        if count == 0:
            gap = {
                'type': 'category_missing',
                'category': category,
                'item_name': f"{category.title()}s",
                'reason': f"You have no {category}s in your wardrobe. This is a fundamental gap that limits your outfit options significantly.",
                'priority': 'high',
                'shopping_query': f"basic {category}"
            }
            gaps.append(gap)
        elif count < 3:
            gap = {
                'type': 'category_low',
                'category': category,
                'item_name': f"More {category.title()}s",
                'reason': f"You only have {count} {category}(s). Adding variety here will multiply your outfit combinations.",
                'priority': 'medium',
                'shopping_query': f"{category} variety"
            }
            gaps.append(gap)
    
    # Check for outerwear
    if category_counts.get('outerwear', 0) == 0:
        gap = {
            'type': 'category_missing',
            'category': 'outerwear',
            'item_name': 'Outerwear',
            'reason': "You're missing outerwear. A good jacket or coat is essential for layering and adapting to different weather conditions.",
            'priority': 'medium',
            'shopping_query': 'jacket outerwear'
        }
        gaps.append(gap)
    
    return gaps

def _calculate_outfit_potential(gap, owned_items):
    """
    Calculate how many new outfit combinations this item would unlock
    Simple heuristic: multiply compatible items across categories
    """
    gap_category = gap.get('category', '').rstrip('s')
    
    if not gap_category:
        return 5  # Default estimate
    
    # Count items in complementary categories
    if gap_category == 'top':
        bottoms = len([i for i in owned_items if i.get('category') == 'bottom'])
        footwear = len([i for i in owned_items if i.get('category') == 'footwear'])
        return max(bottoms * footwear, 5)
    
    elif gap_category == 'bottom':
        tops = len([i for i in owned_items if i.get('category') == 'top'])
        footwear = len([i for i in owned_items if i.get('category') == 'footwear'])
        return max(tops * footwear, 5)
    
    elif gap_category == 'footwear':
        tops = len([i for i in owned_items if i.get('category') == 'top'])
        bottoms = len([i for i in owned_items if i.get('category') == 'bottom'])
        return max(tops * bottoms, 5)
    
    elif gap_category == 'outerwear':
        tops = len([i for i in owned_items if i.get('category') == 'top'])
        return max(tops * 2, 5)
    
    return 5

def _generate_occasion_reason(occasion, category, lifestyle):
    """Generate human-readable reason for occasion gap"""
    reasons = {
        'casual': {
            'tops': "Casual tops are everyday essentials. You'll wear them more than anything else in your wardrobe.",
            'bottoms': "Casual bottoms give you flexibility for daily activities and relaxed settings.",
            'footwear': "Comfortable casual footwear is crucial for daily wear and all-day comfort.",
            'outerwear': "A casual jacket completes your look and adapts to changing weather."
        },
        'formal': {
            'tops': f"{'As an office professional' if lifestyle == 'office' else 'For formal occasions'}, you need proper formal tops to look polished and professional.",
            'bottoms': "Formal bottoms are essential for creating a complete professional appearance.",
            'footwear': "Formal footwear elevates your entire outfit and shows attention to detail.",
            'outerwear': "A formal blazer or jacket is the finishing touch for any professional look."
        },
        'party': {
            'tops': "Party tops help you stand out and feel confident at social events.",
            'bottoms': "The right party bottoms make you feel special for celebrations and nights out.",
            'footwear': "Statement footwear completes your party look and boosts confidence.",
            'accessories': "Accessories transform an outfit from ordinary to extraordinary for special occasions."
        },
        'ethnic': {
            'tops': "Traditional tops connect you to cultural celebrations and formal ethnic events.",
            'bottoms': "Complete ethnic outfits require proper traditional bottoms.",
            'footwear': "Traditional footwear completes your ethnic look authentically.",
            'accessories': "Traditional accessories add the perfect finishing touch to ethnic wear."
        }
    }
    
    return reasons.get(occasion, {}).get(category, f"This {category} is important for {occasion} occasions.")

def _priority_score(priority):
    """Convert priority to numeric score"""
    scores = {'high': 3, 'medium': 2, 'low': 1}
    return scores.get(priority, 1)

def calculate_wardrobe_balance(user_id):
    """
    Calculate wardrobe balance metrics
    Returns readiness scores for different occasions
    """
    stats = WardrobeItem.get_wardrobe_stats(user_id)
    
    balance = {
        'overall_score': 0,
        'occasion_readiness': {},
        'category_balance': {},
        'season_coverage': {},
        'color_diversity': 0
    }
    
    # Occasion readiness (0-100 score)
    occasion_scores = stats.get('by_occasion', {})
    for occasion in ['casual', 'formal', 'party', 'ethnic']:
        count = occasion_scores.get(occasion, 0)
        # Score based on item count (3+ items = 100%, 0 items = 0%)
        score = min(100, (count / 3) * 100)
        balance['occasion_readiness'][occasion] = round(score)
    
    # Category balance
    category_counts = stats.get('by_category', {})
    total_items = stats.get('total_items', 0)
    
    for category in ['top', 'bottom', 'footwear', 'outerwear', 'accessory']:
        count = category_counts.get(category, 0)
        percentage = (count / total_items * 100) if total_items > 0 else 0
        balance['category_balance'][category] = {
            'count': count,
            'percentage': round(percentage, 1)
        }
    
    # Season coverage
    season_scores = stats.get('by_season', {})
    for season in ['spring', 'summer', 'fall', 'winter']:
        count = season_scores.get(season, 0)
        score = min(100, (count / 3) * 100)
        balance['season_coverage'][season] = round(score)
    
    # Color diversity (number of unique colors)
    color_count = len(stats.get('colors', []))
    balance['color_diversity'] = min(100, (color_count / 8) * 100)  # 8+ colors = 100%
    
    # Overall score (average of all metrics)
    all_scores = (
        list(balance['occasion_readiness'].values()) +
        list(balance['season_coverage'].values()) +
        [balance['color_diversity']]
    )
    balance['overall_score'] = round(sum(all_scores) / len(all_scores)) if all_scores else 0
    
    return balance
