// app/api/menus/route.ts
import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

export async function GET(request: NextRequest) {
  try {
    // Read the frontend lunch data
    const dataPath = path.join(process.cwd(), 'data', 'frontend_lunch_dishes.json');
    const combinedDataPath = path.join(process.cwd(), 'data', 'combined_lunch_data.json');
    
    let dishesData = [];
    let metadata = {};
    
    // Try to read the combined data first (has metadata)
    try {
      const combinedRaw = fs.readFileSync(combinedDataPath, 'utf-8');
      const combinedData = JSON.parse(combinedRaw);
      dishesData = combinedData.dishes || [];
      metadata = {
        generated_at: combinedData.generated_at,
        total_dishes: combinedData.total_dishes,
        total_restaurants: combinedData.total_restaurants,
        restaurant_counts: combinedData.restaurant_counts
      };
    } catch (error) {
      // Fallback to frontend dishes data
      const dishesRaw = fs.readFileSync(dataPath, 'utf-8');
      dishesData = JSON.parse(dishesRaw);
      metadata = {
        generated_at: new Date().toISOString(),
        total_dishes: dishesData.length,
        total_restaurants: [...new Set(dishesData.map((d: any) => d.restaurant))].length
      };
    }
    
    // Transform data to match frontend interface
    const restaurantMap = new Map();
    
    dishesData.forEach((dish: any) => {
      const restaurantName = dish.restaurant || 'Unknown';
      
      if (!restaurantMap.has(restaurantName)) {
        restaurantMap.set(restaurantName, {
          id: restaurantName.toLowerCase().replace(/[^a-z0-9]/g, '-'),
          name: restaurantName,
          address: getRestaurantAddress(restaurantName),
          url: getRestaurantUrl(restaurantName),
          menu_items: [],
          walking_time: getWalkingTime(restaurantName)
        });
      }
      
      const restaurant = restaurantMap.get(restaurantName);
      
      // Transform dish to match frontend interface
      const menuItem = {
        name: dish.name || 'Unknown Dish',
        description: dish.description || '',
        price: dish.price || null,
        category: mapCategory(dish.category || ''),
        health_score: generateHealthScore(dish),
        diet_tags: generateDietTags(dish),
        allergens: generateAllergens(dish)
      };
      
      restaurant.menu_items.push(menuItem);
    });
    
    const response = {
      generated_at: metadata.generated_at,
      date: new Date().toISOString().split('T')[0],
      total_dishes: metadata.total_dishes,
      total_restaurants: metadata.total_restaurants,
      restaurants: Array.from(restaurantMap.values())
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('Error reading menu data:', error);
    
    // Return sample data as fallback
    return NextResponse.json({
      generated_at: new Date().toISOString(),
      date: new Date().toISOString().split('T')[0],
      total_dishes: 0,
      total_restaurants: 0,
      restaurants: []
    });
  }
}

// Helper functions
function mapCategory(category: string): "Kött" | "Fisk" | "Vegetarisk" | "Vegansk" | "Övrigt" {
  const cat = category.toLowerCase();
  if (cat.includes('kött') || cat.includes('beef') || cat.includes('chicken') || cat.includes('pork')) return 'Kött';
  if (cat.includes('fisk') || cat.includes('fish') || cat.includes('seafood')) return 'Fisk';
  if (cat.includes('vegetarisk') || cat.includes('vegetarian')) return 'Vegetarisk';
  if (cat.includes('vegansk') || cat.includes('vegan')) return 'Vegansk';
  return 'Övrigt';
}

function generateHealthScore(dish: any): number {
  // Simple health score based on category and description
  const category = dish.category?.toLowerCase() || '';
  const description = dish.description?.toLowerCase() || '';
  const name = dish.name?.toLowerCase() || '';
  
  let score = 50; // Base score
  
  // Category bonuses
  if (category.includes('fisk')) score += 20;
  if (category.includes('vegetarisk')) score += 15;
  if (category.includes('vegansk')) score += 10;
  
  // Ingredient bonuses
  if (description.includes('grönsaker') || description.includes('sallad')) score += 10;
  if (description.includes('fullkorn') || description.includes('quinoa')) score += 10;
  if (description.includes('friterad') || description.includes('stekt')) score -= 15;
  if (description.includes('grädde') || description.includes('smör')) score -= 10;
  
  return Math.max(0, Math.min(100, score));
}

function generateDietTags(dish: any): string[] {
  const tags = [];
  const description = dish.description?.toLowerCase() || '';
  const category = dish.category?.toLowerCase() || '';
  
  if (category.includes('fisk') || category.includes('kött')) tags.push('high-protein');
  if (description.includes('laktosfri')) tags.push('laktosfri');
  if (description.includes('glutenfri')) tags.push('glutenfri');
  if (!description.includes('potatis') && !description.includes('pasta')) tags.push('low-carb');
  
  return tags;
}

function generateAllergens(dish: any): string[] {
  const allergens = [];
  const description = dish.description?.toLowerCase() || '';
  
  if (description.includes('mjölk') || description.includes('ost') || description.includes('grädde')) allergens.push('laktos');
  if (description.includes('pasta') || description.includes('bröd')) allergens.push('gluten');
  if (description.includes('ägg')) allergens.push('ägg');
  if (dish.category?.toLowerCase().includes('fisk')) allergens.push('fisk');
  
  return allergens;
}

function getRestaurantAddress(name: string): string {
  const addresses: { [key: string]: string } = {
    'Lilla Rött': 'Tulegatan 5, Sundbyberg',
    'KRUBB Burgers': 'Sturegatan 6, Sundbyberg', 
    'The Public': 'Landsvägen 50, Sundbyberg',
    'Restaurang S': 'Järnvägsgatan 4, Sundbyberg',
    'Delibruket': 'Sundbybergs centrum',
    'Klå Fann Thai': 'Solna centrum'
  };
  
  return addresses[name] || 'Sundbyberg';
}

function getRestaurantUrl(name: string): string {
  const urls: { [key: string]: string } = {
    'Lilla Rött': 'https://lillaro.nu',
    'KRUBB Burgers': 'https://krubbburgers.se',
    'The Public': 'https://sundbyberg.thepublic.se',
    'Restaurang S': 'http://www.restaurangs.nu',
    'Delibruket': 'https://delibruket.se'
  };
  
  return urls[name] || '#';
}

function getWalkingTime(name: string): number {
  const times: { [key: string]: number } = {
    'Lilla Rött': 3,
    'KRUBB Burgers': 5,
    'The Public': 8,
    'Restaurang S': 6,
    'Delibruket': 7,
    'Klå Fann Thai': 12
  };
  
  return times[name] || 5;
}