import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
lat, lon = 59.3615, 17.9713  # Sundbyberg centrum

def parse_opening_hours(opening_hours_data):
    """Parse Google Places opening hours into useful format"""
    if not opening_hours_data:
        return None
    
    result = {
        "open_now": opening_hours_data.get("open_now", False),
        "weekday_text": opening_hours_data.get("weekday_text", []),
        "periods": opening_hours_data.get("periods", []),
        "serves_lunch": False,
        "lunch_hours": []
    }
    
    # Check if they serve lunch (open between 11:00-14:00 on weekdays)
    lunch_days = []
    
    for period in opening_hours_data.get("periods", []):
        if "open" in period:
            day = period["open"].get("day", 0)  # 0=Sunday, 1=Monday, etc.
            open_time = period["open"].get("time", "")
            close_time = period.get("close", {}).get("time", "2359")
            
            # Convert to hours
            if open_time:
                open_hour = int(open_time[:2])
                close_hour = int(close_time[:2])
                
                # Check if open during lunch hours (11:00-14:00) on weekdays
                if day in [1, 2, 3, 4, 5]:  # Monday-Friday
                    if open_hour <= 11 and close_hour >= 14:
                        result["serves_lunch"] = True
                        lunch_days.append(day)
                        
                        # Extract specific lunch hours if available
                        result["lunch_hours"].append({
                            "day": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][day],
                            "open": open_time,
                            "close": close_time
                        })
    
    return result

def is_valid_lunch_spot(place, details):
    """Filter for proper lunch restaurants and cafés"""
    
    name = place["name"].lower()
    types = place.get("types", [])
    
    # EXCLUDE these
    exclude_keywords = ["hotel", "hotell", "okq8", "circle k", "pressbyrån", 
                       "7-eleven", "gym", "sporthall"]
    if any(kw in name for kw in exclude_keywords):
        return False
    
    # Check opening hours - must serve lunch
    opening_hours = details.get("opening_hours")
    if opening_hours:
        hours_info = parse_opening_hours(opening_hours)
        # Skip if explicitly closed during lunch
        if hours_info and not hours_info["serves_lunch"]:
            # Some dinner-only places might still be worth including
            # if they have "lunch" in name or other indicators
            if "lunch" not in name.lower() and details.get("price_level", 2) > 3:
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
                
                # Parse opening hours
                hours_info = parse_opening_hours(details.get("opening_hours"))
                
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
                    "types": details.get("types", []),
                    "opening_hours": hours_info,  # Add opening hours
                    "serves_lunch": hours_info["serves_lunch"] if hours_info else None,
                    "lunch_hours_text": hours_info["weekday_text"] if hours_info else []
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
                
                # Display with lunch indicator
                lunch_indicator = "🍽️" if (hours_info and hours_info["serves_lunch"]) else "🌙"
                print(f"✓ {restaurant['name']} ({restaurant['category']}) {lunch_indicator}")
                if restaurant["website"]:
                    print(f"  Website: {restaurant['website'][:50]}...")
                if hours_info and hours_info["weekday_text"]:
                    # Show Monday hours as example
                    monday = next((h for h in hours_info["weekday_text"] if "Måndag" in h), None)
                    if monday:
                        print(f"  Hours: {monday}")
    
    # Sort by rating * review_count (popularity) but prioritize lunch-serving places
    all_restaurants.sort(
        key=lambda x: (
            1 if x.get("serves_lunch") else 0,  # Lunch places first
            x["rating"] * (x["review_count"]**0.5)
        ), 
        reverse=True
    )
    
    return all_restaurants

# Find restaurants
print("🍽️ Finding office lunch spots in Sundbyberg...\n")
print("(Excluding hotels, gas stations, etc.)\n")
print("🍽️ = Confirmed lunch hours | 🌙 = May be dinner only\n")

restaurants = find_lunch_restaurants()

# Save to file with opening hours
output = {"restaurants": restaurants[:20]}  # Top 20
with open("restaurants_lunch_enhanced.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Found {len(restaurants)} lunch restaurants")
print("📁 Saved top 20 to restaurants_lunch_enhanced.json")

# Show summary
lunch_count = sum(1 for r in restaurants if r.get("serves_lunch"))
dinner_only = sum(1 for r in restaurants if r.get("serves_lunch") == False)
unknown = sum(1 for r in restaurants if r.get("serves_lunch") is None)

print(f"\n📊 Lunch availability:")
print(f"  Confirmed lunch: {lunch_count} restaurants")
print(f"  Possibly dinner only: {dinner_only} restaurants")
print(f"  Unknown hours: {unknown} restaurants")

print("\n📊 Summary by category:")
categories = {}
for r in restaurants:
    cat = r.get("category", "other")
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in categories.items():
    print(f"  {cat}: {count} restauranger")

print("\n🏆 Top 10 confirmed lunch spots:")
lunch_spots = [r for r in restaurants if r.get("serves_lunch")]
for i, r in enumerate(lunch_spots[:10], 1):
    price = "kr" * r.get("price_level", 2)
    print(f"{i}. {r['name']} - ⭐ {r['rating']} ({r['review_count']} reviews) {price}")
    print(f"   {r['walk_time_min']} min walk - {r['category']}")
    if r.get("lunch_hours_text"):
        # Show Monday hours
        monday = next((h for h in r["lunch_hours_text"] if "Måndag" in h), None)
        if monday:
            print(f"   {monday}")

print("\n⚠️ Possibly dinner-only restaurants (verify manually):")
dinner_spots = [r for r in restaurants if r.get("serves_lunch") == False]
for r in dinner_spots[:5]:
    print(f"- {r['name']} ({r['category']})")
    if r.get("lunch_hours_text"):
        monday = next((h for h in r["lunch_hours_text"] if "Måndag" in h), None)
        if monday:
            print(f"  {monday}")