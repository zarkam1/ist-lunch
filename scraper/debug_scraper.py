"""
Debug scraper to identify why traditional scraping fails
Logs URLs, response codes, and content samples
"""

import os
import json
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time

load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPERAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Test restaurants with known good menus
TEST_RESTAURANTS = [
    {
        "name": "The Public",
        "base_url": "https://sundbyberg.thepublic.se",
        "possible_paths": ["/", "/lunch", "/meny", "/dagens-lunch"]
    },
    {
        "name": "Restaurang S",
        "base_url": "http://www.restaurangs.nu",
        "possible_paths": ["/", "/lunch", "/meny", "/veckans-lunch"]
    },
    {
        "name": "KRUBB Burgers",
        "base_url": "https://krubbburgers.se",
        "possible_paths": ["/", "/meny", "/lunch"]
    },
    {
        "name": "Ristorante Rustico",
        "base_url": "http://www.ristoranterustico.se",
        "possible_paths": ["/", "/meny", "/lunch", "/lunchmeny"]
    },
    {
        "name": "Tre Bröder",
        "base_url": "http://www.3broder.com",
        "possible_paths": ["/", "/lunch", "/meny"]
    }
]

def debug_scraper():
    """Debug why traditional scraping fails"""
    
    print("🔍 SCRAPER DEBUG MODE")
    print("=" * 80)
    print(f"ScraperAPI Key: {'✅ Found' if SCRAPER_API_KEY else '❌ Missing'}")
    print(f"OpenAI Key: {'✅ Found' if OPENAI_API_KEY else '❌ Missing'}")
    print("=" * 80)
    
    results = []
    
    for restaurant in TEST_RESTAURANTS:
        print(f"\n🍽️ Testing: {restaurant['name']}")
        print("-" * 60)
        
        restaurant_result = {
            "name": restaurant["name"],
            "base_url": restaurant["base_url"],
            "attempts": []
        }
        
        for path in restaurant["possible_paths"]:
            full_url = restaurant["base_url"] + path if path != "/" else restaurant["base_url"]
            
            print(f"\n📍 Trying URL: {full_url}")
            
            attempt = {
                "url": full_url,
                "method": "traditional",
                "status_code": None,
                "content_length": 0,
                "menu_keywords_found": [],
                "error": None,
                "sample_content": ""
            }
            
            # Method 1: Direct request (baseline)
            try:
                print("   Method 1: Direct request...")
                direct_response = requests.get(full_url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                print(f"   → Status: {direct_response.status_code}")
                
                if direct_response.status_code == 200:
                    content = direct_response.text
                    check_content(content, "Direct", attempt)
            except Exception as e:
                print(f"   → Failed: {str(e)[:50]}")
            
            # Method 2: ScraperAPI without JS
            try:
                print("   Method 2: ScraperAPI (no JS)...")
                params = {
                    'api_key': SCRAPER_API_KEY,
                    'url': full_url,
                    'country_code': 'se'
                }
                scraper_response = requests.get(
                    'http://api.scraperapi.com',
                    params=params,
                    timeout=15
                )
                print(f"   → Status: {scraper_response.status_code}")
                attempt["status_code"] = scraper_response.status_code
                
                if scraper_response.status_code == 200:
                    content = scraper_response.text
                    attempt["content_length"] = len(content)
                    check_content(content, "ScraperAPI-NoJS", attempt)
            except Exception as e:
                print(f"   → Failed: {str(e)[:50]}")
                attempt["error"] = str(e)[:100]
            
            # Method 3: ScraperAPI with JS rendering
            try:
                print("   Method 3: ScraperAPI (with JS)...")
                params = {
                    'api_key': SCRAPER_API_KEY,
                    'url': full_url,
                    'render': 'true',  # Enable JavaScript
                    'country_code': 'se',
                    'wait_for_selector': '.menu, .lunch, main, #menu, #lunch'
                }
                js_response = requests.get(
                    'http://api.scraperapi.com',
                    params=params,
                    timeout=30
                )
                print(f"   → Status: {js_response.status_code}")
                
                if js_response.status_code == 200:
                    content = js_response.text
                    attempt["content_length"] = len(content)
                    check_content(content, "ScraperAPI-JS", attempt)
                    
                    # Save a sample for inspection
                    if "lunch" in content.lower() or "dagens" in content.lower():
                        sample_file = f"debug/{restaurant['name'].replace(' ', '_')}_{path.replace('/', '_')}.html"
                        os.makedirs("debug", exist_ok=True)
                        with open(sample_file, "w", encoding="utf-8") as f:
                            f.write(content[:50000])  # First 50KB
                        print(f"   💾 Saved sample to {sample_file}")
            except Exception as e:
                print(f"   → Failed: {str(e)[:50]}")
                attempt["error"] = str(e)[:100]
            
            restaurant_result["attempts"].append(attempt)
            
            # If we found menu content, no need to try other paths
            if attempt["menu_keywords_found"] and len(attempt["menu_keywords_found"]) >= 3:
                print("   ✅ Found menu content! No need to try other URLs.")
                break
            
            time.sleep(1)  # Be nice to servers
        
        results.append(restaurant_result)
    
    # Save debug results
    with open("scraper_debug_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print_summary(results)
    suggest_fixes(results)

def check_content(html: str, method: str, attempt: dict):
    """Check if HTML contains menu content"""
    
    # Menu keywords to look for
    swedish_keywords = [
        "dagens", "lunch", "meny", "veckan", "måndag", "tisdag",
        "onsdag", "torsdag", "fredag", "rätt", "kr", "sek",
        "välj", "ingår", "serveras", "inkl", "pris"
    ]
    
    food_keywords = [
        "kött", "fisk", "kyckling", "pasta", "pizza", "sallad",
        "vegetarisk", "vegan", "soppa", "burger", "räkor",
        "lax", "biff", "fläsk", "nöt"
    ]
    
    content_lower = html.lower()
    found_keywords = []
    
    # Check for keywords
    for keyword in swedish_keywords + food_keywords:
        if keyword in content_lower:
            count = content_lower.count(keyword)
            if count > 1:  # Multiple mentions = likely real menu
                found_keywords.append(f"{keyword}({count})")
    
    attempt["menu_keywords_found"] = found_keywords
    
    # Check for price patterns (50-200 kr range)
    import re
    price_pattern = r'\b(5[0-9]|[6-9][0-9]|1[0-9][0-9]|200)\s*(kr|:-|sek)?'
    prices = re.findall(price_pattern, content_lower)
    if prices:
        attempt["menu_keywords_found"].append(f"prices({len(prices)})")
    
    # Extract sample of actual menu text if found
    if found_keywords:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for menu containers
        menu_selectors = [
            'div.menu', 'div.lunch', 'section.menu', 'main',
            'div[class*="lunch"]', 'div[class*="menu"]',
            'div[id*="lunch"]', 'div[id*="menu"]'
        ]
        
        for selector in menu_selectors:
            elements = soup.select(selector)
            if elements:
                text = elements[0].get_text()[:500]
                if any(kw in text.lower() for kw in ["lunch", "dagens", "meny"]):
                    attempt["sample_content"] = text.strip()[:200]
                    break
    
    print(f"   → Found keywords: {', '.join(found_keywords[:5]) if found_keywords else 'None'}")

def print_summary(results):
    """Print summary of debug results"""
    
    print("\n" + "=" * 80)
    print("📊 DEBUG SUMMARY")
    print("=" * 80)
    
    working_traditional = 0
    need_js = 0
    need_screenshot = 0
    
    for restaurant in results:
        success = False
        needs_js = False
        
        for attempt in restaurant["attempts"]:
            if len(attempt["menu_keywords_found"]) >= 3:
                if "ScraperAPI-NoJS" in str(attempt):
                    working_traditional += 1
                    success = True
                    break
                elif "ScraperAPI-JS" in str(attempt):
                    needs_js = True
        
        if needs_js:
            need_js += 1
        elif not success:
            need_screenshot += 1
        
        # Print restaurant status
        status = "✅ Traditional" if success and not needs_js else "⚠️ Needs JS" if needs_js else "❌ Needs Screenshot"
        print(f"\n{restaurant['name']}: {status}")
        
        best_url = None
        for attempt in restaurant["attempts"]:
            if attempt["menu_keywords_found"]:
                best_url = attempt["url"]
                print(f"  Best URL: {best_url}")
                print(f"  Keywords: {', '.join(attempt['menu_keywords_found'][:5])}")
                break
    
    print(f"\n📈 Results:")
    print(f"  Traditional scraping works: {working_traditional}/{len(results)}")
    print(f"  Needs JavaScript rendering: {need_js}/{len(results)}")
    print(f"  Needs screenshot fallback: {need_screenshot}/{len(results)}")

def suggest_fixes(results):
    """Suggest optimizations based on debug results"""
    
    print("\n" + "=" * 80)
    print("💡 RECOMMENDED OPTIMIZATIONS")
    print("=" * 80)
    
    # Build restaurant-specific config
    config = {}
    
    for restaurant in results:
        name_id = restaurant["name"].lower().replace(" ", "-")
        
        best_attempt = None
        for attempt in restaurant["attempts"]:
            if attempt["menu_keywords_found"] and len(attempt["menu_keywords_found"]) >= 3:
                best_attempt = attempt
                break
        
        if best_attempt:
            config[name_id] = {
                "url": best_attempt["url"],
                "needs_js": "JS" in str(best_attempt.get("method", "")),
                "selectors": ".menu, .lunch, main"  # Can be refined
            }
    
    print("\nOptimized configuration for your restaurants:")
    print("```python")
    print("RESTAURANT_SCRAPING_CONFIG = {")
    for name, cfg in config.items():
        print(f'    "{name}": {{')
        print(f'        "url": "{cfg["url"]}",')
        print(f'        "needs_js": {cfg["needs_js"]},')
        print(f'        "method": "{"scraper_js" if cfg["needs_js"] else "scraper_simple"}"')
        print(f'    }},')
    print("}")
    print("```")
    
    print("\nCost optimization:")
    print("- Use simple scraping (no JS) where possible: ~$0.001/request")
    print("- Use JS rendering only when needed: ~$0.002/request")
    print("- Screenshot only as last resort: ~$0.10/request")

if __name__ == "__main__":
    debug_scraper()