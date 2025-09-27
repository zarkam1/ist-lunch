"""
Screenshot Fallback Scraper with GPT-4 Vision
For restaurants where traditional scraping fails
"""

import asyncio
import base64
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import openai

load_dotenv()

class ScreenshotScraper:
    """Take screenshots of restaurant websites for vision analysis"""
    
    def __init__(self):
        self.screenshots_dir = "data/screenshots"
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    async def capture_menu_screenshots(self, restaurant: Dict) -> List[str]:
        """Navigate to restaurant site and capture menu screenshots"""
        
        screenshots = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='sv-SE'
            )
            page = await context.new_page()
            
            try:
                # Navigate to main page
                url = restaurant['website']
                print(f"    📸 Navigating to {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(2000)  # Let JS render
                
                # Try to find and click menu/lunch links
                menu_clicked = False
                for link_text in ['Meny', 'Lunch', 'Dagens lunch', 'Menu', 'Mat']:
                    try:
                        # Try clicking menu link
                        await page.click(f'text=/{link_text}/i', timeout=3000)
                        await page.wait_for_timeout(2000)
                        menu_clicked = True
                        print(f"    ✓ Clicked on '{link_text}' link")
                        break
                    except:
                        continue
                
                # Scroll to load lazy content
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                await page.wait_for_timeout(1000)
                
                # Take main screenshot
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_name = restaurant['name'].replace(' ', '_')[:30]
                
                # Full page screenshot
                screenshot_path = f"{self.screenshots_dir}/{safe_name}_{timestamp}_full.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                screenshots.append(screenshot_path)
                print(f"    📸 Captured full page screenshot")
                
                # Also capture specific menu areas if found
                menu_selectors = [
                    '.menu', '.lunch', '.dagens', 
                    '[class*="menu"]', '[id*="menu"]',
                    'main', 'article', '.content'
                ]
                
                for selector in menu_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            bbox = await element.bounding_box()
                            if bbox and bbox['height'] > 100:  # Meaningful content
                                focused_path = f"{self.screenshots_dir}/{safe_name}_{timestamp}_menu.png"
                                await element.screenshot(path=focused_path)
                                screenshots.append(focused_path)
                                print(f"    📸 Captured menu section")
                                break
                    except:
                        continue
                
                # Try menu-specific URLs if main page didn't work
                if not menu_clicked:
                    menu_urls = [
                        f"{url.rstrip('/')}/meny",
                        f"{url.rstrip('/')}/lunch",
                        f"{url.rstrip('/')}/dagens-lunch"
                    ]
                    
                    for menu_url in menu_urls:
                        try:
                            await page.goto(menu_url, wait_until='networkidle', timeout=15000)
                            await page.wait_for_timeout(2000)
                            
                            menu_screenshot = f"{self.screenshots_dir}/{safe_name}_{timestamp}_menu_page.png"
                            await page.screenshot(path=menu_screenshot, full_page=True)
                            screenshots.append(menu_screenshot)
                            print(f"    📸 Found menu at {menu_url}")
                            break
                        except:
                            continue
                
            except Exception as e:
                print(f"    ❌ Screenshot error: {str(e)[:50]}")
            
            finally:
                await browser.close()
        
        return screenshots

class VisionAnalyzer:
    """Use GPT-4 Vision to extract menu from screenshots"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.available = True
        else:
            self.available = False
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def analyze_screenshot(self, image_path: str, restaurant: Dict) -> List[Dict]:
        """Use GPT-4 Vision to extract menu items from screenshot"""
        
        if not self.available or not os.path.exists(image_path):
            return []
        
        print(f"    🔍 Analyzing screenshot with GPT-4 Vision...")
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Restaurant-specific hints
        hints = ""
        if 'chopchop' in restaurant['name'].lower():
            hints = "This is ChopChop - look for Mix & Match, wok dishes, sushi"
        elif 'pizza' in restaurant['name'].lower():
            hints = "This is a pizza place - look for pizza varieties"
        
        prompt = f"""Analyze this restaurant menu screenshot and extract lunch items.

Restaurant: {restaurant['name']}
Location: Sundbyberg, Stockholm
{hints}

Extract ALL menu items visible that could be ordered for lunch, including:
- Dish names (in Swedish or English)
- Prices in SEK (usually 50-200 kr for lunch)
- Categories

Return a JSON array with found items:
[{{"name": "Dish name", "price": 145, "category": "Category"}}]

Categories to use: Kött, Kyckling, Fisk, Vegetarisk, Vegansk, Pizza, Pasta, Asiatiskt, Sushi, Sallad, Soppa, Buffet

Important:
- Include ANY dishes visible, not just "lunch specials"
- Look for prices like "145:-" or "145 kr" or just "145"
- If you see weekday menus (måndag, tisdag, etc), include those
- Maximum 20 items
- If no clear menu items visible, return empty array []"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"  # High detail for menu text
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            result = response.choices[0].message.content.strip()
            result = result.replace('```json', '').replace('```', '').strip()
            
            if result.startswith('['):
                items = json.loads(result)
                
                # Validate items
                valid_items = []
                for item in items[:20]:
                    if isinstance(item, dict) and item.get('name'):
                        valid_items.append({
                            'name': str(item['name'])[:100],
                            'price': min(max(int(item.get('price', 145)), 50), 300),
                            'category': item.get('category', 'Dagens rätt')
                        })
                
                return valid_items
                
        except Exception as e:
            print(f"    ❌ Vision analysis error: {str(e)[:100]}")
        
        return []

class HybridScraper:
    """Combine traditional scraping with screenshot fallback"""
    
    def __init__(self):
        self.screenshot_scraper = ScreenshotScraper()
        self.vision_analyzer = VisionAnalyzer()
        
        # Try to import your existing scraper
        try:
            from practical_scraper import PracticalExtractor, SimpleScraper
            self.traditional_scraper = SimpleScraper()
            self.traditional_extractor = PracticalExtractor()
            self.traditional_available = True
        except:
            self.traditional_available = False
    
    async def scrape_restaurant(self, restaurant: Dict) -> Dict:
        """Try traditional scraping first, fall back to screenshots"""
        
        print(f"\n📍 {restaurant['name']}")
        
        result = {
            **restaurant,
            'items': [],
            'method': None,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Step 1: Try traditional scraping
        if self.traditional_available:
            print("    🔄 Trying traditional scraping...")
            html = await self.traditional_scraper.scrape(restaurant['website'])
            
            if html and len(html) > 2000:
                items = await self.traditional_extractor.extract_menu_items(html, restaurant)
                
                if items and len(items) > 2:  # Meaningful results
                    result['items'] = items
                    result['method'] = 'traditional'
                    print(f"    ✅ Traditional scraping found {len(items)} items")
                    return result
        
        # Step 2: Fall back to screenshots
        print("    📸 Falling back to screenshot method...")
        screenshots = await self.screenshot_scraper.capture_menu_screenshots(restaurant)
        
        if screenshots:
            # Analyze each screenshot
            all_items = []
            for screenshot in screenshots:
                items = await self.vision_analyzer.analyze_screenshot(screenshot, restaurant)
                all_items.extend(items)
            
            # Deduplicate
            seen = set()
            unique_items = []
            for item in all_items:
                key = item['name'].lower()[:50]
                if key not in seen:
                    seen.add(key)
                    unique_items.append(item)
            
            if unique_items:
                result['items'] = unique_items[:20]  # Max 20 items
                result['method'] = 'screenshot'
                result['screenshots'] = screenshots
                print(f"    ✅ Screenshot method found {len(result['items'])} items")
            else:
                print(f"    ⚠️ No menu items found in screenshots")
        
        return result

async def main():
    """Main function with hybrid approach"""
    
    print("🚀 Hybrid Scraper with Screenshot Fallback")
    print("=" * 50)
    
    # Load restaurants (your existing list)
    with open('restaurants_lunch.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Problem restaurants that need screenshots
    problem_restaurants = [
        "ChopChop Asian Express",
        "Bonab - Persisk Restaurang Stockholm",
        "Restaurang Parma",
        "Ristorante Rustico",
        "Piatti"
    ]
    
    # Filter to problem restaurants for testing
    restaurants = [r for r in data['restaurants'] 
                  if r['name'] in problem_restaurants][:3]
    
    scraper = HybridScraper()
    
    if not scraper.vision_analyzer.available:
        print("❌ OpenAI Vision API not available")
        return
    
    results = []
    
    for restaurant in restaurants:
        result = await scraper.scrape_restaurant(restaurant)
        results.append(result)
        await asyncio.sleep(2)  # Rate limiting
    
    # Save results
    os.makedirs('data', exist_ok=True)
    
    successful = [r for r in results if r['items']]
    total_items = sum(len(r['items']) for r in results)
    
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print(f"✅ Success rate: {len(successful)}/{len(results)}")
    print(f"📝 Total dishes: {total_items}")
    
    # Method breakdown
    traditional = len([r for r in results if r.get('method') == 'traditional'])
    screenshot = len([r for r in results if r.get('method') == 'screenshot'])
    print(f"🔄 Traditional: {traditional}")
    print(f"📸 Screenshot: {screenshot}")
    
    # Save enhanced results
    output = {
        'generated_at': datetime.now().isoformat(),
        'restaurants': results,
        'stats': {
            'total': len(results),
            'successful': len(successful),
            'total_items': total_items,
            'methods': {
                'traditional': traditional,
                'screenshot': screenshot
            }
        }
    }
    
    with open('data/screenshot_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Saved to data/screenshot_results.json")
    print("\n✨ Done!")

if __name__ == "__main__":
    # Install: pip install playwright openai python-dotenv
    # playwright install chromium
    asyncio.run(main())