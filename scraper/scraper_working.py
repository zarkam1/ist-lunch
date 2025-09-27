"""
IST Lunch Scraper with ScraperAPI
Handles complex restaurant sites with ease
Free tier: 5000 API credits/month
"""

import asyncio
import aiohttp
import json
import os
import re
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
import openai

load_dotenv()

class ScraperAPIClient:
    """Use ScraperAPI for reliable scraping"""
    
    def __init__(self):
        self.api_key = os.getenv("SCRAPERAPI_KEY")
        if not self.api_key:
            print("⚠️  Get free API key at: https://www.scraperapi.com")
            print("   Add to .env: SCRAPERAPI_KEY=your_key_here")
        
        self.base_url = "http://api.scraperapi.com"
        
    async def scrape_url(self, url: str, render_js: bool = True) -> str:
        """Scrape URL using ScraperAPI"""
        
        if not self.api_key:
            return ""
        
        params = {
            'api_key': self.api_key,
            'url': url,
            'render': str(render_js).lower(),  # Render JavaScript
            'country_code': 'se'  # Swedish IP
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"  ScraperAPI error: {response.status}")
                        return ""
            except Exception as e:
                print(f"  Error: {e}")
                return ""

class MenuExtractor:
    """Extract menu items from scraped content"""
    
    def __init__(self):
        # Initialize OpenAI if available
        api_key = os.getenv("OPENAI_API_KEY")
        self.ai_available = bool(api_key)
        if self.ai_available:
            self.client = openai.OpenAI(api_key=api_key)
    
    def extract_structured_menu(self, content: str, restaurant_name: str) -> List[Dict]:
        """Try to extract menu with Python first"""
        
        items = []
        content_lower = content.lower()
        
        # Quick check for lunch relevance
        if not any(word in content_lower for word in ['lunch', 'dagens', 'meny', 'mat']):
            return []
        
        # Common Swedish menu patterns
        patterns = [
            # Price patterns
            r'([A-ZÅÄÖ][^.:\n]+?)\s+(\d{2,3})\s*(?:kr|:-|SEK)',
            r'([A-ZÅÄÖ][^.:\n]+?)\s*[\.…]+\s*(\d{2,3})',
            # Weekday patterns
            r'(?:måndag|tisdag|onsdag|torsdag|fredag)[:\s]+([^.\n]+?)(?:\s+(\d{2,3}))?',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                
                # Clean name
                name = re.sub(r'\s+', ' ', name)
                name = name.strip(' .,;:•·')
                
                # Skip if too short or too long
                if len(name) < 5 or len(name) > 100:
                    continue
                
                # Get price
                price = None
                if len(match.groups()) > 1 and match.group(2):
                    try:
                        price = int(match.group(2))
                        if price < 80 or price > 250:  # Validate price range
                            continue
                    except:
                        pass
                
                item = {
                    'name': name,
                    'price': price or 145,  # Default lunch price
                    'category': self.detect_category(name)
                }
                
                items.append(item)
        
        # Remove duplicates
        seen = set()
        unique = []
        for item in items:
            key = item['name'].lower()
            if key not in seen and len(key) > 5:
                seen.add(key)
                unique.append(item)
        
        return unique[:10]  # Max 10 items
    
    def detect_category(self, text: str) -> str:
        """Simple category detection"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['vegan', 'vegansk']):
            return 'Vegansk'
        elif any(w in text_lower for w in ['fisk', 'lax', 'torsk', 'räkor']):
            return 'Fisk'
        elif any(w in text_lower for w in ['kyckling', 'biff', 'fläsk', 'kött']):
            return 'Kött'
        elif any(w in text_lower for w in ['vegetarisk', 'halloumi']):
            return 'Vegetarisk'
        else:
            return 'Övrigt'
    
    async def extract_with_ai(self, content: str, restaurant_name: str) -> List[Dict]:
        """Use AI for complex menus"""
        
        if not self.ai_available or len(content) < 200:
            return []
        
        # Limit content
        content = content[:2500]
        
        prompt = f"""
        Extract lunch items from {restaurant_name}.
        Return JSON array (max 5 items):
        [{{"name": "dish", "price": 145, "category": "Kött"}}]
        
        Text: {content}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract lunch. Only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('['):
                return json.loads(result)
        except:
            pass
        
        return []

async def process_restaurant(scraper: ScraperAPIClient, extractor: MenuExtractor, restaurant: Dict) -> Dict:
    """Process single restaurant"""
    
    result = {
        'name': restaurant['name'],
        'website': restaurant.get('website', ''),
        'items': [],
        'method': 'NONE'
    }
    
    if not restaurant.get('website'):
        return result
    
    print(f"📍 {restaurant['name']}")
    
    # Scrape with ScraperAPI
    content = await scraper.scrape_url(restaurant['website'])
    
    if not content:
        print(f"  ❌ Scraping failed")
        return result
    
    print(f"  ✓ Scraped {len(content)} chars")
    
    # Try Python extraction first
    items = extractor.extract_structured_menu(content, restaurant['name'])
    
    if items:
        result['items'] = items
        result['method'] = 'PYTHON'
        print(f"  ✓ Found {len(items)} items with Python")
    else:
        # Try AI if available
        items = await extractor.extract_with_ai(content, restaurant['name'])
        if items:
            result['items'] = items
            result['method'] = 'AI'
            print(f"  ✓ Found {len(items)} items with AI")
        else:
            print(f"  ⚠️  No menu items found")
    
    # Show sample items
    for item in items[:2]:
        price = f"{item.get('price')} kr" if item.get('price') else "?"
        print(f"    - {item['name']}: {price}")
    
    return result

async def main():
    """Main processing"""
    
    print("🚀 IST Lunch Scraper with ScraperAPI")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("SCRAPERAPI_KEY"):
        print("\n⚠️  ScraperAPI key missing!")
        print("\n📝 Quick Setup:")
        print("1. Go to: https://www.scraperapi.com")
        print("2. Sign up for free account (5000 credits)")
        print("3. Get your API key")
        print("4. Add to .env file:")
        print("   SCRAPERAPI_KEY=your_key_here")
        print("\n💡 Alternative: Use ScrapingBee or HasData")
        return
    
    # Load restaurants
    with open('restaurants_lunch.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    scraper = ScraperAPIClient()
    extractor = MenuExtractor()
    
    results = []
    
    # Test with first 5 restaurants
    test_restaurants = data['restaurants'][:5]
    
    print(f"\n🔍 Processing {len(test_restaurants)} restaurants...\n")
    
    for restaurant in test_restaurants:
        result = await process_restaurant(scraper, extractor, restaurant)
        results.append(result)
        await asyncio.sleep(1)  # Rate limiting
    
    # Statistics
    successful = len([r for r in results if r['items']])
    python_extracted = len([r for r in results if r['method'] == 'PYTHON'])
    ai_extracted = len([r for r in results if r['method'] == 'AI'])
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print(f"  Successful: {successful}/{len(results)}")
    print(f"  Python extraction: {python_extracted}")
    print(f"  AI extraction: {ai_extracted}")
    print(f"  API credits used: ~{len(results)}")
    
    # Save results
    output = {
        'generated_at': datetime.now().isoformat(),
        'restaurants': results,
        'stats': {
            'total': len(results),
            'successful': successful,
            'python': python_extracted,
            'ai': ai_extracted
        }
    }
    
    with open('data/menus.json', 'w', encoding='utf-8') as f:
        os.makedirs('data', exist_ok=True)
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved to data/menus.json")
    print("\n💡 Next: Update frontend to read from data/menus.json")

if __name__ == "__main__":
    # Install if needed: pip install aiohttp
    asyncio.run(main())