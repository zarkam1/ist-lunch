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

# Known problem sites that require screenshot scraping
REQUIRES_SCREENSHOT = [
    "the-public",      # Elementor/WordPress with dynamic loading
    "restaurang-s",    # Divi theme with JavaScript rendering
    "chopchop",        # Heavy JavaScript, needs /meny endpoint
    "bonab"            # Works but needs descriptions for Persian dishes
]

# Update frequency configuration
RESTAURANT_CONFIG = {
    # DAILY UPDATE RESTAURANTS (changes every day)
    "restaurang-s": {
        "update_frequency": "daily",
        "priority": 1,
        "requires_screenshot": True,
        "special_instructions": "Menu changes daily, check each morning"
    },
    "the-public": {
        "update_frequency": "daily", 
        "priority": 1,
        "requires_screenshot": True,
        "special_instructions": "Daily specials, Elementor theme"
    },
    "chopchop": {
        "update_frequency": "weekly",
        "priority": 2,
        "requires_screenshot": True,
        "url_override": "/meny",
        "special_instructions": "Navigate to /meny endpoint"
    },
    "bonab": {
        "update_frequency": "weekly",
        "priority": 2,
        "requires_screenshot": True,
        "special_instructions": "Persian restaurant - extract descriptions"
    }
}

class UnifiedLunchScraper:
    """Main pipeline combining all techniques"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.restaurants = []
        self.menus = {}
        self.scraping_stats = {
            "traditional_success": 0,
            "traditional_failed": 0,
            "screenshot_success": 0,
            "screenshot_failed": 0,
            "total_cost": 0.0
        }
        
    async def run_full_pipeline(self, force_all=False):
        """Execute complete lunch discovery and scraping pipeline"""
        
        print("🚀 IST Lunch Unified Pipeline Starting...")
        if force_all:
            print("🔥 FORCE MODE: Ignoring schedule, updating ALL restaurants")
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
        await self.scrape_all_menus(force_all)
        
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
    
    async def scrape_all_menus(self, force_all=False):
        """Scrape menus using smart routing approach"""
        
        for restaurant in self.restaurants:
            print(f"\n🔍 Scraping: {restaurant['name']}")
            
            # Check if restaurant should be updated today (unless forced)
            if not force_all and not self.should_update_today(restaurant):
                print("   ⏭️ Skipping (not scheduled for today)")
                continue
            
            rest_id = restaurant["id"]
            config = RESTAURANT_CONFIG.get(rest_id, {})
            
            # Use smart routing to determine approach
            menu, method_used, cost = await self.smart_route_scraping(restaurant)
            
            # Track statistics
            self.scraping_stats["total_cost"] += cost
            if method_used == "traditional":
                if menu and len(menu) >= 3:
                    self.scraping_stats["traditional_success"] += 1
                else:
                    self.scraping_stats["traditional_failed"] += 1
            elif method_used == "screenshot":
                if menu and len(menu) >= 3:
                    self.scraping_stats["screenshot_success"] += 1
                else:
                    self.scraping_stats["screenshot_failed"] += 1
            
            if menu and len(menu) >= 3:
                self.menus[restaurant['id']] = {
                    "restaurant": restaurant['name'],
                    "items": menu,
                    "count": len(menu),
                    "method": method_used,
                    "cost": cost,
                    "scraped_at": datetime.now().isoformat(),
                    "config": config
                }
                print(f"   ✅ Found {len(menu)} items via {method_used} (${cost:.3f})")
            else:
                print(f"   ❌ No menu found via {method_used}")
    
    def should_update_today(self, restaurant: Dict) -> bool:
        """Check if restaurant should be updated today based on configuration"""
        
        rest_id = restaurant["id"]
        config = RESTAURANT_CONFIG.get(rest_id, {"update_frequency": "weekly"})
        frequency = config.get("update_frequency", "weekly")
        
        today = datetime.now().strftime("%A").lower()
        
        if frequency == "daily":
            return True
        elif frequency == "weekly":
            # Default to Monday for weekly updates
            return today == "monday"
        elif frequency == "static":
            # Update once a week on Monday
            return today == "monday"
        else:
            return today == "monday"
    
    async def smart_route_scraping(self, restaurant: Dict) -> tuple[List[Dict], str, float]:
        """Smart routing: decide between traditional and screenshot based on site"""
        
        rest_id = restaurant["id"]
        config = RESTAURANT_CONFIG.get(rest_id, {})
        
        # Force screenshot for known problem sites
        if rest_id in REQUIRES_SCREENSHOT or config.get("requires_screenshot", False):
            print("   📸 Using screenshot (known problem site)")
            menu = await self.try_vision_scraping(restaurant)
            return menu or [], "screenshot", 0.10
        
        # Try traditional first for other sites
        print("   🔧 Trying traditional scraping...")
        menu = await self.try_traditional_scraping(restaurant)
        
        # Automatic failure detection: <3 items = failed extraction
        if not menu or len(menu) < 3:
            print(f"   ⚠️ Traditional failed ({len(menu) if menu else 0} items), falling back to screenshot")
            menu = await self.try_vision_scraping(restaurant)
            return menu or [], "screenshot", 0.10
        
        print(f"   ✅ Traditional success ({len(menu)} items)")
        return menu, "traditional", 0.002
    
    async def try_traditional_scraping(self, restaurant: Dict) -> List[Dict]:
        """Traditional scraping with ScraperAPI and multiple URL attempts"""
        
        if not restaurant.get("website"):
            return []
        
        url = restaurant["website"]
        rest_id = restaurant["id"]
        config = RESTAURANT_CONFIG.get(rest_id, {})
        
        # Get URL override if specified
        url_override = config.get("url_override")
        if url_override:
            if url_override.startswith('/'):
                url = url.rstrip('/') + url_override
            else:
                url = url_override
        
        # Try multiple URL patterns in order of likelihood
        urls_to_try = [
            url,
            f"{url.rstrip('/')}/meny",
            f"{url.rstrip('/')}/lunch", 
            f"{url.rstrip('/')}/dagens-lunch",
            f"{url.rstrip('/')}/menu",
            f"{url.rstrip('/')}/mat"
        ]
        
        # Remove duplicates while preserving order
        urls_to_try = list(dict.fromkeys(urls_to_try))
        
        for i, test_url in enumerate(urls_to_try):
            print(f"      Trying URL {i+1}/{len(urls_to_try)}: {test_url}")
            
            params = {
                'api_key': SCRAPER_API_KEY,
                'url': test_url,
                'render': 'true',
                'country_code': 'se',
                'wait_for_selector': '.menu, .lunch, main, .content',
                'wait_for': '2000'  # Wait 2 seconds for JS
            }
            
            try:
                response = requests.get(
                    'http://api.scraperapi.com',
                    params=params,
                    timeout=45
                )
                
                if response.status_code == 200:
                    menu = self.extract_menu_with_ai(response.text, restaurant['name'])
                    if menu and len(menu) >= 3:
                        print(f"      ✅ Success with URL: {test_url}")
                        return menu
                    elif menu:
                        print(f"      ⚠️ Only {len(menu)} items found, trying next URL")
                else:
                    print(f"      ❌ HTTP {response.status_code}")
            except Exception as e:
                print(f"      ❌ Error: {str(e)[:50]}")
                continue
        
        return []
    
    async def try_vision_scraping(self, restaurant: Dict) -> List[Dict]:
        """Vision scraping with Playwright + GPT-4 with enhanced navigation"""
        
        if not restaurant.get("website"):
            return []
        
        rest_id = restaurant["id"]
        config = RESTAURANT_CONFIG.get(rest_id, {})
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    locale='sv-SE'
                )
                page = await context.new_page()
                
                # Navigate to URL (with override if specified)
                url = restaurant["website"]
                url_override = config.get("url_override")
                if url_override:
                    if url_override.startswith('/'):
                        url = url.rstrip('/') + url_override
                    else:
                        url = url_override
                
                print(f"      📸 Navigating to: {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(3000)  # Wait for JS to render
                
                # Try to find and click menu links (multiple strategies)
                menu_clicked = False
                menu_selectors = [
                    'text=/Meny/i', 'text=/Lunch/i', 'text=/Dagens/i', 
                    'text=/Menu/i', 'text=/Mat/i',
                    'a[href*="meny"]', 'a[href*="lunch"]', 'a[href*="menu"]',
                    '[class*="menu"]', '[class*="lunch"]'
                ]
                
                for selector in menu_selectors:
                    try:
                        print(f"      Trying to click: {selector}")
                        await page.click(selector, timeout=3000)
                        await page.wait_for_timeout(2000)
                        menu_clicked = True
                        print(f"      ✅ Clicked menu link")
                        break
                    except:
                        continue
                
                # Special handling for specific sites
                if rest_id == "chopchop" and not menu_clicked:
                    # ChopChop specific: navigate directly to /meny
                    meny_url = f"{restaurant['website'].rstrip('/')}/meny"
                    print(f"      📍 ChopChop: Navigating to {meny_url}")
                    await page.goto(meny_url, wait_until='networkidle')
                    await page.wait_for_timeout(2000)
                
                # Take full page screenshot
                print(f"      📷 Taking screenshot...")
                screenshot = await page.screenshot(full_page=True)
                await browser.close()
                
                # Analyze with GPT-4 Vision
                return self.analyze_screenshot(screenshot, restaurant['name'], config)
                
        except Exception as e:
            print(f"      ❌ Vision scraping error: {str(e)[:100]}")
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
    
    def analyze_screenshot(self, screenshot: bytes, restaurant_name: str, config: Dict = None) -> List[Dict]:
        """Analyze screenshot with GPT-4 Vision with enhanced prompts"""
        
        base64_image = base64.b64encode(screenshot).decode('utf-8')
        config = config or {}
        
        # Special handling for ethnic restaurants
        is_ethnic = any(kw in restaurant_name.lower() 
                       for kw in ['thai', 'sushi', 'persian', 'indian', 'asian', 'bonab'])
        
        # Enhanced prompt based on restaurant type and special instructions
        special_instructions = config.get("special_instructions", "")
        
        base_prompt = f"""Extract lunch menu items from this screenshot of {restaurant_name}.

