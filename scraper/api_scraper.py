"""
Practical Lunch Scraper - Keep It Simple
Based on what actually worked in your tests
"""

import asyncio
import aiohttp
import json
import os
import re
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import openai

load_dotenv()

class SimpleScraper:
    """Simple scraper that actually works"""
    
    def __init__(self):
        self.api_key = os.getenv("SCRAPERAPI_KEY")
        if not self.api_key:
            raise ValueError("Need SCRAPERAPI_KEY in .env")
        
    async def scrape(self, url: str) -> str:
        """Simple scraping with reasonable timeout"""
        
        params = {
            'api_key': self.api_key,
            'url': url,
            'render': 'true',  # Handle JavaScript
            'country_code': 'se'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                # 30 second timeout is usually enough
                async with session.get(
                    "http://api.scraperapi.com",
                    params=params,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        return await response.text()
            except:
                pass
        return ""

class PracticalExtractor:
    """Extract menus without overcomplicating"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.ai_available = True
        else:
            self.ai_available = False
    
    def clean_html_gently(self, html: str) -> str:
        """
        Gentle HTML cleaning - keep the content!
        Don't remove nav, header, main, section, article
        """
        
        if not html:
            return ""
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Only remove truly useless elements
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            
            # Get ALL text - don't be picky
            text = soup.get_text(separator='\n')
            
            # Basic cleanup
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(line for line in lines if line)
            
            return text
            
        except:
            # If parsing fails, just do basic cleanup
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            return text
    
    async def extract_menu_items(self, html: str, restaurant: Dict) -> List[Dict]:
        """
        Simple extraction with GPT-4o-mini
        No patterns, no complexity, just ask for menu items
        """
        
        if not self.ai_available or not html:
            return []
        
        # Clean gently
        text = self.clean_html_gently(html)
        
        # Make sure we have content
        if len(text) < 200:
            print(f"    ⚠️ Only {len(text)} chars after cleaning")
            return []
        
        # Use more content for better context
        text = text[:8000]  # 8K chars should be plenty
        
        # Simple, direct prompt
        prompt = f"""Extract lunch menu items from this restaurant website.

Restaurant: {restaurant['name']}
Type: {restaurant.get('type', 'Restaurant')}

Find ALL lunch dishes with these patterns:
- Daily specials (dagens lunch, dagens rätt)
- Weekly menus (veckans lunch)
- Lunch combos (lunch combo, combo meal)
- Buffets (lunch buffé)
- Regular dishes with lunch pricing (95-165 kr typically)

Text from website:
{text}

Return ONLY a JSON array of actual food dishes:
[{{"name": "Orange Chicken & Thai Tofu", "price": 122, "category": "Asiatiskt"}}]

Categories: Kött, Kyckling, Fisk, Vegetarisk, Vegansk, Pizza, Pasta, Asiatiskt, Sallad, Soppa, Buffet

Rules:
- Include dish name, price (or 145 if not shown), specific category
- Exclude drinks, sides, desserts
- Maximum 15 items
- JSON array only, no explanations"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Cheap and effective
                messages=[
                    {"role": "system", "content": "Extract menu items. Return only JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            result = response.choices[0].message.content.strip()
            result = result.replace('```json', '').replace('```', '').strip()
            
            if result.startswith('['):
                items = json.loads(result)
                
                # Basic validation
                valid_items = []
                for item in items[:15]:  # Max 15 items
                    if isinstance(item, dict) and item.get('name'):
                        name = str(item['name']).strip()
                        
                        # Skip obvious non-menu items
                        if len(name) < 3 or name.startswith('#'):
                            continue
                        
                        valid_items.append({
                            'name': name[:100],  # Limit length
                            'price': min(max(int(item.get('price', 145)), 50), 300),
                            'category': item.get('category', 'Dagens rätt')
                        })
                
                return valid_items
                
        except Exception as e:
            print(f"    ❌ AI error: {str(e)[:50]}")
        
        return []

async def process_restaurant(scraper: SimpleScraper, extractor: PracticalExtractor, restaurant: Dict) -> Dict:
    """Process one restaurant simply and effectively"""
    
    print(f"\n📍 {restaurant['name']}")
    
    result = {
        'name': restaurant['name'],
        'type': restaurant.get('type', 'Restaurant'),
        'website': restaurant.get('website', ''),
        'address': restaurant.get('address', ''),
        'items': []
    }
    
    if not restaurant.get('website'):
        print("    ⚠️ No website")
        return result
    
    # Try primary URL
    urls_to_try = [restaurant['website']]
    
    # Add common lunch page URLs
    base_url = restaurant['website'].rstrip('/')
    urls_to_try.extend([
        f"{base_url}/lunch",
        f"{base_url}/meny",
        f"{base_url}/dagens-lunch",
        f"{base_url}/menu"
    ])
    
    # Try up to 3 URLs
    for i, url in enumerate(urls_to_try[:3]):
        print(f"    Trying: {url}")
        html = await scraper.scrape(url)
        
        if html and len(html) > 1000:
            print(f"    ✓ Got {len(html):,} chars")
            
            # Extract menu items
            items = await extractor.extract_menu_items(html, restaurant)
            
            if items:
                result['items'] = items
                result['scraped_url'] = url
                print(f"    ✅ Found {len(items)} items")
                
                # Show first 3 items
                for item in items[:3]:
                    print(f"      • {item['name'][:40]}: {item['price']} kr ({item['category']})")
                if len(items) > 3:
                    print(f"      ... and {len(items)-3} more")
                
                break  # Success, stop trying URLs
        
        if i < len(urls_to_try) - 1:
            await asyncio.sleep(0.5)  # Small delay between attempts
    
    if not result['items']:
        print("    ⚠️ No menu items found")
    
    return result

async def main():
    """Main function - simple and practical"""
    
    print("🍽️ Practical Lunch Scraper")
    print("=" * 50)
    
    # Check requirements
    if not os.getenv("SCRAPERAPI_KEY"):
        print("❌ Need SCRAPERAPI_KEY in .env")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OpenAI key missing - won't extract menus")
        return
    
    # Load restaurants
    try:
        with open('restaurants_lunch.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        print("❌ Can't load restaurants_lunch.json")
        return
    
    # Initialize
    scraper = SimpleScraper()
    extractor = PracticalExtractor()
    
    # Process restaurants
    restaurants = data['restaurants'][:15]  # Start with 15
    results = []
    
    print(f"\n🔄 Processing {len(restaurants)} restaurants...")
    print("-" * 50)
    
    for i, restaurant in enumerate(restaurants, 1):
        print(f"\n[{i}/{len(restaurants)}]", end="")
        result = await process_restaurant(scraper, extractor, restaurant)
        results.append(result)
        
        # Rate limiting
        if i < len(restaurants):
            await asyncio.sleep(2)
    
    # Results
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("-" * 50)
    
    successful = [r for r in results if r['items']]
    total_items = sum(len(r['items']) for r in results)
    
    print(f"✅ Success rate: {len(successful)}/{len(results)} ({len(successful)*100//len(results)}%)")
    print(f"📝 Total dishes found: {total_items}")
    
    if successful:
        print(f"📊 Average dishes/restaurant: {total_items/len(successful):.1f}")
    
    # Save results
    os.makedirs('data', exist_ok=True)
    
    # Save for frontend (dishes first!)
    all_dishes = []
    for r in successful:
        for item in r['items']:
            dish = {
                **item,
                'restaurant': r['name'],
                'restaurant_type': r.get('type', 'Restaurant'),
                'address': r.get('address', ''),
                'website': r.get('website', '')
            }
            all_dishes.append(dish)
    
    # Sort by category then price
    all_dishes.sort(key=lambda x: (x['category'], x['price']))
    
    output = {
        'generated_at': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_dishes': len(all_dishes),
        'total_restaurants': len(successful),
        'dishes': all_dishes,
        'restaurants': successful
    }
    
    with open('data/lunch_dishes.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved {len(all_dishes)} dishes to data/lunch_dishes.json")
    
    # Show failed restaurants
    failed = [r['name'] for r in results if not r['items']]
    if failed:
        print(f"\n⚠️ Failed restaurants ({len(failed)}):")
        for name in failed[:5]:
            print(f"  • {name}")
    
    # Cost estimate
    print(f"\n💰 Estimated cost:")
    print(f"  • ScraperAPI: ~{len(restaurants) * 2} credits")
    print(f"  • OpenAI: ~${len(restaurants) * 0.002:.2f}")
    
    print("\n✨ Done! Your lunch dishes are ready!")

if __name__ == "__main__":
    asyncio.run(main())