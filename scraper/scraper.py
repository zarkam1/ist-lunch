"""
Advanced Menu Scraper with AI Integration
For home development with full internet access
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import pytesseract
from PIL import Image
import openai
from typing import List, Dict, Optional
import re
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIMenuAnalyzer:
    """Uses OpenAI/Claude API to understand menus"""
    
    def __init__(self, api_key: str):
        self.client = openai.Client(api_key=api_key)
    
    async def analyze_menu_text(self, text: str) -> List[Dict]:
        """
        Send menu text to GPT-4 for analysis
        Returns structured menu items
        """
        prompt = f"""
        Analyze this Swedish restaurant lunch menu and extract:
        1. Dish name
        2. Description
        3. Category (Kött/Fisk/Vegetarisk/Vegansk/Övrigt)
        4. Price in SEK
        5. Allergens if mentioned
        6. Health score (0-100) based on ingredients
        
        Menu text:
        {text}
        
        Return as JSON array with these fields:
        [
            {{
                "name": "dish name",
                "description": "description",
                "category": "category",
                "price_sek": 000,
                "allergens": ["list"],
                "health_score": 00,
                "confidence": 0.0-1.0
            }}
        ]
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Swedish menu analyzer expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return []

class SmartWebScraper:
    """Intelligent scraper that handles dynamic content"""
    
    async def scrape_with_playwright(self, url: str) -> str:
        """Use Playwright for JavaScript-heavy sites"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set Swedish locale
            await page.set_extra_http_headers({
                'Accept-Language': 'sv-SE,sv;q=0.9'
            })
            
            await page.goto(url, wait_until='networkidle')
            
            # Wait for common menu selectors
            menu_selectors = [
                '.lunch-menu',
                '.dagens-lunch',
                '#lunch',
                '[data-menu="lunch"]',
                '.menu-content',
                'article:has-text("lunch")'
            ]
            
            for selector in menu_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    break
                except:
                    continue
            
            # Extract text content
            content = await page.content()
            await browser.close()
            
            return content
    
    async def extract_images_from_page(self, url: str) -> List[str]:
        """Extract menu images for OCR processing"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            
            # Find images that likely contain menus
            images = await page.evaluate("""
                () => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    return imgs
                        .filter(img => {
                            const alt = (img.alt || '').toLowerCase();
                            const src = (img.src || '').toLowerCase();
                            return alt.includes('lunch') || alt.includes('meny') ||
                                   src.includes('lunch') || src.includes('menu');
                        })
                        .map(img => img.src);
                }
            """)
            
            await browser.close()
            return images

class OCRProcessor:
    """Process menu images with OCR"""
    
    def __init__(self):
        # Configure Tesseract for Swedish
        self.custom_config = r'--oem 3 --psm 6 -l swe+eng'
    
    async def process_image_url(self, image_url: str) -> str:
        """Download and OCR an image"""
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    return self.extract_text_from_image(image_data)
        return ""
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using Tesseract"""
        from io import BytesIO
        
        image = Image.open(BytesIO(image_data))
        
        # Preprocess image for better OCR
        image = image.convert('L')  # Convert to grayscale
        
        # Extract text
        text = pytesseract.image_to_string(image, config=self.custom_config)
        
        return text

class RestaurantAPI:
    """Fetch restaurant data from various APIs"""
    
    def __init__(self, google_api_key: str = None, foursquare_api_key: str = None):
        self.google_api_key = google_api_key
        self.foursquare_api_key = foursquare_api_key
    
    async def get_google_places_menus(self, lat: float, lon: float, radius: int = 1500):
        """Use Google Places API to find restaurants"""
        if not self.google_api_key:
            return []
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "type": "restaurant",
            "key": self.google_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return data.get('results', [])
    
    async def get_restaurant_details(self, place_id: str):
        """Get detailed info including website"""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,website,rating,user_ratings_total,formatted_address",
            "key": self.google_api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                return data.get('result', {})

class SocialMediaScraper:
    """Scrape menus from social media"""
    
    async def scrape_facebook_page(self, page_url: str):
        """Scrape restaurant's Facebook for menu posts"""
        # Note: Requires Facebook API or careful scraping
        # to avoid being blocked
        pass
    
    async def scrape_instagram(self, username: str):
        """Check Instagram for menu photos"""
        # Instagram scraping is complex due to anti-bot measures
        # Consider using official API
        pass

