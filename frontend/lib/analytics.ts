// Simple, privacy-friendly analytics without cookies
// Tracks dish views, clicks, and patterns

interface AnalyticsEvent {
  action: 'view' | 'click' | 'filter' | 'search' | 'category_interest' | 'price_range_view';
  dish_id?: string;
  dish_name?: string;
  restaurant?: string;
  category?: string;
  filter_type?: string;
  search_term?: string;
  price_range?: string;
  timestamp: string;
  day_of_week: number;
  hour: number;
  session_id: string;
}

class Analytics {
  private events: AnalyticsEvent[] = [];
  private readonly maxEvents = 1000;
  private sessionId: string;

  constructor() {
    // Generate session ID
    this.sessionId = Date.now().toString(36) + Math.random().toString(36).substr(2);
    
    // Load existing events from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sundbyberg_lunch_analytics');
      if (stored) {
        try {
          this.events = JSON.parse(stored);
        } catch (e) {
          console.warn('Failed to load analytics data');
        }
      }
    }
  }

  private saveEvents() {
    if (typeof window !== 'undefined') {
      // Keep only recent events to prevent unlimited growth
      if (this.events.length > this.maxEvents) {
        this.events = this.events.slice(-this.maxEvents);
      }
      
      localStorage.setItem('sundbyberg_lunch_analytics', JSON.stringify(this.events));
    }
  }

  private createEvent(action: AnalyticsEvent['action'], data: Partial<AnalyticsEvent> = {}): AnalyticsEvent {
    const now = new Date();
    return {
      action,
      timestamp: now.toISOString(),
      day_of_week: now.getDay(),
      hour: now.getHours(),
      session_id: this.sessionId,
      ...data
    };
  }

  private getPriceRange(price: number): string {
    if (price < 100) return 'under-100';
    if (price < 150) return '100-150';
    if (price < 200) return '150-200';
    return 'over-200';
  }

  // Track when a dish is viewed (appears in viewport)
  trackDishView(dish: { name: string; restaurant: string; category: string; price?: number }) {
    const event = this.createEvent('view', {
      dish_id: `${dish.restaurant}-${dish.name}`.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      dish_name: dish.name,
      restaurant: dish.restaurant,
      category: dish.category,
      price_range: dish.price ? this.getPriceRange(dish.price) : undefined
    });
    
    this.events.push(event);
    this.saveEvents();
  }

  // Track when a dish card is clicked
  trackDishClick(dish: { name: string; restaurant: string; category: string }) {
    const event = this.createEvent('click', {
      dish_id: `${dish.restaurant}-${dish.name}`.toLowerCase().replace(/[^a-z0-9]/g, '-'),
      dish_name: dish.name,
      restaurant: dish.restaurant,
      category: dish.category
    });
    
    this.events.push(event);
    this.saveEvents();
  }

  // Track filter usage
  trackFilter(filterType: string, value: string) {
    const event = this.createEvent('filter', {
      filter_type: filterType,
      search_term: value
    });
    
    this.events.push(event);
    this.saveEvents();
  }

  // Track search usage
  trackSearch(searchTerm: string) {
    const event = this.createEvent('search', {
      search_term: searchTerm
    });
    
    this.events.push(event);
    this.saveEvents();
  }

  // Get insights for debugging/admin
  getInsights() {
    if (this.events.length === 0) return null;

    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const recentEvents = this.events.filter(e => new Date(e.timestamp) > weekAgo);

    // Most popular dishes
    const dishViews = recentEvents
      .filter(e => e.action === 'view' && e.dish_name)
      .reduce((acc, e) => {
        const key = `${e.dish_name} - ${e.restaurant}`;
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

    // Most popular categories
    const categoryViews = recentEvents
      .filter(e => e.action === 'view' && e.category)
      .reduce((acc, e) => {
        acc[e.category!] = (acc[e.category!] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

    // Peak hours
    const hourViews = recentEvents
      .filter(e => e.action === 'view')
      .reduce((acc, e) => {
        acc[e.hour] = (acc[e.hour] || 0) + 1;
        return acc;
      }, {} as Record<number, number>);

    // Most popular day
    const dayViews = recentEvents
      .filter(e => e.action === 'view')
      .reduce((acc, e) => {
        acc[e.day_of_week] = (acc[e.day_of_week] || 0) + 1;
        return acc;
      }, {} as Record<number, number>);

    return {
      totalEvents: this.events.length,
      recentEvents: recentEvents.length,
      topDishes: Object.entries(dishViews)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10),
      topCategories: Object.entries(categoryViews)
        .sort(([,a], [,b]) => b - a),
      peakHours: Object.entries(hourViews)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .map(([hour, views]) => ({ hour: parseInt(hour), views })),
      popularDays: Object.entries(dayViews)
        .sort(([,a], [,b]) => b - a)
        .map(([day, views]) => ({ 
          day: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][parseInt(day)], 
          views 
        }))
    };
  }

  // Clear all analytics data (for privacy)
  clearData() {
    this.events = [];
    if (typeof window !== 'undefined') {
      localStorage.removeItem('sundbyberg_lunch_analytics');
    }
  }
}

// Export singleton instance
export const analytics = new Analytics();

// Hook for React components
export function useAnalytics() {
  return analytics;
}