"use client";

import { useState, useEffect, useMemo, useRef } from 'react';
import { Search, Filter, MapPin, RefreshCw } from 'lucide-react';
import DishCard from '../components/DishCard';
import FilterBar from '../components/FilterBar';
import AnimatedCounter from '../components/AnimatedCounter';
import DishCardSkeleton from '../components/DishCardSkeleton';
import { getPlaceholderDescription } from '../lib/placeholderDescriptions';

// Types
interface Dish {
  name: string;
  restaurant: string;
  restaurant_id?: string;
  price: number;
  category: string;
  description?: string;
  walking_minutes?: number;
}

interface Filters {
  restaurant: string;
  category: string;
  search: string;
  sortBy: 'price-asc' | 'price-desc' | 'distance' | 'name';
}

export default function SundbybergLunchApp() {
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Filters>({
    restaurant: '',
    category: '',
    search: '',
    sortBy: 'price-asc'  // Default to lowest price first
  });

  useEffect(() => {
    fetchDishes();
  }, []);

  const fetchDishes = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/menus');
      const data = await response.json();
      
      // Transform restaurant-grouped data to flat dish array
      const allDishes: Dish[] = [];
      data.restaurants?.forEach((restaurant: any) => {
        restaurant.menu_items?.forEach((item: any) => {
          // Use placeholder description if none exists
          const description = item.description || getPlaceholderDescription(item.name);
          
          allDishes.push({
            name: item.name,
            restaurant: restaurant.name,
            restaurant_id: restaurant.id,
            price: item.price,
            category: item.category,
            description: description,
            walking_minutes: restaurant.walking_time || 5
          });
        });
      });
      
      setDishes(allDishes);
    } catch (error) {
      console.error('Failed to fetch dishes:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get unique restaurants and categories for filters
  const restaurants = useMemo(() => {
    const unique = [...new Set(dishes.map(d => d.restaurant))];
    return unique.sort();
  }, [dishes]);

  const categories = useMemo(() => {
    const unique = [...new Set(dishes.map(d => d.category))];
    return unique.sort();
  }, [dishes]);

  // Filter and sort dishes
  const filteredDishes = useMemo(() => {
    let filtered = dishes.filter(dish => {
      if (filters.restaurant && dish.restaurant !== filters.restaurant) return false;
      if (filters.category && dish.category !== filters.category) return false;
      if (filters.search && !dish.name.toLowerCase().includes(filters.search.toLowerCase())) return false;
      return true;
    });

    // Sort dishes
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'price-asc':
          return (a.price || 0) - (b.price || 0);
        case 'price-desc':
          return (b.price || 0) - (a.price || 0);
        case 'distance':
          return (a.walking_minutes || 0) - (b.walking_minutes || 0);
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    return filtered;
  }, [dishes, filters]);

  const stats = useMemo(() => {
    const totalDishes = filteredDishes.length;
    const uniqueRestaurants = new Set(filteredDishes.map(d => d.restaurant)).size;
    const prices = filteredDishes.map(d => d.price || 0).filter(p => p > 0);
    const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
    const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
    
    return { totalDishes, uniqueRestaurants, minPrice, maxPrice };
  }, [filteredDishes]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50">
        {/* Header with loading state */}
        <header className="bg-white/80 backdrop-blur-sm border-b border-orange-100 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🍽️</span>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
                    Sundbyberg Lunch
                  </h1>
                  <p className="text-xs text-gray-600">Laddar dagens lunchmeny...</p>
                </div>
              </div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
            </div>
          </div>
        </header>

        {/* Skeleton grid */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
            {Array.from({ length: 12 }).map((_, index) => (
              <DishCardSkeleton key={index} />
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-orange-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🍽️</span>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
                  Sundbyberg Lunch
                </h1>
                <p className="text-xs text-gray-600">Dagens bästa lunch i Sundbyberg centrum</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right text-sm">
                <p className="text-gray-500">v4.0 - Complete</p>
                <p className="font-medium text-gray-700">
                  {new Date().toLocaleTimeString('sv-SE', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <button
                onClick={fetchDishes}
                className="p-2 rounded-lg bg-orange-100 text-orange-600 hover:bg-orange-200 transition-colors"
                title="Uppdatera"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="bg-white/60 backdrop-blur-sm border-b border-orange-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="group hover:scale-105 transition-transform duration-200">
              <p className="text-3xl font-bold text-gray-900">
                <AnimatedCounter end={stats.totalDishes} />
              </p>
              <p className="text-sm text-gray-600 font-medium">rätter att välja på</p>
            </div>
            <div className="group hover:scale-105 transition-transform duration-200">
              <p className="text-3xl font-bold text-gray-900">
                <AnimatedCounter end={stats.uniqueRestaurants} />
              </p>
              <p className="text-sm text-gray-600 font-medium">olika kök</p>
            </div>
            <div className="group hover:scale-105 transition-transform duration-200">
              <p className="text-2xl font-bold text-gray-900">
                {stats.minPrice}-{stats.maxPrice} kr
              </p>
              <p className="text-sm text-gray-600 font-medium">Prisintervall</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <FilterBar
        restaurants={restaurants}
        categories={categories}
        filters={filters}
        onFiltersChange={setFilters}
      />

      {/* Dishes Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {filteredDishes.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
            {filteredDishes.map((dish, index) => (
              <DishCard key={`${dish.restaurant}-${dish.name}-${index}`} dish={dish} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-medium text-gray-900 mb-2">Inga rätter hittades</h3>
            <p className="text-gray-600 mb-6">Prova att ändra dina filter för att se fler alternativ</p>
            <button 
              onClick={() => setFilters({ restaurant: '', category: '', search: '', sortBy: 'distance' })}
              className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              <Filter className="w-4 h-4 mr-2" />
              Rensa filter
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-sm border-t border-orange-100 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-600">
            <p>🏢 Perfekt för lunch i Sundbyberg centrum</p>
            <p className="mt-1">Avstånd visar gångtid från centrala Sundbyberg</p>
          </div>
        </div>
      </footer>
    </div>
  );
}