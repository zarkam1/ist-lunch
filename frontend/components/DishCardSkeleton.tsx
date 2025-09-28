export default function DishCardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 animate-pulse">
      {/* Price badge skeleton */}
      <div className="absolute top-4 right-4">
        <div className="bg-gray-200 h-6 w-16 rounded-md"></div>
      </div>

      {/* Category emoji skeleton */}
      <div className="bg-gray-200 h-6 w-6 rounded mb-3"></div>
      
      {/* Dish Header skeleton */}
      <div className="mb-4 pr-16">
        <div className="bg-gray-300 h-6 w-3/4 rounded mb-2"></div>
        <div className="bg-gray-200 h-4 w-full rounded mb-1"></div>
        <div className="bg-gray-200 h-4 w-2/3 rounded"></div>
      </div>

      {/* Footer skeleton */}
      <div className="flex items-center justify-between mt-auto pt-3">
        <div className="flex items-center gap-1.5">
          <div className="bg-gray-200 h-3 w-16 rounded"></div>
          <span className="text-gray-200">•</span>
          <div className="bg-gray-200 h-3 w-12 rounded"></div>
        </div>
        <div className="bg-gray-200 h-6 w-12 rounded"></div>
      </div>
    </div>
  );
}