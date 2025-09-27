// frontend/app/page.tsx
"use client";

import { useState, useEffect, useMemo } from 'react';
import { Search, Filter, Clock, MapPin, Heart, TrendingUp, Leaf, Beef, Fish, ChefHat, Euro, Star, RefreshCw, Sun, Moon } from 'lucide-react';

// Types
interface MenuItem {
  name: string;
  description?: string;
  price: number | null;
  category: "Kött" | "Fisk" | "Vegetarisk" | "Vegansk" | "Övrigt";
  health_score: number;
  diet_tags: string[];
  allergens: string[];
}

interface Restaurant {
  id: string;
  name: string;
  address: string;
  url: string;
  lat?: number;
  lon?: number;
  menu_items: MenuItem[];
  distance?: number;
  walking_time?: number;
}

interface MenuData {
  generated_at: string;
  date: string;
  restaurants: Restaurant[];
}

// Modern color scheme
const categoryColors = {
  'Kött': 'bg-red-50 text-red-700 border-red-200',
  'Fisk': 'bg-blue-50 text-blue-700 border-blue-200',
  'Vegetarisk': 'bg-green-50 text-green-700 border-green-200',
  'Vegansk': 'bg-emerald-50 text-emerald-700 border-emerald-200',
  'Övrigt': 'bg-gray-50 text-gray-700 border-gray-200'
};

const categoryEmojis = {
  'Kött': '🥩',
  'Fisk': '🐟',
  'Vegetarisk': '🥗',
  'Vegansk': '🌱',
  'Övrigt': '🍽️'
};

// Components
const HealthScore = ({ score }: { score: number }) => {
  const getColor = () => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-amber-600';
    return 'text-red-600';
  };
  
  return (
    <div className={`flex items-center gap-1 ${getColor()}`}>
      <Heart className="w-4 h-4 fill-current" />
      <span className="font-semibold">{score}</span>
    </div>
  );
};

const DietTag = ({ tag }: { tag: string }) => {
  const getIcon = () => {
    if (tag.includes('protein')) return <TrendingUp className="w-3 h-3" />;
    if (tag.includes('carb')) return <Beef className="w-3 h-3" />;
    if (tag.includes('gluten')) return <ChefHat className="w-3 h-3" />;
    return <Leaf className="w-3 h-3" />;
  };
  
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 text-slate-700 rounded-full text-xs">
      {getIcon()}
      {tag}
    </span>
  );
};

