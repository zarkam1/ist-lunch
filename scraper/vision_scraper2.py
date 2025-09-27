"""
Re-analyze existing screenshots to extract descriptions
Specifically for Persian/ethnic restaurants where descriptions are crucial
"""

import base64
import json
import os
from typing import List, Dict
import openai
from dotenv import load_dotenv
import glob

load_dotenv()

class DescriptionExtractor:
    """Re-analyze screenshots focusing on descriptions"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Need OPENAI_API_KEY in .env")
        self.client = openai.OpenAI(api_key=api_key)
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def extract_with_descriptions(self, image_path: str, restaurant_name: str) -> List[Dict]:
        """Extract menu items WITH descriptions"""
        
        if not os.path.exists(image_path):
            print(f"    ❌ Image not found: {image_path}")
            return []
        
        print(f"    🔍 Re-analyzing {os.path.basename(image_path)}...")
        
        base64_image = self.encode_image(image_path)
        
        # Strong emphasis on descriptions for Persian restaurant
        if 'bonab' in restaurant_name.lower() or 'persisk' in restaurant_name.lower():
            system_prompt = """You are analyzing a Persian restaurant menu. 
CRITICAL: Persian dish names mean nothing to Swedish customers.
You MUST extract BOTH the Persian name AND the Swedish description."""
            
            user_prompt = """Look at this Persian restaurant menu screenshot.

For EACH dish visible, extract:
1. The Persian/foreign name (like "Gheyme bademjoon")
2. The Swedish description that explains what it is
3. The price in SEK
4. Appropriate category

Example of what I need:
{
  "name": "Gheyme bademjoon",
  "description": "Lammkött med gula linser, stekt aubergine och strips, serveras med saffransris",
  "price": 149,
  "category": "Kött"
}

IMPORTANT: 
- The description is ESSENTIAL - without it, customers don't know what they're ordering
- Look for the Swedish text that follows or is near each Persian dish name
- These descriptions usually mention ingredients like "lammkött", "ris", "saffran", etc.

Return JSON array of ALL menu items with descriptions:"""
        
        else:
            system_prompt = "You are extracting menu items from a restaurant screenshot."
            user_prompt = """Extract menu items from this screenshot.

For each dish, include:
1. name: The dish name as shown
2. description: Any explanation of what the dish contains (if visible)
3. price: Price in SEK
4. category: Appropriate food category

Return JSON array:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content.strip()
            result = result.replace('```json', '').replace('```', '').strip()
            
            if result.startswith('['):
                items = json.loads(result)
                print(f"    ✅ Extracted {len(items)} items with descriptions")
                return items
            else:
                print(f"    ⚠️ Unexpected response format")
                return []
                
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:100]}")
            return []

async def main():
    """Re-analyze screenshots for better extraction"""
    
    print("🔄 Re-analyzing Screenshots for Descriptions")
    print("=" * 50)
    
    extractor = DescriptionExtractor()
    
    # Find Bonab screenshots specifically
    screenshots = glob.glob("data/screenshots/*Bonab*.png")
    
    if not screenshots:
        print("❌ No Bonab screenshots found!")
        print("Looking for any screenshots...")
        screenshots = glob.glob("data/screenshots/*.png")[:2]
    
    all_items = []
    
    for screenshot in screenshots:
        restaurant_name = "Bonab - Persisk Restaurang" if "Bonab" in screenshot else "Restaurant"
        print(f"\n📸 Processing: {os.path.basename(screenshot)}")
        
        items = await extractor.extract_with_descriptions(screenshot, restaurant_name)
        
        if items:
            # Show sample with descriptions
            print("\n📝 Sample items extracted:")
            for item in items[:3]:
                print(f"\n  🍽️ {item.get('name', 'Unknown')}")
                if item.get('description'):
                    print(f"     📖 {item['description']}")
                print(f"     💰 {item.get('price', '?')} kr")
                print(f"     📂 {item.get('category', 'Unknown')}")
            
            all_items.extend(items)
    
    # Save enhanced results
    if all_items:
        output = {
            'restaurant': 'Bonab - Persisk Restaurang Stockholm',
            'items_with_descriptions': all_items,
            'total_items': len(all_items)
        }
        
        os.makedirs('data', exist_ok=True)
        with open('data/bonab_enhanced.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Saved {len(all_items)} items with descriptions to data/bonab_enhanced.json")
        
        # Show how it should look in the app
        print("\n🎯 How it will appear in your app:")
        print("-" * 50)
        for item in all_items[:5]:
            name = item.get('name', '')
            desc = item.get('description', '')
            price = item.get('price', 145)
            
            if desc:
                display = f"{name} - {desc[:60]}..."
            else:
                display = name
            
            print(f"\n{display}")
            print(f"  {price} kr")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())