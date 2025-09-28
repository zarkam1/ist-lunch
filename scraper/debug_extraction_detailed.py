"""
Debug why The Public and Restaurang S extraction fails
Save HTML samples and test different extraction methods
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import re

load_dotenv()

def debug_restaurant(name: str, url: str):
    """Deep debug of a specific restaurant"""
    
    print(f"\n{'='*60}")
    print(f"🔍 DEBUGGING: {name}")
    print(f"📍 URL: {url}")
    print('='*60)
    
    # Fetch HTML
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch: {response.status_code}")
        return
    
    html = response.text
    print(f"✅ Fetched {len(html)} bytes")
    
    # Save raw HTML for inspection
    os.makedirs("debug", exist_ok=True)
    filename = f"debug/{name.replace(' ', '_')}_raw.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"💾 Saved raw HTML to {filename}")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove scripts and styles
    for element in soup(['script', 'style', 'meta', 'link', 'noscript']):
        element.decompose()
    
    # Strategy 1: Find menu by common patterns
    print("\n📋 SEARCHING FOR MENU CONTENT:")
    print("-" * 40)
    
    menu_indicators = [
        "dagens lunch", "veckans lunch", "lunch meny", "dagens rätt",
        "måndag", "tisdag", "onsdag", "torsdag", "fredag"
    ]
    
    # Check whole page text
    page_text = soup.get_text()
    for indicator in menu_indicators:
        count = page_text.lower().count(indicator)
        if count > 0:
            print(f"  ✓ Found '{indicator}': {count} times")
    
    # Strategy 2: Look for price patterns
    price_pattern = r'\b(6[0-9]|7[0-9]|8[0-9]|9[0-9]|1[0-9]{2})\s*(kr|:-|SEK)?'
    prices = re.findall(price_pattern, page_text)
    print(f"\n  💰 Found {len(prices)} price patterns")
    if prices:
        print(f"     Sample prices: {[p[0] for p in prices[:5]]}")
    
    # Strategy 3: Find specific containers
    print("\n📦 CHECKING CONTAINERS:")
    print("-" * 40)
    
    # Different selectors to try
    selectors = [
        ('div.lunch', 'Lunch div'),
        ('div.menu', 'Menu div'),
        ('section.lunch', 'Lunch section'),
        ('div[class*="lunch"]', 'Class contains lunch'),
        ('div[class*="menu"]', 'Class contains menu'),
        ('main', 'Main content'),
        ('article', 'Article'),
        ('div.content', 'Content div'),
        ('#lunch', 'Lunch ID'),
        ('#menu', 'Menu ID')
    ]
    
    best_container = None
    best_score = 0
    
    for selector, description in selectors:
        elements = soup.select(selector)
        if elements:
            for elem in elements:
                text = elem.get_text()
                # Score based on menu keywords
                score = sum(1 for kw in menu_indicators if kw in text.lower())
                score += len(re.findall(price_pattern, text)) * 0.5
                
                if score > best_score:
                    best_score = score
                    best_container = elem
                    print(f"  ✓ {description}: Score {score:.1f} ({len(text)} chars)")
    
    # Extract best content
    if best_container:
        menu_text = best_container.get_text()
        print(f"\n🎯 BEST CONTAINER: {len(menu_text)} chars, score {best_score:.1f}")
    else:
        # Fallback: Find text around lunch keywords
        print("\n⚠️ No container found, using keyword proximity extraction")
        menu_text = extract_around_keywords(page_text, menu_indicators)
    
    # Save extracted menu text
    menu_file = f"debug/{name.replace(' ', '_')}_menu.txt"
    with open(menu_file, "w", encoding="utf-8") as f:
        f.write(menu_text[:5000])
    print(f"💾 Saved menu text to {menu_file}")
    
    # Try to extract items
    print("\n🍽️ EXTRACTING MENU ITEMS:")
    print("-" * 40)
    
    items = extract_menu_items(menu_text)
    
    if items:
        print(f"✅ Found {len(items)} items!")
        for item in items[:5]:
            print(f"  • {item['name'][:50]} - {item.get('price', '?')} kr")
    else:
        print("❌ No items extracted")
        print("\nSample of menu text:")
        print("-" * 40)
        print(menu_text[:500])

def extract_around_keywords(text: str, keywords: list, context: int = 500) -> str:
    """Extract text around menu keywords"""
    
    extracted = []
    text_lower = text.lower()
    
    for keyword in keywords:
        index = text_lower.find(keyword)
        if index != -1:
            start = max(0, index - context)
            end = min(len(text), index + len(keyword) + context)
            extracted.append(text[start:end])
    
    return "\n---\n".join(extracted)

def extract_menu_items(text: str) -> list:
    """Extract menu items using patterns"""
    
    items = []
    
    # Pattern 1: Line with price at end
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        # Look for lines ending with price
        price_match = re.search(r'(\d{2,3})\s*(?:kr|:-|SEK)?$', line)
        if price_match and len(line) > 10:
            price = int(price_match.group(1))
            if 50 <= price <= 200:
                name = line[:price_match.start()].strip(' .-')
                if name and len(name) > 3:
                    items.append({"name": name, "price": price})
    
    # Pattern 2: Weekday followed by dish
    weekday_pattern = r'(måndag|tisdag|onsdag|torsdag|fredag)[:\s]+([^.\n]{10,})'
    matches = re.findall(weekday_pattern, text.lower())
    for day, dish in matches:
        items.append({
            "name": dish.strip().title(),
            "day": day,
            "price": 110  # Default lunch price
        })
    
    # Pattern 3: Numbered items
    numbered_pattern = r'^\d+\.\s*([^.\n]{10,}?)\s*(\d{2,3})\s*(?:kr|:-)?'
    for match in re.finditer(numbered_pattern, text, re.MULTILINE):
        name = match.group(1).strip()
        price = int(match.group(2))
        if 50 <= price <= 200:
            items.append({"name": name, "price": price})
    
    # Deduplicate
    unique = []
    seen = set()
    for item in items:
        key = item['name'][:30].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    
    return unique

# Debug the problem restaurants
problem_restaurants = [
    ("The Public", "https://sundbyberg.thepublic.se"),
    ("Restaurang S", "http://www.restaurangs.nu")
]

for name, url in problem_restaurants:
    debug_restaurant(name, url)

print("\n" + "="*60)
print("📝 NEXT STEPS:")
print("1. Check debug/*.html files to see raw HTML")
print("2. Check debug/*_menu.txt to see extracted text")
print("3. Look for menu in unexpected places (iframes, JavaScript variables)")
print("4. May need to try different URLs (/lunch, /meny, etc.)")
print("="*60)