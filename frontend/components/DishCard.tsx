import { MapPin, Clock } from 'lucide-react';
import { useAnalytics } from '../lib/analytics';
import { useEffect, useRef } from 'react';

interface Dish {
  name: string;
  restaurant: string;
  restaurant_id?: string;
  price: number;
  category: string;
  description?: string;
  walking_minutes?: number;
}

interface DishCardProps {
  dish: Dish;
}

// Price-based color mapping
const getPriceStyles = (price: number) => {
  if (price < 100) {
    return {
      badge: 'bg-green-100 text-green-800 border-green-200',
      icon: '💰',
      level: 'budget'
    };
  }
  if (price <= 150) {
    return {
      badge: 'bg-yellow-100 text-yellow-800 border-yellow-200', 
      icon: '💳',
      level: 'medium'
    };
  }
  return {
    badge: 'bg-orange-100 text-orange-800 border-orange-200',
    icon: '💎',
    level: 'premium'
  };
};

// Category color mapping
const getCategoryStyles = (category: string) => {
  const normalizedCategory = category?.toLowerCase() || '';
  
  if (normalizedCategory.includes('kött') || normalizedCategory.includes('meat')) {
    return {
      badge: 'bg-red-100 text-red-800 border-red-200',
      emoji: '🥩',
      accent: 'border-l-red-400'
    };
  }
  if (normalizedCategory.includes('fisk') || normalizedCategory.includes('fish')) {
    return {
      badge: 'bg-blue-100 text-blue-800 border-blue-200',
      emoji: '🐟',
      accent: 'border-l-blue-400'
    };
  }
  if (normalizedCategory.includes('vegetarisk') || normalizedCategory.includes('vegetarian')) {
    return {
      badge: 'bg-green-100 text-green-800 border-green-200',
      emoji: '🥗',
      accent: 'border-l-green-400'
    };
  }
  if (normalizedCategory.includes('vegansk') || normalizedCategory.includes('vegan')) {
    return {
      badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      emoji: '🌱',
      accent: 'border-l-emerald-400'
    };
  }
  if (normalizedCategory.includes('asiat') || normalizedCategory.includes('thai') || normalizedCategory.includes('sushi')) {
    return {
      badge: 'bg-purple-100 text-purple-800 border-purple-200',
      emoji: '🥢',
      accent: 'border-l-purple-400'
    };
  }
  if (normalizedCategory.includes('pizza')) {
    return {
      badge: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      emoji: '🍕',
      accent: 'border-l-yellow-400'
    };
  }
  if (normalizedCategory.includes('pasta')) {
    return {
      badge: 'bg-orange-100 text-orange-800 border-orange-200',
      emoji: '🍝',
      accent: 'border-l-orange-400'
    };
  }
  
  // Default
  return {
    badge: 'bg-gray-100 text-gray-800 border-gray-200',
    emoji: '🍽️',
    accent: 'border-l-gray-400'
  };
};

export default function DishCard({ dish }: DishCardProps) {
  const categoryStyles = getCategoryStyles(dish.category);
  const priceStyles = getPriceStyles(dish.price);
  const walkingTime = dish.walking_minutes || 5;
  const analytics = useAnalytics();
  const cardRef = useRef<HTMLDivElement>(null);
  const hasBeenViewed = useRef(false);

  // Track view when card enters viewport
  useEffect(() => {
    if (!cardRef.current || hasBeenViewed.current) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasBeenViewed.current) {
          analytics.trackDishView({
            name: dish.name,
            restaurant: dish.restaurant,
            category: dish.category,
            price: dish.price
          });
          hasBeenViewed.current = true;
        }
      },
      { threshold: 0.5 }
    );

    observer.observe(cardRef.current);
    return () => observer.disconnect();
  }, [dish, analytics]);

  const handleClick = () => {
    analytics.trackDishClick({
      name: dish.name,
      restaurant: dish.restaurant,
      category: dish.category
    });
  };

  return (
    <div 
      ref={cardRef}
      onClick={handleClick}
      className="bg-white rounded-lg shadow-sm border border-gray-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 p-5 group cursor-pointer relative overflow-hidden"
      style={{ 
        minHeight: '200px'
      }}
    >
      {/* Top row: Category icon left, price badge right */}
      <div className="flex justify-between items-start mb-3">
        <span className="text-2xl">{categoryStyles.emoji}</span>
        <div className={`${priceStyles.badge} border px-3 py-1.5 rounded-full text-sm font-semibold`}>
          {dish.price} kr
        </div>
      </div>

      {/* Dish name - BIGGEST and BOLDEST */}
      <h3 className="text-xl font-bold text-gray-900 mb-2 leading-tight">
        {dish.name}
      </h3>

      {/* Description - 2-3 lines, gray, smaller */}
      <p className="text-sm text-gray-600 leading-relaxed mb-4" style={{ minHeight: '2.5rem' }}>
        {dish.description || "Klassisk rätt med dagens ingredienser"}
      </p>

      {/* Separator line */}
      <div className="border-t border-gray-100 pt-3 mt-auto">
        {/* Restaurant info - VERY subtle at bottom */}
        <div className="flex items-center text-xs text-gray-400">
          <span className="mr-1">🍽️</span>
          <span>{dish.restaurant}</span>
          <span className="mx-2">•</span>
          <span className="mr-1">🚶</span>
          <span>{walkingTime} min</span>
        </div>
      </div>

    </div>
  );
}