const RestaurantCard = ({ restaurant }: { restaurant: Restaurant }) => {
  const avgPrice = useMemo(() => {
    const prices = restaurant.menu_items.filter(item => item.price).map(item => item.price!);
    return prices.length > 0 ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : null;
  }, [restaurant.menu_items]);
  
  const avgHealth = useMemo(() => {
    const scores = restaurant.menu_items.map(item => item.health_score);
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  }, [restaurant.menu_items]);
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 hover:scale-[1.01]">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 p-5 border-b border-gray-100">
        <div className="flex justify-between items-start mb-2">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{restaurant.name}</h3>
            <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {restaurant.walking_time || '5'} min
              </span>
              {avgPrice && (
                <span className="flex items-center gap-1">
                  <Euro className="w-4 h-4" />
                  ~{avgPrice} kr
                </span>
              )}
              <HealthScore score={avgHealth} />
            </div>
          </div>
          <a 
            href={restaurant.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            Hemsida →
          </a>
        </div>
      </div>
      
      {/* Menu Items */}
      <div className="p-5 space-y-4">
        {restaurant.menu_items.map((item, idx) => (
          <div key={idx} className="border-b border-gray-100 last:border-0 pb-4 last:pb-0">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{item.name}</h4>
                {item.description && (
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                )}
              </div>
              <div className="flex items-center gap-3 ml-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${categoryColors[item.category]}`}>
                  {categoryEmojis[item.category]} {item.category}
                </span>
                {item.price && (
                  <span className="font-bold text-gray-900">{item.price} kr</span>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-4 mt-3">
              <HealthScore score={item.health_score} />
              {item.diet_tags.length > 0 && (
                <div className="flex gap-2 flex-wrap">
                  {item.diet_tags.slice(0, 3).map((tag, i) => (
                    <DietTag key={i} tag={tag} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main App Component
export default function ISTLunch() {
  const [menuData, setMenuData] = useState<MenuData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('alla');
  const [selectedDiet, setSelectedDiet] = useState<string>('alla');
  const [maxPrice, setMaxPrice] = useState<number>(200);
  const [minHealth, setMinHealth] = useState<number>(0);
  const [darkMode, setDarkMode] = useState(false);
  
  useEffect(() => {
    fetchMenuData();
  }, []);
  
  const fetchMenuData = async () => {
    setLoading(true);
    try {
      // In production, fetch from your API
      // For now, using sample data
      const response = await fetch('/api/menus');
      const data = await response.json();
      setMenuData(data);
    } catch (error) {
      console.error('Failed to fetch menus:', error);
      // Use sample data for demo
      setMenuData(getSampleData());
    } finally {
      setLoading(false);
    }
  };
  
  // Filter restaurants and items
  const filteredRestaurants = useMemo(() => {
    if (!menuData) return [];
    
    return menuData.restaurants.map(restaurant => {
      const filteredItems = restaurant.menu_items.filter(item => {
        // Search filter
        if (searchTerm && !item.name.toLowerCase().includes(searchTerm.toLowerCase()) && 
            !item.description?.toLowerCase().includes(searchTerm.toLowerCase())) {
          return false;
        }
        
        // Category filter
        if (selectedCategory !== 'alla' && item.category !== selectedCategory) {
          return false;
        }
        
        // Diet filter
        if (selectedDiet !== 'alla' && !item.diet_tags.includes(selectedDiet)) {
          return false;
        }
        
        // Price filter
        if (item.price && item.price > maxPrice) {
          return false;
        }
        
        // Health filter
        if (item.health_score < minHealth) {
          return false;
        }
        
        return true;
      });
      
      return {
        ...restaurant,
        menu_items: filteredItems
      };
    }).filter(r => r.menu_items.length > 0);
  }, [menuData, searchTerm, selectedCategory, selectedDiet, maxPrice, minHealth]);
  
  // Stats
  const stats = useMemo(() => {
    if (!filteredRestaurants.length) return { restaurants: 0, items: 0, avgPrice: 0, avgHealth: 0 };
    
    const allItems = filteredRestaurants.flatMap(r => r.menu_items);
    const prices = allItems.filter(i => i.price).map(i => i.price!);
    const healths = allItems.map(i => i.health_score);
    
    return {
      restaurants: filteredRestaurants.length,
      items: allItems.length,
      avgPrice: prices.length ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : 0,
      avgHealth: healths.length ? Math.round(healths.reduce((a, b) => a + b, 0) / healths.length) : 0
    };
  }, [filteredRestaurants]);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Laddar dagens lunchmenyer...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-gradient-to-br from-slate-50 to-slate-100'}`}>
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🍽️</span>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  IST Lunch
                </h1>
                <p className="text-xs text-gray-600">Sundbybergs bästa lunchguide</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-xs text-gray-500">Uppdaterad</p>
                <p className="text-sm font-medium text-gray-700">
                  {new Date().toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <button
                onClick={fetchMenuData}
                className="p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition"
                title="Uppdatera"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition"
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Stats Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">{stats.restaurants}</p>
              <p className="text-sm text-gray-600">Restauranger</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">{stats.items}</p>
              <p className="text-sm text-gray-600">Rätter</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">{stats.avgPrice} kr</p>
              <p className="text-sm text-gray-600">Snittpris</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">{stats.avgHealth}</p>
              <p className="text-sm text-gray-600">Hälsopoäng</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Filters */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Search */}
          <div className="relative mb-6">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Sök på restaurang eller maträtt..."
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          {/* Filter Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Kategori</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 transition"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="alla">Alla kategorier</option>
                <option value="Kött">🥩 Kött</option>
                <option value="Fisk">🐟 Fisk</option>
                <option value="Vegetarisk">🥗 Vegetarisk</option>
                <option value="Vegansk">🌱 Vegansk</option>
                <option value="Övrigt">🍽️ Övrigt</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Kost</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 transition"
                value={selectedDiet}
                onChange={(e) => setSelectedDiet(e.target.value)}
              >
                <option value="alla">Alla koster</option>
                <option value="high-protein">High Protein</option>
                <option value="low-carb">Low Carb</option>
                <option value="glutenfri">Glutenfri</option>
                <option value="laktosfri">Laktosfri</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max pris: {maxPrice} kr
              </label>
              <input
                type="range"
                min="50"
                max="300"
                step="10"
                value={maxPrice}
                onChange={(e) => setMaxPrice(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Min hälsopoäng: {minHealth}
              </label>
              <input
                type="range"
                min="0"
                max="100"
                step="10"
                value={minHealth}
                onChange={(e) => setMinHealth(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* Restaurant Cards */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {filteredRestaurants.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2">
            {filteredRestaurants.map(restaurant => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-gray-500 text-lg">Inga restauranger matchar dina filter</p>
            <button 
              onClick={() => {
                setSearchTerm('');
                setSelectedCategory('alla');
                setSelectedDiet('alla');
                setMaxPrice(200);
                setMinHealth(0);
              }}
              className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Återställ filter
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

// Sample data function
function getSampleData(): MenuData {
  return {
    generated_at: new Date().toISOString(),
    date: new Date().toISOString().split('T')[0],
    restaurants: [
      {
        id: "eatery-garden",
        name: "Eatery Garden Sundbyberg",
        address: "Landsvägen 50A",
        url: "https://eatery.se",
        menu_items: [
          {
            name: "Örtbakad kycklingfilé",
            description: "Med champinjonsås och rostad potatis",
            price: 135,
            category: "Kött",
            health_score: 65,
            diet_tags: ["high-protein"],
            allergens: ["laktos"]
          },
          {
            name: "Lax med dillsås",
            description: "Serveras med kokt potatis och grönsaker",
            price: 145,
            category: "Fisk",
            health_score: 85,
            diet_tags: ["high-protein", "low-carb"],
            allergens: ["fisk", "laktos"]
          }
        ],
        walking_time: 5
      },
      {
        id: "a-la-chino",
        name: "A la Chino",
        address: "Sundbyberg centrum",
        url: "https://alachino.se",
        menu_items: [
          {
            name: "Pasta Carbonara",
            description: "Klassisk italiensk rätt",
            price: 150,
            category: "Kött",
            health_score: 45,
            diet_tags: [],
            allergens: ["gluten", "ägg", "laktos"]
          }
        ],
        walking_time: 3
      }
    ]
  };
}