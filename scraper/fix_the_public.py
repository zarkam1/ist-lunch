"""
Quick fix to scrape The Public with descriptions using screenshot method
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright
import openai
import base64
from dotenv import load_dotenv

load_dotenv()

async def scrape_the_public_with_descriptions():
    """Scrape The Public specifically with screenshot method for descriptions"""
    
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("📸 Navigating to The Public...")
            await page.goto("https://sundbyberg.thepublic.se/", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # Look for menu or lunch links
            try:
                # Try various selectors for menu
                menu_selectors = [
                    'a[href*="meny"]', 'a[href*="lunch"]', 'a[href*="menu"]',
                    'text=Meny', 'text=Lunch', 'text=Menu', '.menu', '#menu'
                ]
                
                for selector in menu_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"🔗 Found menu link: {selector}")
                        await elements[0].click()
                        await page.wait_for_timeout(2000)
                        break
                        
            except Exception as e:
                print(f"No menu link found, continuing with main page: {e}")
            
            # Take screenshot
            screenshot = await page.screenshot(full_page=True)
            screenshot_b64 = base64.b64encode(screenshot).decode()
            
            print("🤖 Analyzing screenshot with GPT-4 Vision...")
            
            prompt = """You are analyzing a restaurant website screenshot to extract the lunch menu.

CRITICAL: Extract FULL descriptions for each dish, not just names!

Example of what I need:
- Name: "Kalvgryta" 
- Description: "med champinjoner, rotfrukter, örter och madeira serveras med potatismos"
- Price: 149
- Category: "Kött"

For The Public restaurant, look for:
1. Burger descriptions (ingredients, sauces, sides)
2. Pasta descriptions (sauce, protein, accompaniments) 
3. Appetizer descriptions (preparation method, ingredients)
4. Any lunch specials with full details

Return JSON array with FULL descriptions:
[
  {
    "name": "Dish name",
    "description": "Complete description with ingredients and preparation",
    "price": 149,
    "category": "Kött/Fisk/Vegetarisk/Pasta/Pizza"
  }
]

IMPORTANT: Include ALL visible ingredients and preparation details in the description field!"""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            print(f"🍽️ Raw AI response: {result_text}")
            
            # Parse JSON
            import re
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                print(f"✅ Extracted {len(items)} items with descriptions")
                
                # Save results
                result = {
                    "restaurant": "The Public",
                    "url": "https://sundbyberg.thepublic.se/",
                    "method": "screenshot_vision",
                    "items": items,
                    "extraction_date": "2025-09-28"
                }
                
                with open("data/the_public_fixed.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                return result
            else:
                print("❌ No valid JSON found in response")
                return None
                
        except Exception as e:
            print(f"❌ Error scraping The Public: {e}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(scrape_the_public_with_descriptions())
    if result:
        print(f"\n🎉 Successfully extracted {len(result['items'])} dishes:")
        for item in result['items'][:3]:  # Show first 3
            print(f"  • {item['name']}: {item.get('description', 'No description')[:50]}...")
    else:
        print("❌ Failed to extract dishes")