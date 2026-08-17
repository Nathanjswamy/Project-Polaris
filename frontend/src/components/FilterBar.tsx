import { Filter, X } from "lucide-react";

export default function FilterBar({ filters, activeFilters, onFilterChange }) {
  if (!filters) return null;

  const hasActiveFilters = Object.values(activeFilters).some(v => v !== "");

  const handleClear = () => {
    onFilterChange({
      neighborhood: "",
      cafeType: "",
      priceLevel: "",
    });
  };

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2 text-sm text-[var(--text-secondary)] font-mono">
        <Filter size={14} />
        <span>FILTERS</span>
      </div>
      
      <select 
        value={activeFilters.neighborhood}
        onChange={(e) => onFilterChange({...activeFilters, neighborhood: e.target.value})}
        className="bg-[var(--surface-alt)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded px-3 py-1.5 text-sm outline-none focus:border-[var(--chai)] transition-colors"
      >
        <option value="">All Neighborhoods</option>
        {filters.neighborhoods?.map(n => (
          <option key={n} value={n}>{n}</option>
        ))}
      </select>

      <select 
        value={activeFilters.cafeType}
        onChange={(e) => onFilterChange({...activeFilters, cafeType: e.target.value})}
        className="bg-[var(--surface-alt)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded px-3 py-1.5 text-sm outline-none focus:border-[var(--chai)] transition-colors capitalize"
      >
        <option value="">All Formats</option>
        {filters.cafe_types?.map(t => (
          <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
        ))}
      </select>
      
      <select 
        value={activeFilters.priceLevel}
        onChange={(e) => onFilterChange({...activeFilters, priceLevel: e.target.value})}
        className="bg-[var(--surface-alt)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded px-3 py-1.5 text-sm outline-none focus:border-[var(--chai)] transition-colors"
      >
        <option value="">Any Price</option>
        {filters.price_levels?.map(p => (
          <option key={p} value={p}>{Array(p).fill("₹").join("")}</option>
        ))}
      </select>

      {hasActiveFilters && (
        <button 
          onClick={handleClear}
          className="flex items-center gap-1 text-xs font-mono text-[var(--chili)] hover:text-[var(--text-primary)] transition-colors px-2 py-1"
        >
          <X size={12} /> CLEAR
        </button>
      )}
    </div>
  );
}
