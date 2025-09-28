import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Sundbyberg centrum coordinates
lat, lon = 59.3615, 17.9713

def find_restaurants():
    """Find actual restaurants (not hotels) in Sundbyberg"""
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    restaurants = []
    
    # Search for restaurants specifically
    params = {
        "location": f"{lat},{lon}",
        "radius": 1000,  # 1km radius (walking distance)
        "type": "restaurant",
        "keyword": "lunch OR restaurang OR mat",  # Swedish keywords
        "key": API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("results"):
        for place in data["results"]:
            # Filter out hotels, gas stations, etc
            types = place.get("types", [])
            name = place["name"].lower()
            
            # Skip if it's primarily a hotel or gas station
            if "lodging" in types or "gas_station" in types:
                continue
            if "hotel" in name or "okq8" in name:
                continue
                
            # Get more details
            place_id = place["place_id"]
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": place_id,
                "fields": "name,formatted_address,website,rating,user_ratings_total,opening_hours,price_level",
                "key": API_KEY,
                "language": "sv"  # Swedish
            }
            
            detail_response = requests.get(details_url, params=details_params)
            details = detail_response.json().get("result", {})
            
            restaurant = {
                "id": place["name"].lower().replace(" ", "-"),
                "name": place["name"],
                "address": details.get("formatted_address", ""),
                "website": details.get("website", ""),
                "rating": place.get("rating", 0),
                "user_ratings_total": place.get("user_ratings_total", 0),
                "price_level": place.get("price_level", 0),
                "lat": place["geometry"]["location"]["lat"],
                "lon": place["geometry"]["location"]["lng"]
            }
            
            # Only add if it has a website (more likely to have lunch menu)
            if restaurant["website"] or "restaurant" in types:
                restaurants.append(restaurant)
                print(f"✓ {restaurant['name']}")
                if restaurant["website"]:
                    print(f"  Website: {restaurant['website']}")
    
    return restaurants

# Find restaurants
print("🔍 Finding lunch restaurants in Sundbyberg...\n")
restaurants = find_restaurants()

# Save to restaurants_google.json
output = {"restaurants": restaurants}
with open("restaurants_google.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Found {len(restaurants)} restaurants")
print("📁 Saved to restaurants_google.json")

# Show top 5
print("\n🏆 Top restaurants by rating:")
sorted_restaurants = sorted(restaurants, key=lambda x: x.get("rating", 0), reverse=True)
for r in sorted_restaurants[:5]:
    print(f"  {r['name']} - ⭐ {r.get('rating', 'N/A')} ({r.get('user_ratings_total', 0)} reviews)")