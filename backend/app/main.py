"""
Project Polaris — FastAPI Backend (Real Data Adapted)
=====================================================

Serves analytics computed from the real extracted dataset via REST API.
Removed all synthetic time-series endpoints and "Simulated Dataset" references.
"""

import json
import os
import sys
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.analytics.competitive import get_competitor_ranking, compare_businesses, get_positioning_data
from src.analytics.clustering import run_segmentation
from src.analytics.correlation import compute_correlation_matrix, compute_drivers_analysis
from src.analytics.opportunities import detect_opportunities


# ---------------------------------------------------------------------------
# Load data once at startup
# ---------------------------------------------------------------------------

DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "polaris_cafes.csv")
METADATA_DIR = os.path.join(PROJECT_ROOT, "data", "metadata")

_df = None
_manifest = None


def get_df() -> pd.DataFrame:
    """Lazy-load and cache the processed dataset."""
    global _df
    if _df is None:
        if not os.path.exists(DATA_PATH):
            # Return empty structure if pipeline hasn't run yet
            return pd.DataFrame(columns=[
                "place_id", "name", "neighborhood", "zone", "cafe_type",
                "rating", "review_count", "sentiment_score", "competitive_score"
            ])
        _df = pd.read_csv(DATA_PATH)
    return _df


def get_manifest() -> dict:
    """Load pipeline manifest for provenance."""
    global _manifest
    if _manifest is None:
        path = os.path.join(METADATA_DIR, "pipeline_manifest.json")
        if os.path.exists(path):
            with open(path) as f:
                _manifest = json.load(f)
        else:
            _manifest = {"error": "Pipeline manifest not found. Run the ETL pipeline first."}
    return _manifest


def apply_filters(df: pd.DataFrame,
                  neighborhood: Optional[str] = None,
                  cafe_type: Optional[str] = None,
                  price_level: Optional[int] = None) -> pd.DataFrame:
    """Apply global filters to the dataset."""
    if neighborhood:
        df = df[df["neighborhood"] == neighborhood]
    if cafe_type:
        df = df[df["cafe_type"] == cafe_type]
    if price_level:
        df = df[df["price_level"] == price_level]
    return df


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Project Polaris API",
    description="Hyderabad Café Intelligence. Grounded entirely in real extracted data.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "Project Polaris API", "version": "3.0.0", "dataset": "Real"}


@app.get("/health")
def health():
    df = get_df()
    return {"status": "ok", "records": len(df), "columns": len(df.columns)}


# ===== PROVENANCE & METADATA =====

@app.get("/api/provenance")
def get_provenance():
    """Return pipeline manifest showing exactly where data came from."""
    return get_manifest()


@app.get("/api/filters")
def get_filters():
    """Get available filter values."""
    df = get_df()
    if len(df) == 0:
        return {"neighborhoods": [], "cafe_types": [], "price_levels": []}
        
    return {
        "neighborhoods": sorted([x for x in df["neighborhood"].unique().tolist() if pd.notna(x)]),
        "cafe_types": sorted([x for x in df["cafe_type"].unique().tolist() if pd.notna(x)]),
        "price_levels": sorted([int(x) for x in df["price_level"].unique().tolist() if pd.notna(x)]),
    }


# ===== OVERVIEW & AGGREGATES =====

@app.get("/api/overview")
def get_overview(
    neighborhood: Optional[str] = None,
    cafe_type: Optional[str] = None,
    price_level: Optional[int] = None,
):
    """Snapshot overview of the market based on filters."""
    df = apply_filters(get_df().copy(), neighborhood, cafe_type, price_level)
    if len(df) == 0:
        return {"error": "No data matching filters"}
        
    return {
        "total_cafes": len(df),
        "avg_rating": round(float(df["rating"].mean()), 2) if "rating" in df and not df["rating"].empty else None,
        "total_reviews": int(df["review_count"].sum()) if "review_count" in df and not df["review_count"].empty else 0,
        "avg_sentiment": round(float(df["sentiment_score"].mean()), 3) if "sentiment_score" in df and not df["sentiment_score"].empty else None,
        "top_neighborhood": df.groupby("neighborhood")["rating"].mean().idxmax() if "neighborhood" in df and len(df["neighborhood"].dropna()) > 0 else None,
    }