class MenuAggregator:
    """Main orchestrator that combines all sources"""
    
    def __init__(self, ai_api_key: str, google_api_key: str = None):
        self.ai_analyzer = AIMenuAnalyzer(ai_api_key)
        self.web_scraper = SmartWebScraper()
        self.ocr_processor = OCRProcessor()
        self.restaurant_api = RestaurantAPI(google_api_key)
        
        # Swedish restaurant chain websites to check
        self.chain_scrapers = {
            'max': self.scrape_max_burgers,
            'espresso_house': self.scrape_espresso_house,
            'waynes': self.scrape_waynes_coffee
        }
    
    async def aggregate_all_menus(self, lat: float, lon: float):
        """
        Main method that orchestrates all data collection
        """
        all_menus = []
        
        # 1. Get restaurants from Google Places
        logger.info("Fetching restaurants from Google Places...")
        restaurants = await self.restaurant_api.get_google_places_menus(lat, lon)
        
        for restaurant in restaurants:
            place_id = restaurant['place_id']
            details = await self.restaurant_api.get_restaurant_details(place_id)
            
            if details.get('website'):
                # 2. Scrape restaurant website
                logger.info(f"Scraping {details['name']} website...")
                html = await self.web_scraper.scrape_with_playwright(details['website'])
                
                # 3. Extract menu text
                soup = BeautifulSoup(html, 'html.parser')
                menu_text = self.extract_menu_section(soup)
                
                if menu_text:
                    # 4. Use AI to analyze menu
                    logger.info(f"AI analyzing menu for {details['name']}...")
                    menu_items = await self.ai_analyzer.analyze_menu_text(menu_text)
                    
                    all_menus.append({
                        'restaurant': details['name'],
                        'address': details.get('formatted_address'),
                        'rating': details.get('rating'),
                        'review_count': details.get('user_ratings_total'),
                        'menu_items': menu_items,
                        'source': 'website',
                        'scraped_at': datetime.now().isoformat()
                    })
                else:
                    # 5. Try to find menu images
                    logger.info(f"Looking for menu images on {details['name']} website...")
                    images = await self.web_scraper.extract_images_from_page(details['website'])
                    
                    for img_url in images[:3]:  # Limit to 3 images
                        ocr_text = await self.ocr_processor.process_image_url(img_url)
                        if ocr_text:
                            menu_items = await self.ai_analyzer.analyze_menu_text(ocr_text)
                            if menu_items:
                                all_menus.append({
                                    'restaurant': details['name'],
                                    'menu_items': menu_items,
                                    'source': 'image_ocr'
                                })
                                break
        
        # 6. Check known restaurant aggregators
        logger.info("Checking restaurant aggregators...")
        aggregator_menus = await self.scrape_aggregators()
        all_menus.extend(aggregator_menus)
        
        return all_menus
    
    def extract_menu_section(self, soup: BeautifulSoup) -> str:
        """Extract likely menu content from HTML"""
        menu_keywords = ['lunch', 'dagens', 'meny', 'menu', 'veckans']
        
        # Look for menu sections
        for keyword in menu_keywords:
            # Try different selectors
            menu_section = soup.find(['div', 'section', 'article'], 
                                    class_=re.compile(keyword, re.I))
            if menu_section:
                return menu_section.get_text(separator='\n', strip=True)
            
            # Try finding by text content
            menu_section = soup.find(text=re.compile(keyword, re.I))
            if menu_section:
                parent = menu_section.find_parent(['div', 'section', 'article'])
                if parent:
                    return parent.get_text(separator='\n', strip=True)
        
        return ""
    
    async def scrape_aggregators(self):
        """Scrape menu aggregator sites"""
        menus = []
        
        # Kvartersmenyn
        url = "https://www.kvartersmenyn.se/index.php/stockholm/area/sundbyberg_22"
        html = await self.web_scraper.scrape_with_playwright(url)
        # Parse and extract...
        
        # TheFork
        # Wolt
        # Foodora
        
        return menus
    
    async def scrape_max_burgers(self):
        """Custom scraper for MAX Burgers"""
        # Chain-specific scraping logic
        pass
    
    async def scrape_espresso_house(self):
        """Custom scraper for Espresso House"""
        pass
    
    async def scrape_waynes_coffee(self):
        """Custom scraper for Wayne's Coffee"""
        pass

# ===== MAIN EXECUTION =====
async def main():
    """
    Run the complete menu aggregation pipeline
    """
    # Configuration
    OPENAI_API_KEY = "your-openai-api-key"
    GOOGLE_API_KEY = "your-google-api-key"
    SUNDBYBERG_LAT = 59.3615
    SUNDBYBERG_LON = 17.9713
    
    # Initialize aggregator
    aggregator = MenuAggregator(
        ai_api_key=OPENAI_API_KEY,
        google_api_key=GOOGLE_API_KEY
    )
    
    # Collect all menus
    logger.info("Starting menu aggregation...")
    menus = await aggregator.aggregate_all_menus(SUNDBYBERG_LAT, SUNDBYBERG_LON)
    
    # Save results
    with open('menus_today.json', 'w', encoding='utf-8') as f:
        json.dump(menus, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Collected {len(menus)} restaurant menus")
    
    # Print summary
    for menu in menus:
        print(f"\n{menu['restaurant']}:")
        for item in menu.get('menu_items', []):
            print(f"  - {item['name']}: {item['price_sek']} kr ({item['category']})")

if __name__ == "__main__":
    asyncio.run(main())

# ===== REQUIREMENTS.TXT =====
"""
Requirements for AI-powered menu scraping:

# Web scraping
aiohttp==3.9.1
beautifulsoup4==4.12.3
playwright==1.41.0
lxml==5.1.0

# OCR
Pillow==10.2.0
pytesseract==0.3.10

# AI/ML
openai==1.10.0
transformers==4.36.0  # For local models
langchain==0.1.0  # For chaining AI operations

# Swedish NLP (optional)
spacy==3.7.2
# python -m spacy download sv_core_news_sm

# Image processing
opencv-python==4.9.0
pdf2image==1.17.0

# APIs
google-api-python-client==2.114.0
python-facebook-api==0.17.0

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9

# Scheduling
celery==5.3.4
redis==5.0.1
schedule==1.2.0

# Monitoring
sentry-sdk==1.39.2
prometheus-client==0.19.0
"""