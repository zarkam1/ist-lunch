"""Test ScraperAPI directly"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPERAPI_KEY")

def test_scraper_api():
    """Test ScraperAPI with a simple request"""
    
    print("Testing ScraperAPI...")
    
    params = {
        'api_key': SCRAPER_API_KEY,
        'url': 'https://krubbburgers.se',
        'render': 'false'  # Don't render JS for faster test
    }
    
    try:
        print("Making request...")
        response = requests.get(
            'http://api.scraperapi.com',
            params=params,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        print(f"First 200 chars: {response.text[:200]}")
        
        if response.status_code == 200:
            print("✅ ScraperAPI working!")
        else:
            print(f"❌ ScraperAPI error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_scraper_api()