IMPORTANT REQUIREMENTS:
- Only include lunch items (40-200 SEK range)
- Return JSON array with: name, description, price, category
"""
        
        if is_ethnic or "persian" in restaurant_name.lower():
            base_prompt += """
CRITICAL FOR ETHNIC RESTAURANTS:
- Extract BOTH original dish names AND Swedish descriptions
- Include ingredients/contents in description field
- Essential for customers to understand what they're ordering"""
        
        if "daily" in special_instructions.lower():
            base_prompt += """
- Look for daily specials or weekday-specific menus
- Extract day-specific information if visible"""
        
        if special_instructions:
            base_prompt += f"""

SPECIAL INSTRUCTIONS: {special_instructions}"""
        
        prompt = base_prompt + """

Return ONLY valid JSON array format:
[{"name": "dish name", "description": "ingredients/description", "price": 125, "category": "Kött/Fisk/Vegetarisk"}]"""
        
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
        """Print final summary with smart routing statistics"""
        
        total_dishes = sum(len(m["items"]) for m in self.menus.values())
        
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY - SMART ROUTING RESULTS")
        print("=" * 60)
        print(f"✅ Restaurants scraped: {len(self.menus)}/{len(self.restaurants)}")
        print(f"🍽️ Total dishes found: {total_dishes}")
        
        # Success rate
        success_rate = (len(self.menus) / len(self.restaurants) * 100) if self.restaurants else 0
        print(f"📈 Overall success rate: {success_rate:.1f}%")
        
        # Smart routing statistics
        stats = self.scraping_stats
        total_attempts = stats["traditional_success"] + stats["traditional_failed"] + stats["screenshot_success"] + stats["screenshot_failed"]
        
        if total_attempts > 0:
            print(f"\n🔧 SCRAPING METHOD BREAKDOWN:")
            print(f"   Traditional scraping:")
            print(f"      ✅ Success: {stats['traditional_success']}")
            print(f"      ❌ Failed:  {stats['traditional_failed']}")
            if stats['traditional_success'] + stats['traditional_failed'] > 0:
                trad_rate = stats['traditional_success'] / (stats['traditional_success'] + stats['traditional_failed']) * 100
                print(f"      📊 Success rate: {trad_rate:.1f}%")
            
            print(f"   Screenshot fallback:")
            print(f"      ✅ Success: {stats['screenshot_success']}")
            print(f"      ❌ Failed:  {stats['screenshot_failed']}")
            if stats['screenshot_success'] + stats['screenshot_failed'] > 0:
                screen_rate = stats['screenshot_success'] / (stats['screenshot_success'] + stats['screenshot_failed']) * 100
                print(f"      📊 Success rate: {screen_rate:.1f}%")
        
        # Cost breakdown
        print(f"\n💰 COST ANALYSIS:")
        print(f"   Total cost this run: ${stats['total_cost']:.3f}")
        print(f"   Average per restaurant: ${stats['total_cost']/max(len(self.menus), 1):.3f}")
        
        # Method breakdown in results
        traditional_count = len([m for m in self.menus.values() if m.get("method") == "traditional"])
        screenshot_count = len([m for m in self.menus.values() if m.get("method") == "screenshot"])
        
        print(f"\n📊 RESULTS BY METHOD:")
        print(f"   Traditional scraping: {traditional_count} restaurants")
        print(f"   Screenshot fallback: {screenshot_count} restaurants")
        
        # Known problem sites
        problem_sites = [m for m in self.menus.values() if m.get("config", {}).get("requires_screenshot")]
        print(f"\n⚠️  Known problem sites handled: {len(problem_sites)}")
        for menu in problem_sites:
            print(f"   - {menu['restaurant']} ({menu['method']})")
        
        print(f"\n📁 Results saved to data/")
        
        # Monthly cost projection
        monthly_cost = stats['total_cost'] * 4.33  # Average weeks per month
        print(f"🔮 Projected monthly cost: ${monthly_cost:.2f}")
    
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
    import sys
    
    # Check for --force flag
    force_all = "--force" in sys.argv or "-f" in sys.argv
    
    scraper = UnifiedLunchScraper()
    await scraper.run_full_pipeline(force_all)

if __name__ == "__main__":
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Show usage if help requested
    import sys
    if "--help" in sys.argv or "-h" in sys.argv:
        print("IST Lunch Unified Scraper")
        print("Usage:")
        print("  python unified_scraper.py           # Normal mode (respects schedule)")
        print("  python unified_scraper.py --force   # Force mode (scrape all restaurants)")
        print("  python unified_scraper.py -f        # Same as --force")
        exit(0)
    
    # Run the pipeline
    asyncio.run(main())