import { Search, Filter, ArrowUpDown } from 'lucide-react';
import { useAnalytics } from '../lib/analytics';

interface Filters {
  restaurant: string;
  category: string;
  search: string;
  sortBy: 'price-asc' | 'price-desc' | 'distance' | 'name';
}

interface FilterBarProps {
  restaurants: string[];
  categories: string[];
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
}

export default function FilterBar({ restaurants, categories, filters, onFiltersChange }: FilterBarProps) {
  const analytics = useAnalytics();
  
  const updateFilter = (key: keyof Filters, value: string) => {
    onFiltersChange({ ...filters, [key]: value });
    
    // Track filter usage
    if (key === 'search' && value) {
      analytics.trackSearch(value);
    } else if (key !== 'search' && value) {
      analytics.trackFilter(key, value);
    }
  };

  const clearFilters = () => {
    onFiltersChange({ restaurant: '', category: '', search: '', sortBy: 'price-asc' });
  };

  const hasActiveFilters = filters.restaurant || filters.category || filters.search;

  return (
    <div className="bg-white/80 backdrop-blur-sm border-b border-orange-100 sticky top-16 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          
          {/* Search Bar - enhanced with gradient focus */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 transition-colors duration-200" />
            <input
              type="text"
              placeholder="Sök rätter..."
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white/90 hover:bg-white transition-all duration-200 focus:shadow-md"
            />
          </div>

          {/* Restaurant Dropdown - enhanced */}
          <select
            value={filters.restaurant}
            onChange={(e) => updateFilter('restaurant', e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white/90 hover:bg-white min-w-[160px] transition-all duration-200 focus:shadow-md cursor-pointer hover:border-gray-300"
          >
            <option value="">📍 Alla restauranger</option>
            {restaurants.map(restaurant => (
              <option key={restaurant} value={restaurant}>{restaurant}</option>
            ))}
          </select>

          {/* Category Filter - enhanced */}
          <select
            value={filters.category}
            onChange={(e) => updateFilter('category', e.target.value)}
            className="px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white/90 hover:bg-white min-w-[140px] transition-all duration-200 focus:shadow-md cursor-pointer hover:border-gray-300"
          >
            <option value="">🏷️ Alla kategorier</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          {/* Sort Dropdown - enhanced */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-gray-500 transition-colors duration-200" />
            <select
              value={filters.sortBy}
              onChange={(e) => updateFilter('sortBy', e.target.value as 'price-asc' | 'price-desc' | 'distance' | 'name')}
              className="px-3 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white/90 hover:bg-white transition-all duration-200 focus:shadow-md cursor-pointer hover:border-gray-300"
            >
              <option value="price-asc">💰 Pris (Lägst först)</option>
              <option value="price-desc">💎 Pris (Högst först)</option>
              <option value="distance">📍 Avstånd (Närmast först)</option>
              <option value="name">🔤 Namn (A-Ö)</option>
            </select>
          </div>

          {/* Clear Filters - colorful button */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center px-4 py-2.5 text-sm bg-gradient-to-r from-red-500 to-pink-500 text-white hover:from-red-600 hover:to-pink-600 rounded-lg transition-all duration-200 hover:shadow-md hover:scale-105 active:scale-95"
            >
              <Filter className="w-4 h-4 mr-1" />
              Rensa
            </button>
          )}
        </div>

        {/* Active Filters Display - enhanced with gradients */}
        {hasActiveFilters && (
          <div className="flex flex-wrap gap-2 mt-3">
            {filters.restaurant && (
              <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-orange-400 to-amber-400 text-white text-sm rounded-full shadow-sm hover:shadow-md transition-all duration-200">
                📍 {filters.restaurant}
                <button
                  onClick={() => updateFilter('restaurant', '')}
                  className="ml-2 text-white hover:text-orange-100 bg-white/20 hover:bg-white/30 rounded-full w-5 h-5 flex items-center justify-center text-xs transition-all duration-200"
                >
                  ×
                </button>
              </span>
            )}
            {filters.category && (
              <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-blue-400 to-cyan-400 text-white text-sm rounded-full shadow-sm hover:shadow-md transition-all duration-200">
                🏷️ {filters.category}
                <button
                  onClick={() => updateFilter('category', '')}
                  className="ml-2 text-white hover:text-blue-100 bg-white/20 hover:bg-white/30 rounded-full w-5 h-5 flex items-center justify-center text-xs transition-all duration-200"
                >
                  ×
                </button>
              </span>
            )}
            {filters.search && (
              <span className="inline-flex items-center px-3 py-1.5 bg-gradient-to-r from-green-400 to-emerald-400 text-white text-sm rounded-full shadow-sm hover:shadow-md transition-all duration-200">
                🔍 "{filters.search}"
                <button
                  onClick={() => updateFilter('search', '')}
                  className="ml-2 text-white hover:text-green-100 bg-white/20 hover:bg-white/30 rounded-full w-5 h-5 flex items-center justify-center text-xs transition-all duration-200"
                >
                  ×
                </button>
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}