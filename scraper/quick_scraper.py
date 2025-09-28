"""Quick traditional-only scraper to get immediate results"""

import os
import json
import requests
import asyncio
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
import openai

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SCRAPER_API_KEY = os.getenv("SCRAPERAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LAT, LON = 59.3615, 17.9713

class QuickScraper:
    """Traditional scraping only - fast results"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.results = {}
    
    async def run(self):
        """Run quick traditional scraping"""
        
        print("🚀 Quick Traditional Scraper Starting...")
        print("=" * 50)
        
        # Discover restaurants
        restaurants = self.discover_restaurants()
        print(f"📍 Found {len(restaurants)} restaurants")
        
        # Test known working restaurants first
        priority_restaurants = [
            {"name": "KRUBB Burgers", "website": "https://krubbburgers.se"},
            {"name": "Lilla Rött", "website": "https://lillaro.nu"},
            {"name": "Delibruket", "website": "https://delibruket.se"},
        ]
        
        # Add Google discovered restaurants
        all_restaurants = priority_restaurants + restaurants[:10]
        
        # Scrape each restaurant
        for restaurant in all_restaurants:
            if not restaurant.get("website"):
                continue
                
            print(f"\n🔍 Scraping: {restaurant['name']}")
            menu = await self.scrape_restaurant(restaurant)
            
            if menu and len(menu) >= 3:
                self.results[restaurant['name']] = {
                    "restaurant": restaurant['name'],
                    "website": restaurant.get("website"),
                    "items": menu,
                    "count": len(menu),
                    "scraped_at": datetime.now().isoformat()
                }
                print(f"   ✅ Found {len(menu)} items")
            else:
                print(f"   ❌ No menu found ({len(menu) if menu else 0} items)")
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def discover_restaurants(self) -> List[Dict]:
        """Quick Google Places discovery"""
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        restaurants = []
        
        params = {
            "location": f"{LAT},{LON}",
            "radius": 1500,
            "keyword": "restaurang lunch",
            "type": "restaurant",
            "key": GOOGLE_API_KEY,
            "language": "sv"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            for place in data.get("results", []):
                # Get website
                details = self.get_place_details(place["place_id"])
                website = details.get("website", "")
                
                if website:  # Only include if has website
                    restaurants.append({
                        "name": place["name"],
                        "website": website,
                        "rating": place.get("rating", 0)
                    })
        except:
            pass
        
        return restaurants
    
    def get_place_details(self, place_id: str) -> Dict:
        """Get Google Place details"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website",
            "key": GOOGLE_API_KEY
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            return response.json().get("result", {})
        except:
            return {}
    
    async def scrape_restaurant(self, restaurant: Dict) -> List[Dict]:
        """Traditional scraping with multiple URL attempts"""
        
        website = restaurant["website"]
        
        # Try multiple URL patterns
        urls_to_try = [
            website,
            f"{website.rstrip('/')}/meny",
            f"{website.rstrip('/')}/lunch",
            f"{website.rstrip('/')}/dagens-lunch"
        ]
        
        for url in urls_to_try:
            print(f"      Trying: {url}")
            
            params = {
                'api_key': SCRAPER_API_KEY,
                'url': url,
                'render': 'true',
                'country_code': 'se'
            }
            
            try:
                response = requests.get(
                    'http://api.scraperapi.com',
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    menu = self.extract_menu_with_ai(response.text, restaurant['name'])
                    if menu and len(menu) >= 3:
                        print(f"      ✅ Success: {len(menu)} items")
                        return menu
                    elif menu:
                        print(f"      ⚠️ Only {len(menu)} items")
                else:
                    print(f"      ❌ HTTP {response.status_code}")
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:50]}")
        
        return []
    
    def extract_menu_with_ai(self, html: str, restaurant_name: str) -> List[Dict]:
        """Extract menu using GPT-4o-mini"""
        
        prompt = f"""Extract lunch menu items from this HTML for {restaurant_name}.

Return JSON array with:
- name: dish name
- description: ingredients/description (if available)
- price: price in SEK (40-200 range typically)
- category: Kött/Fisk/Vegetarisk/Pasta/Pizza/etc

HTML content:
{html[:8000]}

Return ONLY valid JSON array or empty array if no menu found."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                timeout=30
            )
            
            result = response.choices[0].message.content
            result = result.replace('```json', '').replace('```', '').strip()
            
            items = json.loads(result)
            # Filter reasonable lunch prices
            return [i for i in items if 40 <= i.get("price", 0) <= 200]
        except Exception as e:
            print(f"      AI extraction error: {str(e)[:50]}")
            return []
    
    def save_results(self):
        """Save results"""
        os.makedirs("data", exist_ok=True)
        
        with open("data/quick_scrape_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # Create dishes list for frontend
        all_dishes = []
        for data in self.results.values():
            for item in data["items"]:
                item["restaurant"] = data["restaurant"]
                all_dishes.append(item)
        
        with open("data/quick_lunch_dishes.json", "w", encoding="utf-8") as f:
            json.dump(all_dishes, f, ensure_ascii=False, indent=2)
    
    def print_summary(self):
        """Print summary"""
        total_dishes = sum(len(data["items"]) for data in self.results.values())
        
        print("\n" + "=" * 50)
        print("📊 QUICK SCRAPE RESULTS")
        print("=" * 50)
        print(f"✅ Restaurants with menus: {len(self.results)}")
        print(f"🍽️ Total dishes found: {total_dishes}")
        print(f"📁 Results saved to data/quick_*.json")
        
        for name, data in self.results.items():
            print(f"   - {name}: {data['count']} items")

async def main():
    scraper = QuickScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())