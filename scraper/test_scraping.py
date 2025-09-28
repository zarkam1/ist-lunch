"""Test scraping for a few restaurants to debug issues"""

import asyncio
import os
import json
from unified_scraper import UnifiedLunchScraper

async def test_scraping():
    """Test scraping for just a few restaurants"""
    
    print("🧪 Testing smart routing on a few restaurants...")
    
    scraper = UnifiedLunchScraper()
    
    # Test restaurants (manual list to avoid Google API calls)
    test_restaurants = [
        {
            "id": "restaurang-s",
            "name": "Restaurang S",
            "website": "http://www.restaurangs.nu"
        },
        {
            "id": "krubb-burgers-sundbyberg", 
            "name": "KRUBB Burgers Sundbyberg",
            "website": "https://krubbburgers.se"
        },
        {
            "id": "the-public",
            "name": "The Public",
            "website": "https://sundbyberg.thepublic.se"
        }
    ]
    
    scraper.restaurants = test_restaurants
    
    # Test scraping with force=True
    print(f"\n🔍 Testing {len(test_restaurants)} restaurants...")
    await scraper.scrape_all_menus(force_all=True)
    
    # Print results
    print(f"\n📊 Results:")
    for rest_id, menu_data in scraper.menus.items():
        print(f"✅ {menu_data['restaurant']}: {menu_data['count']} items via {menu_data.get('method', 'unknown')}")
    
    # Print statistics
    stats = scraper.scraping_stats
    print(f"\n📈 Statistics:")
    print(f"   Traditional success: {stats['traditional_success']}")
    print(f"   Traditional failed: {stats['traditional_failed']}")
    print(f"   Screenshot success: {stats['screenshot_success']}")
    print(f"   Screenshot failed: {stats['screenshot_failed']}")
    print(f"   Total cost: ${stats['total_cost']:.3f}")

if __name__ == "__main__":
    asyncio.run(test_scraping())