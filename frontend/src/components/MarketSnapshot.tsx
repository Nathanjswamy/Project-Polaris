import { TrendingUp, Users, Map, Star, AlertTriangle } from "lucide-react";

export default function MarketSnapshot({ overview, cafeTypes }) {
  if (!overview) return null;

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Total Cafés */}
      <div className="glass-panel p-5 rounded-lg flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[var(--text-secondary)] text-sm font-mono uppercase tracking-wider">Indexed Cafés</span>
          <Map className="text-[var(--chai)] w-5 h-5" />
        </div>
        <div>
          <span className="text-4xl font-display">{overview.total_cafes || 0}</span>
          <div className="mt-2 text-xs text-[var(--cardamom)] flex items-center gap-1">
            <span className="font-mono">100%</span>
            <span>real extraction</span>
          </div>
        </div>
      </div>

      {/* Reviews (Footfall Proxy) */}
      <div className="glass-panel p-5 rounded-lg flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[var(--text-secondary)] text-sm font-mono uppercase tracking-wider">Total Signals</span>
          <Users className="text-[var(--chai)] w-5 h-5" />
        </div>
        <div>
          <span className="text-4xl font-display">
            {(overview.total_reviews || 0).toLocaleString()}
          </span>
          <div className="mt-2 text-xs text-[var(--text-secondary)]">
            Total reviews across dataset
          </div>
        </div>
      </div>

      {/* Top Category */}
      <div className="glass-panel p-5 rounded-lg col-span-2">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[var(--text-secondary)] text-sm font-mono uppercase tracking-wider">Top Formats</span>
          <TrendingUp className="text-[var(--chai)] w-5 h-5" />
        </div>
        <div className="space-y-3">
          {cafeTypes && cafeTypes.length > 0 ? (
            cafeTypes
              .sort((a, b) => b.count - a.count)
              .slice(0, 3)
              .map((type, i) => (
                <div key={type.cafe_type} className="flex items-center justify-between">
                  <span className="text-[var(--text-primary)] font-medium capitalize">
                    {type.cafe_type.replace(/_/g, " ")}
                  </span>
                  <div className="flex items-center gap-4 text-sm font-mono text-[var(--text-secondary)]">
                    <span>{type.count} locations</span>
                    <span className="flex items-center text-[var(--cardamom)]">
                      {type.avg_rating?.toFixed(1) || "-"} <Star className="w-3 h-3 ml-1 fill-current" />
                    </span>
                  </div>
                </div>
              ))
          ) : (
            <div className="text-sm text-[var(--text-tertiary)] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Not enough data to classify types.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
