/**
 * Skeleton loader components for better loading states
 */

export function SkeletonCard() {
  return (
    <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 animate-pulse">
      <div className="h-4 bg-slate-800 rounded w-3/4 mb-4"></div>
      <div className="h-3 bg-slate-800 rounded w-1/2 mb-2"></div>
      <div className="h-3 bg-slate-800 rounded w-2/3"></div>
    </div>
  );
}

export function SkeletonClipGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {[...Array(8)].map((_, i) => (
        <div key={i} className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden animate-pulse">
          <div className="aspect-[9/16] bg-slate-800"></div>
          <div className="p-4">
            <div className="h-3 bg-slate-800 rounded w-3/4 mb-2"></div>
            <div className="h-2 bg-slate-800 rounded w-1/2"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonJobList() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-xl p-6 animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="h-5 bg-slate-800 rounded w-1/3 mb-3"></div>
              <div className="h-3 bg-slate-800 rounded w-1/4 mb-2"></div>
              <div className="h-3 bg-slate-800 rounded w-1/2"></div>
            </div>
            <div className="w-20 h-8 bg-slate-800 rounded-lg"></div>
          </div>
        </div>
      ))}
    </div>
  );
}
