"""Quick test to see restaurant discovery and check for issues"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
LAT, LON = 59.3615, 17.9713

def test_discovery():
    """Test Google Places discovery"""
    
    print("Testing Google Places discovery...")
    print(f"API Key present: {'Yes' if GOOGLE_API_KEY else 'No'}")
    
    if not GOOGLE_API_KEY:
        print("❌ Missing GOOGLE_PLACES_API_KEY in .env file")
        return
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    params = {
        "location": f"{LAT},{LON}",
        "radius": 1500,
        "keyword": "restaurang lunch",
        "type": "restaurant",
        "key": GOOGLE_API_KEY,
        "language": "sv"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        print(f"Status: {response.status_code}")
        print(f"Results found: {len(data.get('results', []))}")
        
        if 'error_message' in data:
            print(f"❌ Google API Error: {data['error_message']}")
            return
        
        # Show first few restaurants
        for i, place in enumerate(data.get("results", [])[:5]):
            print(f"{i+1}. {place['name']} - Rating: {place.get('rating', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_discovery()