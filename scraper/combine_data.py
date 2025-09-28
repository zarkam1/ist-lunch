"""Combine all existing scraped data into a comprehensive dataset"""

import json
import os
from datetime import datetime

def load_json(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def combine_all_data():
    """Combine all existing scraped data"""
    
    print("🔄 Combining all existing scraped data...")
    
    combined_dishes = []
    restaurant_stats = {}
    
    # Load all data sources
    data_sources = [
        ("lunch_dishes.json", "Traditional scraping"),
        ("screenshot_results.json", "Screenshot scraping"),
        ("bonab_enhanced.json", "Enhanced Persian dishes"),
        ("all_menus.json", "Latest unified scraping"),
        ("smart_extraction_results.json", "Smart extraction"),
        ("fixed_extraction_results.json", "Fixed extraction with descriptions")
    ]
    
    for filename, source_name in data_sources:
        filepath = f"data/{filename}"
        if not os.path.exists(filepath):
            continue
            
        print(f"📂 Processing {filename} ({source_name})...")
        data = load_json(filepath)
        
        if filename == "lunch_dishes.json":
            # Extract dishes from lunch_dishes format
            dishes = data.get("dishes", [])
            for dish in dishes:
                dish["source"] = source_name
                combined_dishes.append(dish)
            print(f"   Added {len(dishes)} dishes")
            
        elif filename == "screenshot_results.json":
            # Extract from screenshot results format
            if isinstance(data, list):
                for restaurant_data in data:
                    restaurant = restaurant_data.get("restaurant", "Unknown")
                    items = restaurant_data.get("items", [])
                    for item in items:
                        item["restaurant"] = restaurant
                        item["source"] = source_name
                        combined_dishes.append(item)
                    print(f"   Added {len(items)} dishes from {restaurant}")
                    
        elif filename == "bonab_enhanced.json":
            # Extract from Bonab enhanced format
            restaurant = data.get("restaurant", "Bonab")
            items = data.get("items", [])
            for item in items:
                item["restaurant"] = restaurant
                item["source"] = source_name
                combined_dishes.append(item)
            print(f"   Added {len(items)} dishes from {restaurant}")
            
        elif filename == "all_menus.json":
            # Extract from unified scraper format
            for rest_id, menu_data in data.items():
                restaurant = menu_data.get("restaurant", rest_id)
                items = menu_data.get("items", [])
                method = menu_data.get("method", "unknown")
                for item in items:
                    item["restaurant"] = restaurant
                    item["source"] = f"{source_name} ({method})"
                    combined_dishes.append(item)
                print(f"   Added {len(items)} dishes from {restaurant}")
        
        elif filename == "smart_extraction_results.json":
            # Extract from smart extraction format
            restaurants = data.get("restaurants", [])
            for restaurant_data in restaurants:
                if isinstance(restaurant_data, dict):
                    restaurant = restaurant_data.get("restaurant", "Unknown")
                    items = restaurant_data.get("items", [])
                    for item in items:
                        if isinstance(item, dict):
                            item["restaurant"] = restaurant  
                            item["source"] = source_name
                            combined_dishes.append(item)
                    if items:
                        print(f"   Added {len(items)} dishes from {restaurant}")
                        
        elif filename == "fixed_extraction_results.json":
            # Extract from fixed extraction format (list of restaurants)
            if isinstance(data, list):
                for restaurant_data in data:
                    restaurant = restaurant_data.get("restaurant", "Unknown")
                    items = restaurant_data.get("items", [])
                    for item in items:
                        item["restaurant"] = restaurant
                        item["source"] = source_name
                        combined_dishes.append(item)
                    print(f"   Added {len(items)} dishes from {restaurant}")
    
    # Remove duplicates based on name + restaurant
    print(f"\n🔍 Removing duplicates...")
    seen = set()
    unique_dishes = []
    
    for dish in combined_dishes:
        key = f"{dish.get('name', '')}-{dish.get('restaurant', '')}"
        if key not in seen:
            seen.add(key)
            unique_dishes.append(dish)
    
    print(f"   Before: {len(combined_dishes)} dishes")
    print(f"   After: {len(unique_dishes)} dishes")
    
    # Count by restaurant
    for dish in unique_dishes:
        restaurant = dish.get("restaurant", "Unknown")
        if restaurant not in restaurant_stats:
            restaurant_stats[restaurant] = 0
        restaurant_stats[restaurant] += 1
    
    # Create final dataset
    final_data = {
        "generated_at": datetime.now().isoformat(),
        "total_dishes": len(unique_dishes),
        "total_restaurants": len(restaurant_stats),
        "source": "Combined from all scraping efforts",
        "restaurant_counts": restaurant_stats,
        "dishes": unique_dishes
    }
    
    # Save combined data
    with open("data/combined_lunch_data.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    # Create simple dishes list for frontend
    simple_dishes = []
    for dish in unique_dishes:
        simple_dish = {
            "name": dish.get("name", ""),
            "description": dish.get("description", ""),
            "price": dish.get("price", 0),
            "category": dish.get("category", ""),
            "restaurant": dish.get("restaurant", "")
        }
        # Only include if has required fields
        if simple_dish["name"] and simple_dish["restaurant"]:
            simple_dishes.append(simple_dish)
    
    with open("data/frontend_lunch_dishes.json", "w", encoding="utf-8") as f:
        json.dump(simple_dishes, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 COMBINED DATA SUMMARY")
    print("=" * 60)
    print(f"✅ Total unique dishes: {len(unique_dishes)}")
    print(f"🏪 Total restaurants: {len(restaurant_stats)}")
    print(f"📁 Saved to:")
    print(f"   - data/combined_lunch_data.json (full data)")
    print(f"   - data/frontend_lunch_dishes.json (for frontend)")
    
    print(f"\n📈 Restaurants with most dishes:")
    sorted_restaurants = sorted(restaurant_stats.items(), key=lambda x: x[1], reverse=True)
    for restaurant, count in sorted_restaurants[:10]:
        print(f"   {restaurant:30} {count:3} dishes")

if __name__ == "__main__":
    combine_all_data()