@app.get("/api/neighborhoods")
def get_neighborhoods():
    """Aggregate stats by real Hyderabad neighborhoods."""
    df = get_df()
    if len(df) == 0:
        return []
        
    stats = df.groupby("neighborhood").agg(
        cafe_count=("place_id", "count"),
        avg_rating=("rating", "mean"),
        total_reviews=("review_count", "sum"),
        avg_density=("density_1km", "mean")
    ).reset_index()
    
    # Fill NaN with None for JSON serialization
    stats = stats.where(pd.notna(stats), None)
    
    return [
        {
            "neighborhood": row["neighborhood"],
            "cafe_count": int(row["cafe_count"]),
            "avg_rating": round(float(row["avg_rating"]), 2) if row["avg_rating"] is not None else None,
            "total_reviews": int(row["total_reviews"]),
            "avg_density": round(float(row["avg_density"]), 1) if row["avg_density"] is not None else None,
        }
        for _, row in stats.iterrows()
    ]


@app.get("/api/cafe-types")
def get_cafe_types():
    """Aggregate stats by classified café types (Irani, Filter, etc.)."""
    df = get_df()
    if len(df) == 0:
        return []
        
    stats = df.groupby("cafe_type").agg(
        count=("place_id", "count"),
        avg_rating=("rating", "mean"),
    ).reset_index()
    
    stats = stats.where(pd.notna(stats), None)
    
    return [
        {
            "cafe_type": row["cafe_type"],
            "count": int(row["count"]),
            "avg_rating": round(float(row["avg_rating"]), 2) if row["avg_rating"] is not None else None,
        }
        for _, row in stats.iterrows()
    ]


# ===== COMPETITORS =====

@app.get("/api/competitors/ranking")
def get_ranking(
    limit: int = 50,
    neighborhood: Optional[str] = None,
    cafe_type: Optional[str] = None,
):
    """Rank cafés by computed competitive score."""
    df = apply_filters(get_df().copy(), neighborhood, cafe_type)
    if len(df) == 0:
        return {"rankings": []}
        
    # We need to adapt the df shape to what competitive.py expects (date column, etc)
    # Or just write a simpler ranking here since we dropped time-series
    ranked = df.sort_values("competitive_score", ascending=False).head(limit)
    
    rankings = []
    for rank, (_, row) in enumerate(ranked.iterrows(), 1):
        rankings.append({
            "rank": rank,
            "place_id": row.get("place_id"),
            "name": row.get("name"),
            "neighborhood": row.get("neighborhood"),
            "cafe_type": row.get("cafe_type"),
            "rating": round(float(row.get("rating", 0)), 2) if pd.notna(row.get("rating")) else None,
            "review_count": int(row.get("review_count", 0)),
            "sentiment_score": round(float(row.get("sentiment_score", 0)), 3) if pd.notna(row.get("sentiment_score")) else None,
            "competitive_score": round(float(row.get("competitive_score", 0)), 1) if pd.notna(row.get("competitive_score")) else None,
        })

    return {
        "total_businesses": len(df),
        "rankings": rankings,
    }


# ===== DISTRIBUTION & GEOGRAPHIC =====

@app.get("/api/distribution")
def get_distribution(metric: str = "rating"):
    """Get histogram data for a metric."""
    df = get_df()
    if len(df) == 0 or metric not in df.columns:
        return {"histogram": []}
        
    data = df[metric].dropna()
    if len(data) == 0:
        return {"histogram": []}
        
    # Create histogram bins
    if metric == "rating":
        bins = np.arange(1.0, 5.5, 0.5)
    else:
        bins = 10
        
    counts, edges = np.histogram(data, bins=bins)
    
    histogram = []
    for i in range(len(counts)):
        histogram.append({
            "bin_start": round(float(edges[i]), 2),
            "bin_end": round(float(edges[i+1]), 2),
            "count": int(counts[i]),
        })
        
    return {"metric": metric, "histogram": histogram}


@app.get("/api/geographic")
def get_geographic():
    """Returns all café coordinates for the hero map."""
    df = get_df()
    if len(df) == 0:
        return {"points": []}
        
    points = []
    for _, row in df.iterrows():
        if pd.notna(row.get("latitude")) and pd.notna(row.get("longitude")):
            points.append({
                "place_id": row.get("place_id"),
                "name": row.get("name"),
                "latitude": round(float(row["latitude"]), 6),
                "longitude": round(float(row["longitude"]), 6),
                "rating": round(float(row.get("rating", 0)), 2) if pd.notna(row.get("rating")) else None,
                "review_count": int(row.get("review_count", 0)),
                "neighborhood": row.get("neighborhood"),
                "cafe_type": row.get("cafe_type"),
            })

    return {"points": points}
