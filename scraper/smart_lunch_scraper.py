"""
Smart IST Lunch Scraper with configurable update frequencies
Prioritizes closest restaurants and handles daily/weekly menus
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# CORRECT IST OFFICE LOCATION: Esplanaden 1, Sundbyberg
LAT = 59.3685
LON = 17.9668
MAX_WALK_MINUTES = 12  # Maximum walking distance

# Restaurant Configuration
RESTAURANT_CONFIG = {
    # DAILY UPDATE RESTAURANTS (changes every day)
    "restaurang-s": {
        "update_frequency": "daily",
        "priority": 1,  # Always include
        "special_instructions": "Menu changes daily, check each morning"
    },
    "the-public": {
        "update_frequency": "daily",
        "priority": 1,
        "special_instructions": "Daily specials"
    },
    
    # WEEKLY UPDATE RESTAURANTS (fixed weekly menu)
    "tre-broder": {
        "update_frequency": "weekly",
        "update_day": "monday",
        "priority": 2
    },
    "krubb-burgers-sundbyberg": {
        "update_frequency": "weekly",
        "update_day": "monday",
        "priority": 2
    },
    "ristorante-rustico": {
        "update_frequency": "weekly", 
        "update_day": "monday",
        "priority": 2
    },
    
    # STATIC RESTAURANTS (rarely changes)
    "burgers-beer": {
        "update_frequency": "static",
        "update_day": "monday",  # Check once a week just in case
        "priority": 3
    }
}

# Blacklist (never scrape these)
BLACKLIST = [
    "delibruket-flatbread",  # No weekday lunch
    "piatti",                 # Dinner only
    "parma"                   # Dinner only
]

class SmartLunchScraper:
    def __init__(self):
        self.today = datetime.now().strftime("%A").lower()
        self.restaurants = []
        self.menus_by_day = {
            "monday": {},
            "tuesday": {},
            "wednesday": {},
            "thursday": {},
            "friday": {}
        }
        
    def find_closest_restaurants(self, limit: int = 25) -> List[Dict]:
        """Find closest restaurants with walking time calculation"""
        
        print(f"📍 Finding restaurants near IST office (Esplanaden 1)")
        print(f"   Max walking distance: {MAX_WALK_MINUTES} minutes")
        
        API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        all_restaurants = []
        seen_ids = set()
        
        # Search with correct coordinates
        search_terms = ["restaurang lunch", "dagens lunch", "sushi", "thai", "restaurang S"]
        
        for term in search_terms:
            params = {
                "location": f"{LAT},{LON}",
                "radius": MAX_WALK_MINUTES * 80,  # ~80m per minute walking
                "keyword": term,
                "type": "restaurant",
                "key": API_KEY
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            for place in data.get("results", []):
                if place["place_id"] in seen_ids:
                    continue
                seen_ids.add(place["place_id"])
                
                # Calculate exact walking distance
                plat = place["geometry"]["location"]["lat"]
                plon = place["geometry"]["location"]["lng"]
                
                # Better distance calculation (Haversine-ish)
                distance_km = ((plat - LAT)**2 + (plon - LON)**2)**0.5 * 111
                walk_minutes = int(distance_km * 15)  # 15 min per km walking
                
                rest_id = self.create_id(place["name"])
                
                # Skip blacklisted
                if rest_id in BLACKLIST:
                    continue
                
                # Get details for website and hours
                details = self.get_place_details(place["place_id"])
                
                restaurant = {
                    "id": rest_id,
                    "name": place["name"],
                    "walk_minutes": walk_minutes,
                    "distance_m": int(distance_km * 1000),
                    "website": details.get("website", ""),
                    "rating": place.get("rating", 0),
                    "lat": plat,
                    "lon": plon,
                    "update_frequency": RESTAURANT_CONFIG.get(rest_id, {}).get("update_frequency", "weekly"),
                    "priority": RESTAURANT_CONFIG.get(rest_id, {}).get("priority", 3)
                }
                
                all_restaurants.append(restaurant)
        
        # Sort by priority then distance
        all_restaurants.sort(key=lambda x: (x["priority"], x["walk_minutes"]))
        
        # Ensure Restaurang S is included
        has_rest_s = any(r["id"] == "restaurang-s" for r in all_restaurants)
        if not has_rest_s:
            print("⚠️ Restaurang S not found in initial search, searching specifically...")
            # Search specifically for Restaurang S with wider radius
            # ... (additional search logic)
        
        return all_restaurants[:limit]
    
    def should_update_today(self, restaurant: Dict) -> bool:
        """Check if restaurant should be updated today"""
        
        rest_id = restaurant["id"]
        config = RESTAURANT_CONFIG.get(rest_id, {})
        frequency = config.get("update_frequency", "weekly")
        
        if frequency == "daily":
            return True
        elif frequency == "weekly":
            update_day = config.get("update_day", "monday")
            return self.today == update_day
        elif frequency == "static":
            # Update once a week on configured day
            update_day = config.get("update_day", "monday")
            return self.today == update_day
        else:
            # Default: update on Mondays
            return self.today == "monday"
    
    async def scrape_restaurant_menu(self, restaurant: Dict) -> Dict:
        """Scrape menu for a single restaurant"""
        
        rest_id = restaurant["id"]
        config = RESTAURANT_CONFIG.get(rest_id, {})
        
        # For daily restaurants, try to get each day's menu
        if config.get("update_frequency") == "daily":
            return await self.scrape_daily_menu(restaurant)
        else:
            return await self.scrape_weekly_menu(restaurant)
    
    async def scrape_daily_menu(self, restaurant: Dict) -> Dict:
        """Scrape menu that changes daily (like Restaurang S)"""
        
        print(f"   📅 Scraping daily menu for {restaurant['name']}")
        
        # This would use your vision scraper
        # For Restaurang S, might need special handling to get each day
        menu = {
            "monday": [],
            "tuesday": [],
            "wednesday": [],
            "thursday": [],
            "friday": []
        }
        
        # Try to extract all weekdays if visible
        # Otherwise just get today's menu
        # ... (implement scraping logic)
        
        return menu
    
    async def scrape_weekly_menu(self, restaurant: Dict) -> Dict:
        """Scrape weekly menu (same all week)"""
        
        print(f"   📋 Scraping weekly menu for {restaurant['name']}")
        
        # Scrape once, apply to all days
        items = []  # ... scrape items
        
        # Apply same menu to all weekdays
        menu = {
            "monday": items,
            "tuesday": items,
            "wednesday": items,
            "thursday": items,
            "friday": items
        }
        
        return menu
    
    def create_daily_view(self) -> Dict:
        """Create Manus-style daily view of all restaurants"""
        
        daily_view = {}
        
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            daily_view[day] = {
                "date": self.get_date_for_day(day),
                "restaurants": []
            }
            
            for rest_id, menu in self.menus_by_day[day].items():
                if menu:  # Only include if menu exists
                    restaurant_info = next((r for r in self.restaurants if r["id"] == rest_id), {})
                    daily_view[day]["restaurants"].append({
                        "name": restaurant_info.get("name", rest_id),
                        "walk_minutes": restaurant_info.get("walk_minutes", 0),
                        "items": menu,
                        "item_count": len(menu)
                    })
            
            # Sort by walking distance
            daily_view[day]["restaurants"].sort(key=lambda x: x["walk_minutes"])
        
        return daily_view
    
    def save_results(self):
        """Save in multiple formats for flexibility"""
        
        os.makedirs("data", exist_ok=True)
        
        # Save restaurant list with distances
        with open("data/restaurants_by_distance.json", "w", encoding="utf-8") as f:
            json.dump(self.restaurants, f, indent=2, ensure_ascii=False)
        
        # Save daily view (Manus-style)
        daily_view = self.create_daily_view()
        with open("data/lunch_by_day.json", "w", encoding="utf-8") as f:
            json.dump(daily_view, f, indent=2, ensure_ascii=False)
        
        # Save update schedule
        schedule = {}
        for restaurant in self.restaurants[:20]:
            rest_id = restaurant["id"]
            config = RESTAURANT_CONFIG.get(rest_id, {})
            schedule[rest_id] = {
                "name": restaurant["name"],
                "frequency": config.get("update_frequency", "weekly"),
                "next_update": self.get_next_update(rest_id)
            }
        
        with open("data/update_schedule.json", "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
        
        print("\n💾 Saved:")
        print("   - restaurants_by_distance.json (sorted by walk time)")
        print("   - lunch_by_day.json (Manus-style daily view)")
        print("   - update_schedule.json (when to update each restaurant)")
    
    def get_next_update(self, rest_id: str) -> str:
        """Calculate next update time for restaurant"""
        config = RESTAURANT_CONFIG.get(rest_id, {})
        frequency = config.get("update_frequency", "weekly")
        
        if frequency == "daily":
            return "tomorrow"
        elif frequency == "weekly":
            return f"next {config.get('update_day', 'monday')}"
        else:
            return "next monday"
    
    def get_date_for_day(self, day: str) -> str:
        """Get actual date for weekday"""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        today_idx = days.index(self.today)
        target_idx = days.index(day)
        
        if target_idx >= today_idx:
            days_ahead = target_idx - today_idx
        else:
            days_ahead = 7 - today_idx + target_idx
        
        target_date = datetime.now() + timedelta(days=days_ahead)
        return target_date.strftime("%Y-%m-%d")
    
    def print_summary(self):
        """Print configuration summary"""
        
        print("\n" + "=" * 60)
        print("📊 SCRAPING CONFIGURATION")
        print("=" * 60)
        
        daily_count = sum(1 for r in self.restaurants[:20] 
                         if RESTAURANT_CONFIG.get(r["id"], {}).get("update_frequency") == "daily")
        weekly_count = sum(1 for r in self.restaurants[:20] 
                          if RESTAURANT_CONFIG.get(r["id"], {}).get("update_frequency") != "daily")
        
        print(f"\n📍 Closest restaurants to IST (Esplanaden 1):")
        for i, r in enumerate(self.restaurants[:10], 1):
            freq = RESTAURANT_CONFIG.get(r["id"], {}).get("update_frequency", "weekly")
            emoji = "📅" if freq == "daily" else "📋"
            print(f"{i:2}. {emoji} {r['name'][:30]:<30} {r['walk_minutes']:2} min walk ({freq})")
        
        print(f"\n📈 Update frequency:")
        print(f"   Daily updates: {daily_count} restaurants")
        print(f"   Weekly updates: {weekly_count} restaurants")
        
        # Check Restaurang S specifically
        rest_s = next((r for r in self.restaurants if r["id"] == "restaurang-s"), None)
        if rest_s:
            print(f"\n✅ Restaurang S found: {rest_s['walk_minutes']} min walk")
            print(f"   Will update: DAILY (menu changes each day)")
        else:
            print("\n⚠️ Restaurang S not found - may need to search with wider radius")
    
    # Helper methods
    def create_id(self, name: str) -> str:
        return name.lower().replace(" ", "-").replace("å", "a").replace("ä", "a").replace("ö", "o")
    
    def get_place_details(self, place_id: str) -> Dict:
        API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website,opening_hours",
            "key": API_KEY
        }
        response = requests.get(url, params=params)
        return response.json().get("result", {})

async def main():
    scraper = SmartLunchScraper()
    
    # Find closest restaurants
    scraper.restaurants = scraper.find_closest_restaurants(limit=25)
    
    # Show configuration
    scraper.print_summary()
    
    # Check what needs updating today
    print(f"\n📅 Today is {scraper.today.title()}")
    to_update = [r for r in scraper.restaurants if scraper.should_update_today(r)]
    print(f"Need to update: {len(to_update)} restaurants")
    
    for r in to_update[:5]:
        print(f"   - {r['name']}")
    
    # Save configuration
    scraper.save_results()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())