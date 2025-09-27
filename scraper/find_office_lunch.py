import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
lat, lon = 59.3615, 17.9713  # Sundbyberg centrum

def is_valid_lunch_spot(place, details):
    """Filter for proper lunch restaurants and cafés"""
    
    name = place["name"].lower()
    types = place.get("types", [])
    
    # EXCLUDE these
    exclude_keywords = ["hotel", "hotell", "okq8", "circle k", "pressbyrån", 
                       "7-eleven", "gym", "sporthall"]
    if any(kw in name for kw in exclude_keywords):
        return False
    
    # INCLUDE these
    include_types = ["restaurant", "cafe", "bakery", "meal_takeaway"]
    include_keywords = ["restaurang", "café", "cafe", "thelins", "espresso house", 
                       "waynes", "lunch", "kök", "kitchen", "sushi", "thai",
                       "italiensk", "pizza", "kebab", "asian"]
    
    # Check if it's a valid type
    if any(t in types for t in include_types):
        return True
    
    # Check name for lunch-related keywords
    if any(kw in name for kw in include_keywords):
        return True
    
    # Check if it has a website and good ratings (likely a real restaurant)
    if details.get("website") and place.get("rating", 0) >= 3.5:
        return True
    
    return False

def find_lunch_restaurants():
    """Find proper lunch restaurants for office workers"""
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    all_restaurants = []
    
    # Search terms for different cuisines
    search_terms = [
        "restaurang lunch",
        "café lunch", 
        "sushi",
        "thai restaurang",
        "italiensk restaurang",
        "salad bar",
        "dagens lunch"
    ]
    
    seen_ids = set()
    
    for search_term in search_terms:
        params = {
            "location": f"{lat},{lon}",
            "radius": 1000,  # 1km = ~12 min walk
            "keyword": search_term,
            "type": "restaurant|cafe|food",
            "key": API_KEY,
            "language": "sv"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get("results"):
            for place in data["results"]:
                # Skip if we've seen it
                if place["place_id"] in seen_ids:
                    continue
                seen_ids.add(place["place_id"])
                
                # Get details
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {
                    "place_id": place["place_id"],
                    "fields": "name,formatted_address,website,rating,user_ratings_total,opening_hours,price_level,types",
                    "key": API_KEY,
                    "language": "sv"
                }
                
                detail_response = requests.get(details_url, params=details_params)
                details = detail_response.json().get("result", {})
                
                # Check if it's a valid lunch spot
                if not is_valid_lunch_spot(place, details):
                    continue
                
                # Calculate walking time (rough estimate)
                distance = ((place["geometry"]["location"]["lat"] - lat)**2 + 
                           (place["geometry"]["location"]["lng"] - lon)**2)**0.5
                walk_minutes = int(distance * 111 * 12)  # Very rough estimate
                
                restaurant = {
                    "id": place["name"].lower().replace(" ", "-").replace("å", "a").replace("ä", "a").replace("ö", "o"),
                    "name": place["name"],
                    "address": details.get("formatted_address", "").split(",")[0],  # Just street
                    "website": details.get("website", ""),
                    "rating": place.get("rating", 0),
                    "review_count": place.get("user_ratings_total", 0),
                    "price_level": place.get("price_level", 2),  # 1=cheap, 4=expensive
                    "lat": place["geometry"]["location"]["lat"],
                    "lon": place["geometry"]["location"]["lng"],
                    "walk_time_min": walk_minutes,
                    "types": details.get("types", [])
                }
                
                # Categorize
                if "cafe" in restaurant["types"] or "bakery" in restaurant["types"]:
                    restaurant["category"] = "café"
                elif any(t in restaurant["name"].lower() for t in ["sushi", "thai", "indian", "asian"]):
                    restaurant["category"] = "asian"
                elif any(t in restaurant["name"].lower() for t in ["pizza", "italiano", "italiensk"]):
                    restaurant["category"] = "italiensk"
                else:
                    restaurant["category"] = "restaurang"
                
                all_restaurants.append(restaurant)
                print(f"✓ {restaurant['name']} ({restaurant['category']})")
                if restaurant["website"]:
                    print(f"  Website: {restaurant['website'][:50]}...")
    
    # Sort by rating * review_count (popularity)
    all_restaurants.sort(key=lambda x: x["rating"] * (x["review_count"]**0.5), reverse=True)
    
    return all_restaurants

# Find restaurants
print("🍽️ Finding office lunch spots in Sundbyberg...\n")
print("(Excluding hotels, gas stations, etc.)\n")

restaurants = find_lunch_restaurants()

# Save to file
output = {"restaurants": restaurants[:20]}  # Top 20
with open("restaurants_lunch.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Found {len(restaurants)} lunch restaurants")
print("📁 Saved top 20 to restaurants_lunch.json")

# Show summary
print("\n📊 Summary by category:")
categories = {}
for r in restaurants:
    cat = r.get("category", "other")
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in categories.items():
    print(f"  {cat}: {count} restauranger")

print("\n🏆 Top 10 lunch spots for office workers:")
for i, r in enumerate(restaurants[:10], 1):
    price = "kr" * r.get("price_level", 2)
    print(f"{i}. {r['name']} - ⭐ {r['rating']} ({r['review_count']} reviews) {price}")
    print(f"   {r['walk_time_min']} min walk - {r['category']}")