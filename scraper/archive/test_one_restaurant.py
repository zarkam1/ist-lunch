# test_one_restaurant.py
import asyncio
from scraper import RestaurantScraper, MenuAnalyzer

async def test():
    scraper = RestaurantScraper()
    analyzer = MenuAnalyzer()
    
    # Test Delibruket Flatbread
    url = "http://www.flatbread.se/"
    print(f"Testing {url}...")
    
    menu_text = await scraper.scrape_url(url)
    print(f"Found {len(menu_text)} characters")
    
    if menu_text:
        items = await analyzer.analyze_menu("Delibruket", menu_text[:1000])
        print(f"Found {len(items)} menu items")
        for item in items:
            print(f"  - {item['name']}: {item['price']} kr")

asyncio.run(test())