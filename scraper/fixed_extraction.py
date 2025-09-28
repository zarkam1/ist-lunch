"""
Fixed extraction scraper - Traditional scraping DOES work!
The HTML is there, we just need better extraction logic
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import openai
import re

load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPERAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class FixedMenuExtractor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    def scrape_restaurant(self, name: str, url: str) -> dict:
        """Scrape a restaurant with proper extraction"""
        
        print(f"\n🍽️ Scraping: {name}")
        print(f"📍 URL: {url}")
        
        # Step 1: Fetch HTML (we know this works!)
        html = self.fetch_html(url)
        if not html:
            return None
        
        # Step 2: Pre-process with BeautifulSoup
        menu_text = self.extract_menu_text(html)
        print(f"   📄 Extracted {len(menu_text)} chars of menu text")
        
        # Step 3: Use AI to structure the data
        if menu_text and len(menu_text) > 100:
            items = self.extract_with_ai(menu_text, name)
            if items:
                print(f"   ✅ Found {len(items)} menu items!")
                return {
                    "restaurant": name,
                    "url": url,
                    "items": items,
                    "method": "traditional"
                }
        
        print(f"   ❌ AI extraction failed - falling back to pattern matching")
        
        # Step 4: Fallback to pattern matching
        items = self.extract_with_patterns(menu_text)
        if items:
            print(f"   ✅ Pattern matching found {len(items)} items")
            return {
                "restaurant": name,
                "url": url,
                "items": items,
                "method": "pattern"
            }
        
        return None
    
    def fetch_html(self, url: str) -> str:
        """Fetch HTML - we know this works from debug!"""
        
        # Try direct first (worked for all in debug)
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if response.status_code == 200:
                print(f"   ✅ Direct fetch successful ({len(response.text)} bytes)")
                return response.text
        except:
            pass
        
        # Fallback to ScraperAPI (without JS since that had connection issues)
        try:
            params = {
                'api_key': SCRAPER_API_KEY,
                'url': url,
                'country_code': 'se'
            }
            response = requests.get('http://api.scraperapi.com', params=params, timeout=15)
            if response.status_code == 200:
                print(f"   ✅ ScraperAPI fetch successful ({len(response.text)} bytes)")
                return response.text
        except Exception as e:
            print(f"   ❌ Fetch failed: {str(e)[:50]}")
        
        return None
    
    def extract_menu_text(self, html: str) -> str:
        """Extract relevant menu text from HTML"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Look for menu sections
        menu_text = ""
        
        # Strategy 1: Find elements with menu-related classes/ids
        menu_selectors = [
            'div[class*="lunch"]', 'div[class*="menu"]', 'div[class*="meny"]',
            'section[class*="lunch"]', 'section[class*="menu"]',
            'div[id*="lunch"]', 'div[id*="menu"]',
            'main', 'article', '.content', '#content'
        ]
        
        for selector in menu_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text()
                if any(kw in text.lower() for kw in ['lunch', 'dagens', 'meny', 'måndag', 'kr']):
                    menu_text += text + "\n"
                    if len(menu_text) > 1000:  # Enough content
                        break
        
        # Strategy 2: If not enough content, get all text
        if len(menu_text) < 500:
            menu_text = soup.get_text()
        
        # Clean up
        menu_text = re.sub(r'\s+', ' ', menu_text)
        menu_text = re.sub(r'\n{3,}', '\n\n', menu_text)
        
        return menu_text[:8000]  # Limit for AI
    
    def extract_with_ai(self, text: str, restaurant: str) -> list:
        """Extract menu items using GPT-4o-mini"""
        
        # Simpler, more focused prompt
        prompt = f"""Extract lunch menu items from this Swedish restaurant text.

Restaurant: {restaurant}

Look for dishes with prices in the 50-200 kr range.
Common patterns:
- "Dish name ... 89 kr"
- "Måndag: Pasta Carbonara"
- "Dagens lunch: Köttbullar med potatismos"

Return a JSON array with these fields:
- name: dish name (required)
- price: number between 50-200 (required) 
- description: ingredients if mentioned (optional)
- day: weekday if specified (optional)

Example output:
[
  {{"name": "Pasta Carbonara", "price": 115, "day": "måndag"}},
  {{"name": "Köttbullar", "price": 109, "description": "med potatismos och lingon"}}
]

Text to analyze:
{text[:4000]}

Return ONLY the JSON array, no explanation."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            result = result.replace('```json', '').replace('```', '').strip()
            
            if result.startswith('['):
                items = json.loads(result)
                # Filter valid items
                valid_items = []
                for item in items:
                    if item.get('name') and 40 <= item.get('price', 0) <= 250:
                        valid_items.append(item)
                return valid_items
        except Exception as e:
            print(f"   AI extraction error: {str(e)[:50]}")
        
        return []
    
    def extract_with_patterns(self, text: str) -> list:
        """Fallback: Extract using regex patterns"""
        
        items = []
        
        # Pattern 1: "Dish name ... 99 kr"
        pattern1 = r'([A-ZÅÄÖ][^.!?]*?)\s+(\d{2,3})\s*(?:kr|:-|SEK)'
        matches = re.findall(pattern1, text)
        
        for match in matches:
            name = match[0].strip()
            price = int(match[1])
            
            if 50 <= price <= 200 and len(name) > 5:
                items.append({
                    "name": name,
                    "price": price,
                    "method": "pattern"
                })
        
        # Pattern 2: Weekday menus
        days = ['måndag', 'tisdag', 'onsdag', 'torsdag', 'fredag']
        for day in days:
            day_pattern = f'{day}[:\s]+([^.!?\n]+)'
            day_matches = re.findall(day_pattern, text.lower())
            for match in day_matches:
                if len(match) > 10:
                    items.append({
                        "name": match.strip().title(),
                        "price": 110,  # Default lunch price
                        "day": day
                    })
        
        # Deduplicate
        seen = set()
        unique_items = []
        for item in items:
            key = item['name'].lower()[:20]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items[:30]  # Max 30 items

def test_fixed_scraper():
    """Test the fixed scraper on restaurants we know have menus"""
    
    extractor = FixedMenuExtractor()
    
    # Test restaurants from debug that had good keyword matches
    test_restaurants = [
        {
            "name": "The Public",
            "url": "https://sundbyberg.thepublic.se"
        },
        {
            "name": "Restaurang S", 
            "url": "http://www.restaurangs.nu"
        },
        {
            "name": "KRUBB Burgers",
            "url": "https://krubbburgers.se"  
        },
        {
            "name": "Ristorante Rustico",
            "url": "http://www.ristoranterustico.se"
        }
    ]
    
    results = []
    total_items = 0
    
    print("🚀 TESTING FIXED EXTRACTION")
    print("=" * 60)
    
    for restaurant in test_restaurants:
        result = extractor.scrape_restaurant(restaurant["name"], restaurant["url"])
        
        if result:
            results.append(result)
            total_items += len(result["items"])
            
            # Show sample items
            print(f"\n   📋 Sample items:")
            for item in result["items"][:3]:
                price = item.get('price', '?')
                day = f" ({item['day']})" if item.get('day') else ""
                print(f"      • {item['name']}{day} - {price} kr")
    
    # Save results
    with open("fixed_extraction_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully scraped {len(results)}/{len(test_restaurants)} restaurants")
    print(f"🍽️ Total items extracted: {total_items}")
    print(f"💰 Cost: ~${len(test_restaurants) * 0.002:.3f} (vs ${len(test_restaurants) * 0.10:.2f} for screenshots)")
    print(f"📁 Saved to fixed_extraction_results.json")
    
    # Show which method worked
    for result in results:
        method = result.get("method", "unknown")
        items = len(result["items"])
        print(f"\n{result['restaurant']}: {items} items via {method}")

if __name__ == "__main__":
    test_fixed_scraper()