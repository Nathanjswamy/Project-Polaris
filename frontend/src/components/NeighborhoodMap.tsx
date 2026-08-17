"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { Star, MessageSquare } from "lucide-react";

// Helper component to recenter map when points change
function MapRecenter({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points && points.length > 0) {
      // Calculate bounds
      const lats = points.map(p => p.latitude).filter(l => l !== null);
      const lngs = points.map(p => p.longitude).filter(l => l !== null);
      
      if (lats.length > 0 && lngs.length > 0) {
        const minLat = Math.min(...lats);
        const maxLat = Math.max(...lats);
        const minLng = Math.min(...lngs);
        const maxLng = Math.max(...lngs);
        
        // Add padding
        const latPad = (maxLat - minLat) * 0.1 || 0.05;
        const lngPad = (maxLng - minLng) * 0.1 || 0.05;
        
        map.fitBounds([
          [minLat - latPad, minLng - lngPad],
          [maxLat + latPad, maxLng + lngPad]
        ]);
      }
    }
  }, [points, map]);
  return null;
}

export default function NeighborhoodMap({ points, onNeighborhoodSelect }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Hyderabad center roughly
  const center = [17.42, 78.41];

  return (
    <div className="h-full w-full relative z-0">
      <MapContainer 
        center={center} 
        zoom={13} 
        style={{ height: "100%", width: "100%" }}
        zoomControl={false}
      >
        {/* Dark map tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        <MapRecenter points={points} />

        {points.map((point) => (
          point.latitude && point.longitude ? (
            <CircleMarker
              key={point.place_id}
              center={[point.latitude, point.longitude]}
              radius={Math.max(6, Math.min(15, (point.review_count || 100) / 100))}
              fillColor="var(--chai)"
              color="var(--ink)"
              weight={2}
              opacity={1}
              fillOpacity={0.7}
              eventHandlers={{
                click: () => {
                  if (onNeighborhoodSelect && point.neighborhood) {
                    // Optional: filter by this neighborhood on click
                  }
                },
              }}
            >
              <Popup className="polaris-popup">
                <div className="p-1">
                  <h3 className="font-medium text-base mb-1 leading-tight">{point.name}</h3>
                  <div className="text-xs text-[var(--text-secondary)] mb-3 flex items-center gap-1">
                    {point.neighborhood} • <span className="capitalize">{point.cafe_type ? point.cafe_type.replace(/_/g, " ") : "Unknown"}</span>
                  </div>
                  
                  <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-2 mt-2">
                    <div className="flex items-center gap-1 text-[var(--cardamom)]">
                      <Star size={14} className="fill-current" />
                      <span className="font-mono">{point.rating ? point.rating.toFixed(1) : "-"}</span>
                    </div>
                    <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
                      <MessageSquare size={14} />
                      <span className="font-mono">{point.review_count}</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          ) : null
        ))}
      </MapContainer>
      
      {/* Overlay gradient for styling */}
      <div className="absolute inset-0 pointer-events-none border border-[var(--border-subtle)] rounded-lg shadow-inner z-[1000]"></div>
    </div>
  );
}
