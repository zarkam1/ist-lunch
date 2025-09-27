"""
Unified IST Lunch Scraper Pipeline
Combines Google Places discovery with AI scraping and vision fallback
"""

import os
import json
import requests
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import openai
from playwright.async_api import async_playwright
import base64

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
SCRAPER_API_KEY = os.getenv("SCRAPERAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Location: Sundbyberg
LAT, LON = 59.3615, 17.9713

# Blacklist - Confirmed NOT serving weekday lunch
BLACKLIST = [
    "delibruket-flatbread",  # Confirmed no weekday lunch
    "piatti",                 # Opens 17:00
    "parma",                  # Dinner only
    # Add more as confirmed
]

# Whitelist - Override Google, we KNOW these serve lunch  
WHITELIST = [
    "restaurang-s",
    "tre-broder",
    "bra-mat",
    # Add more verified lunch spots
]

class UnifiedLunchScraper:
    """Main pipeline combining all techniques"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.restaurants = []
        self.menus = {}
        
    async def run_full_pipeline(self):
        """Execute complete lunch discovery and scraping pipeline"""
        
        print("🚀 IST Lunch Unified Pipeline Starting...")
        print("=" * 60)
        
        # Step 1: Discover restaurants
        print("\n📍 Step 1: Discovering restaurants via Google Places...")
        self.restaurants = await self.discover_restaurants()
        print(f"   Found {len(self.restaurants)} potential restaurants")
        
        # Step 2: Filter with blacklist/whitelist
        print("\n🔍 Step 2: Applying blacklist/whitelist...")
        self.restaurants = self.filter_restaurants()
        print(f"   {len(self.restaurants)} restaurants after filtering")
        
        # Step 3: Scrape menus
        print("\n🍽️ Step 3: Scraping menus...")
        await self.scrape_all_menus()
        
        # Step 4: Save results
        print("\n💾 Step 4: Saving results...")
        self.save_results()
        
        # Summary
        self.print_summary()
    
    async def discover_restaurants(self) -> List[Dict]:
        """Discover restaurants using Google Places API"""
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        restaurants = []
        seen_ids = set()
        
        search_terms = [
            "restaurang lunch", "café lunch", "sushi",
            "thai restaurang", "dagens lunch"
        ]
        
        for term in search_terms:
            params = {
                "location": f"{LAT},{LON}",
                "radius": 1500,
                "keyword": term,
                "type": "restaurant|cafe|food",
                "key": GOOGLE_API_KEY,
                "language": "sv"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            for place in data.get("results", []):
                if place["place_id"] in seen_ids:
                    continue
                seen_ids.add(place["place_id"])
                
                # Get details
                details = self.get_place_details(place["place_id"])
                
                restaurant = {
                    "id": self.create_id(place["name"]),
                    "name": place["name"],
                    "website": details.get("website", ""),
                    "rating": place.get("rating", 0),
                    "serves_lunch": self.check_lunch_hours(details),
                    "opening_hours": details.get("opening_hours", {})
                }
                restaurants.append(restaurant)
        
        return restaurants
    
    def filter_restaurants(self) -> List[Dict]:
        """Apply blacklist and whitelist"""
        
        filtered = []
        for r in self.restaurants:
            rest_id = r["id"]
            
            # Skip blacklisted
            if rest_id in BLACKLIST:
                print(f"   ❌ Skipping {r['name']} (blacklisted)")
                continue
            
            # Include whitelisted regardless of hours
            if rest_id in WHITELIST:
                r["serves_lunch"] = True
                r["whitelisted"] = True
                print(f"   ✅ Including {r['name']} (whitelisted)")
                filtered.append(r)
            # Include if serves lunch
            elif r.get("serves_lunch"):
                print(f"   ✅ Including {r['name']} (lunch hours confirmed)")
                filtered.append(r)
            # Skip if no lunch
            else:
                print(f"   ⏭️ Skipping {r['name']} (no lunch hours)")
        
        return filtered
    
    async def scrape_all_menus(self):
        """Scrape menus using hybrid approach"""
        
        for restaurant in self.restaurants:
            print(f"\n🔍 Scraping: {restaurant['name']}")
            
            # Try traditional first
            menu = await self.try_traditional_scraping(restaurant)
            
            # Fallback to vision if needed
            if not menu or len(menu) < 3:
                print("   📸 Using vision fallback...")
                menu = await self.try_vision_scraping(restaurant)
            
            if menu:
                self.menus[restaurant['id']] = {
                    "restaurant": restaurant['name'],
                    "items": menu,
                    "count": len(menu),
                    "scraped_at": datetime.now().isoformat()
                }
                print(f"   ✅ Found {len(menu)} items")
            else:
                print(f"   ❌ No menu found")
    
    async def try_traditional_scraping(self, restaurant: Dict) -> List[Dict]:
        """Traditional scraping with ScraperAPI"""
        
        if not restaurant.get("website"):
            return []
        
        url = restaurant["website"]
        
        # Try multiple URL patterns
        urls_to_try = [
            url,
            f"{url}/meny" if not url.endswith('/') else f"{url}meny",
            f"{url}/lunch",
            f"{url}/dagens-lunch"
        ]
        
        for test_url in urls_to_try:
            params = {
                'api_key': SCRAPER_API_KEY,
                'url': test_url,
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
                    if menu:
                        return menu
            except:
                continue
        
        return []
    
    async def try_vision_scraping(self, restaurant: Dict) -> List[Dict]:
        """Vision scraping with Playwright + GPT-4"""
        
        if not restaurant.get("website"):
            return []
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(restaurant["website"], wait_until='networkidle')
                
                # Try to find and click menu link
                menu_selectors = ['text=/Meny/i', 'text=/Lunch/i', 'text=/Dagens/i']
                for selector in menu_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        await page.wait_for_timeout(1000)
                        break
                    except:
                        continue
                
                # Take screenshot
                screenshot = await page.screenshot(full_page=True)
                await browser.close()
                
                # Analyze with GPT-4 Vision
                return self.analyze_screenshot(screenshot, restaurant['name'])
        except:
            return []
    
    def extract_menu_with_ai(self, html: str, restaurant_name: str) -> List[Dict]:
        """Extract menu using GPT-4o-mini"""
        
        prompt = f"""Extract lunch menu items from this HTML.
Restaurant: {restaurant_name}

Return JSON array of items with:
- name: dish name
- description: ingredients/description (if available)
- price: price in SEK (50-200 range typically)
- category: Kött/Fisk/Vegetarisk/Pasta/Pizza/Asiatiskt/etc

HTML content:
{html[:8000]}

Return ONLY valid JSON array or empty array if no menu found."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            result = result.replace('```json', '').replace('```', '').strip()
            
            items = json.loads(result)
            # Filter reasonable lunch prices
            return [i for i in items if 40 <= i.get("price", 0) <= 200]
        except:
            return []
    
    def analyze_screenshot(self, screenshot: bytes, restaurant_name: str) -> List[Dict]:
        """Analyze screenshot with GPT-4 Vision"""
        
        base64_image = base64.b64encode(screenshot).decode('utf-8')
        
        # Special handling for ethnic restaurants
        is_ethnic = any(kw in restaurant_name.lower() 
                       for kw in ['thai', 'sushi', 'persian', 'indian', 'asian'])
        
        prompt = f"""Extract lunch menu items from this screenshot.
{"IMPORTANT: Include Swedish descriptions for foreign dish names!" if is_ethnic else ""}

Return JSON array with:
- name: dish name
- description: what it contains (CRITICAL for ethnic food)
- price: in SEK
- category: appropriate category

Only include items 40-200 SEK (lunch range)."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            result = result.replace('```json', '').replace('```', '').strip()
            return json.loads(result)
        except:
            return []
    
    def save_results(self):
        """Save all results"""
        
        # Save restaurants
        with open("data/restaurants_verified.json", "w", encoding="utf-8") as f:
            json.dump(self.restaurants, f, ensure_ascii=False, indent=2)
        
        # Save menus
        with open("data/all_menus.json", "w", encoding="utf-8") as f:
            json.dump(self.menus, f, ensure_ascii=False, indent=2)
        
        # Create combined lunch data for frontend
        all_dishes = []
        for rest_id, data in self.menus.items():
            for item in data["items"]:
                item["restaurant"] = data["restaurant"]
                item["restaurant_id"] = rest_id
                all_dishes.append(item)
        
        with open("data/lunch_dishes_complete.json", "w", encoding="utf-8") as f:
            json.dump(all_dishes, f, ensure_ascii=False, indent=2)
    
    def print_summary(self):
        """Print final summary"""
        
        total_dishes = sum(len(m["items"]) for m in self.menus.values())
        
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"✅ Restaurants scraped: {len(self.menus)}/{len(self.restaurants)}")
        print(f"🍽️ Total dishes found: {total_dishes}")
        print(f"📁 Results saved to data/")
        
        # Success rate
        success_rate = (len(self.menus) / len(self.restaurants) * 100) if self.restaurants else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        # Cost estimate
        traditional = len([1 for m in self.menus.values() if len(m["items"]) > 5])
        vision = len(self.menus) - traditional
        cost = (traditional * 0.002) + (vision * 0.10)
        print(f"💰 Estimated cost: ${cost:.2f}")
    
    # Helper methods
    def create_id(self, name: str) -> str:
        """Create restaurant ID from name"""
        return name.lower().replace(" ", "-").replace("å", "a").replace("ä", "a").replace("ö", "o")
    
    def get_place_details(self, place_id: str) -> Dict:
        """Get Google Place details"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "website,opening_hours",
            "key": GOOGLE_API_KEY
        }
        response = requests.get(url, params=params)
        return response.json().get("result", {})
    
    def check_lunch_hours(self, details: Dict) -> bool:
        """Check if restaurant serves lunch"""
        hours = details.get("opening_hours", {})
        for period in hours.get("periods", []):
            if "open" in period:
                day = period["open"].get("day", 0)
                open_time = period["open"].get("time", "")
                if day in [1,2,3,4,5] and open_time:
                    open_hour = int(open_time[:2])
                    if open_hour <= 11:
                        return True
        return False

# Main execution
async def main():
    scraper = UnifiedLunchScraper()
    await scraper.run_full_pipeline()

if __name__ == "__main__":
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Run the pipeline
    asyncio.run(main())