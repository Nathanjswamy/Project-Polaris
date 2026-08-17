"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { Coffee, MapPin, TrendingUp, AlertTriangle, Info, Clock, CheckCircle, Activity, Star } from "lucide-react";

// The Map component needs to be dynamically imported with SSR disabled
// because Leaflet requires the window object which isn't available on the server.
const NeighborhoodMap = dynamic(() => import("../components/NeighborhoodMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-[var(--surface)] border border-[var(--border-subtle)] flex items-center justify-center">
      <div className="flex flex-col items-center text-[var(--text-secondary)]">
        <Activity className="w-8 h-8 mb-4 animate-pulse text-[var(--chai)]" />
        <span className="font-mono text-sm">Loading telemetry...</span>
      </div>
    </div>
  ),
});

import MarketSnapshot from "../components/MarketSnapshot";
import CompetitiveTable from "../components/CompetitiveTable";
import ProvenanceFooter from "../components/ProvenanceFooter";
import FilterBar from "../components/FilterBar";
import EmptyState from "../components/EmptyState";

export default function Dashboard() {
  const [isClient, setIsClient] = useState(false);
  const [data, setData] = useState({
    overview: null,
    neighborhoods: [],
    cafeTypes: [],
    rankings: [],
    points: [],
    provenance: null,
    filters: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filter state
  const [activeFilters, setActiveFilters] = useState({
    neighborhood: "",
    cafeType: "",
    priceLevel: "",
  });

  useEffect(() => {
    setIsClient(true);
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Build query string
      const params = new URLSearchParams();
      if (activeFilters.neighborhood) params.append("neighborhood", activeFilters.neighborhood);
      if (activeFilters.cafeType) params.append("cafe_type", activeFilters.cafeType);
      if (activeFilters.priceLevel) params.append("price_level", activeFilters.priceLevel);
      const query = params.toString() ? `?${params.toString()}` : "";

      // Fetch all needed data
      const [
        overviewRes, 
        neighborhoodsRes, 
        cafeTypesRes, 
        rankingsRes, 
        pointsRes, 
        provenanceRes,
        filtersRes
      ] = await Promise.all([
        fetch(`http://localhost:8000/api/overview${query}`),
        fetch("http://localhost:8000/api/neighborhoods"),
        fetch("http://localhost:8000/api/cafe-types"),
        fetch(`http://localhost:8000/api/competitors/ranking${query}&limit=20`),
        fetch("http://localhost:8000/api/geographic"),
        fetch("http://localhost:8000/api/provenance"),
        fetch("http://localhost:8000/api/filters"),
      ]);

      if (!overviewRes.ok) throw new Error("Failed to fetch data from backend");

      setData({
        overview: await overviewRes.json(),
        neighborhoods: await neighborhoodsRes.json(),
        cafeTypes: await cafeTypesRes.json(),
        rankings: (await rankingsRes.json()).rankings || [],
        points: (await pointsRes.json()).points || [],
        provenance: await provenanceRes.json(),
        filters: await filtersRes.json(),
      });
    } catch (err) {
      console.error(err);
      setError("Failed to connect to backend API. Ensure the FastAPI server is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [activeFilters]);

  // Don't render until hydration is complete to avoid mismatched HTML
  if (!isClient) return null;

  return (
    <div className="flex flex-col min-h-screen">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 glass-panel-solid border-b border-[var(--border-subtle)] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[var(--chai)] flex items-center justify-center text-[var(--ink)]">
            <Coffee size={18} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="text-xl m-0 leading-none">POLARIS</h1>
            <span className="text-xs font-mono text-[var(--text-tertiary)] uppercase tracking-wider">
              Hyderabad Café Intelligence
            </span>
          </div>
        </div>
        
        {data.filters && !error && (
          <FilterBar 
            filters={data.filters} 
            activeFilters={activeFilters}
            onFilterChange={setActiveFilters}
          />
        )}
      </header>

      <main className="flex-1 p-6 space-y-6 max-w-[1600px] mx-auto w-full">
        {error ? (
          <EmptyState 
            icon={<AlertTriangle className="w-12 h-12 text-[var(--chili)]" />}
            title="Backend Connection Failed"
            description={error}
            actionText="Retry Connection"
            onAction={fetchDashboardData}
          />
        ) : loading && !data.overview ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-pulse">
            <div className="lg:col-span-2 h-[500px] bg-[var(--surface)] border border-[var(--border-subtle)] rounded-lg"></div>
            <div className="h-[500px] bg-[var(--surface)] border border-[var(--border-subtle)] rounded-lg"></div>
          </div>
        ) : data.points.length === 0 ? (
          <EmptyState 
            icon={<MapPin className="w-12 h-12 text-[var(--chai)]" />}
            title="No Data Available"
            description="The dataset is empty. You need to run the extraction pipeline."
            actionText="How to run extraction"
            onAction={() => alert("Run: python -m src.etl.pipeline --extract")}
          />
        ) : (
          <>
            {/* Top Row: Map & Snapshot */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
              <div className="lg:col-span-2 rounded-lg overflow-hidden border border-[var(--border-subtle)] shadow-xl relative group">
                <div className="absolute top-4 left-4 z-[400] bg-[var(--surface)]/90 backdrop-blur border border-[var(--border-subtle)] px-3 py-2 rounded text-sm font-mono flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[var(--cardamom)] animate-pulse"></span>
                  {data.points.length} locations tracking
                </div>
                <NeighborhoodMap 
                  points={data.points} 
                  onNeighborhoodSelect={(n) => setActiveFilters({...activeFilters, neighborhood: n})} 
                />
              </div>
              
              <div className="flex flex-col gap-6">
                <MarketSnapshot 
                  overview={data.overview} 
                  cafeTypes={data.cafeTypes} 
                />
                
                {/* Opportunity Panel directly beneath snapshot */}
                <div className="glass-panel p-5 rounded-lg flex-1 flex flex-col">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp size={18} className="text-[var(--chai)]" />
                    <h2 className="text-lg">Opportunity Zones</h2>
                  </div>
                  <div className="space-y-4 flex-1 overflow-y-auto pr-2">
                    {data.neighborhoods
                      .filter(n => n.avg_rating && n.avg_density)
                      .sort((a, b) => b.total_reviews - a.total_reviews)
                      .slice(0, 3)
                      .map((n, i) => (
                      <div key={i} className="bg-[var(--surface-alt)] p-3 rounded border border-[var(--border-subtle)] hover:border-[var(--chai)]/50 transition-colors cursor-pointer" onClick={() => setActiveFilters({...activeFilters, neighborhood: n.neighborhood})}>
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-medium text-[var(--text-primary)]">{n.neighborhood}</span>
                          <span className="font-mono text-xs bg-[var(--surface)] px-2 py-0.5 rounded text-[var(--text-secondary)]">Rank {i+1}</span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                          High demand ({n.total_reviews} reviews) vs {n.cafe_count} cafés. 
                          Average rating is {n.avg_rating}.
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Row: Competitive Rankings */}
            <div className="glass-panel rounded-lg overflow-hidden">
              <CompetitiveTable rankings={data.rankings} />
            </div>
          </>
        )}
      </main>

      {data.provenance && (
        <ProvenanceFooter manifest={data.provenance} />
      )}
    </div>
  );
}
