"""
ETL Pipeline Orchestrator for Project Polaris
==============================================

Processes REAL café data extracted from Google Maps via Apify.
No synthetic data generation. Every number traces to a real source.

Pipeline stages:
    1. Load raw Apify extract (JSON)
    2. Validate with Pydantic — reject malformed records with logged reasons
    3. Deduplicate by place_id (exact) + fuzzy name+geo matching
    4. Clean and normalize
    5. Enrich (neighborhood, café type, density, sentiment)
    6. Feature engineering (competitive score, opportunity score)
    7. Save processed dataset + pipeline manifest

Usage:
    python -m src.etl.pipeline
    python -m src.etl.pipeline --extract          # run extraction first
    python -m src.etl.pipeline --extract --test    # extract small test batch
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pydantic import ValidationError
from src.etl.transformers.validator import (
    RawGooglePlace, CleanCafe, RejectionRecord, PipelineManifest
)
from src.etl.enrich import enrich_cafes, CAFE_TYPE_LABELS, haversine_km

# Paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")

RAW_EXTRACT_PATH = os.path.join(RAW_DIR, "apify_latest.json")
PROCESSED_PATH = os.path.join(PROCESSED_DIR, "polaris_cafes.csv")
MANIFEST_PATH = os.path.join(METADATA_DIR, "pipeline_manifest.json")
REJECTIONS_PATH = os.path.join(METADATA_DIR, "validation_rejections.json")
QUALITY_REPORT_PATH = os.path.join(METADATA_DIR, "quality_report.json")


def ensure_directories():
    for d in [RAW_DIR, PROCESSED_DIR, METADATA_DIR]:
        os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------------------
# Stage 1: Load Raw Extract
# ---------------------------------------------------------------------------

def load_raw_extract(path: str) -> List[dict]:
    """Load raw Apify JSON extract from disk."""
    if not os.path.exists(path):
        print(f"  ERROR: Raw extract not found at {path}")
        print("  Run with --extract flag to scrape data first.")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"  Loaded {len(items)} raw items from {path}")
    return items


# ---------------------------------------------------------------------------
# Stage 2: Validate
# ---------------------------------------------------------------------------

def validate_records(
    raw_items: List[dict],
) -> Tuple[List[RawGooglePlace], List[RejectionRecord]]:
    """
    Validate each raw record through Pydantic models.
    Returns valid records and a list of rejection records with reasons.
    """
    valid = []
    rejections = []

    for item in raw_items:
        # Attempt Pydantic validation
        try:
            place = RawGooglePlace(**item)
        except ValidationError as e:
            rej = RejectionRecord(
                place_id=item.get("placeId"),
                title=item.get("title"),
                rejection_reason=str(e),
                stage="pydantic_validation",
            )
            rejections.append(rej)
            continue

        # Business rule: must have coordinates
        if not place.get_lat() or not place.get_lng():
            rejections.append(RejectionRecord(
                place_id=place.placeId,
                title=place.title,
                rejection_reason="Missing coordinates (lat/lng)",
                rejected_field="location",
                stage="coordinate_check",
            ))
            continue

        # Business rule: must be in Hyderabad bounding box
        if not place.is_in_hyderabad():
            rejections.append(RejectionRecord(
                place_id=place.placeId,
                title=place.title,
                rejection_reason=f"Outside Hyderabad bounds: lat={place.get_lat()}, lng={place.get_lng()}",
                rejected_field="location",
                rejected_value=f"({place.get_lat()}, {place.get_lng()})",
                stage="geo_bounds_check",
            ))
            continue

        # Business rule: must have a rating (at least some signal)
        if place.totalScore is None or place.totalScore == 0:
            rejections.append(RejectionRecord(
                place_id=place.placeId,
                title=place.title,
                rejection_reason="No rating available (totalScore is None or 0)",
                rejected_field="totalScore",
                stage="rating_check",
            ))
            continue

        valid.append(place)

    return valid, rejections


# ---------------------------------------------------------------------------
# Stage 3: Deduplicate
# ---------------------------------------------------------------------------

def deduplicate(
    places: List[RawGooglePlace],
) -> Tuple[List[RawGooglePlace], int, List[Dict]]:
    """
    Remove duplicates by place_id (exact match).
    Also checks for fuzzy duplicates (same name within 100m).

    Returns:
        - Deduplicated list
        - Count of duplicates removed
        - Examples of collapsed records (for provenance)
    """
    seen_ids = {}
    dedup_examples = []
    duplicates_removed = 0

    # Pass 1: Exact place_id dedup
    unique_by_id = []
    for place in places:
        if place.placeId in seen_ids:
            duplicates_removed += 1
            existing = seen_ids[place.placeId]
            dedup_examples.append({
                "type": "exact_place_id",
                "kept": existing.title,
                "dropped": place.title,
                "place_id": place.placeId,
                "reason": "Same Google Maps place_id",
            })
        else:
            seen_ids[place.placeId] = place
            unique_by_id.append(place)

    # Pass 2: Fuzzy name + geo dedup (within 100m, similar name)
    final = []
    seen_names_geo = []  # (name_lower, lat, lng)

    for place in unique_by_id:
        name_lower = place.title.lower().strip()
        lat = place.get_lat()
        lng = place.get_lng()

        is_fuzzy_dup = False
        for existing_name, existing_lat, existing_lng in seen_names_geo:
            if lat and lng and existing_lat and existing_lng:
                dist = haversine_km(lat, lng, existing_lat, existing_lng)
                # Same name (or very similar) within 100m = likely duplicate
                if dist < 0.1 and _names_similar(name_lower, existing_name):
                    is_fuzzy_dup = True
                    duplicates_removed += 1
                    dedup_examples.append({
                        "type": "fuzzy_name_geo",
                        "kept": existing_name,
                        "dropped": place.title,
                        "distance_m": round(dist * 1000),
                        "reason": f"Similar name within {round(dist*1000)}m",
                    })
                    break

        if not is_fuzzy_dup:
            final.append(place)
            seen_names_geo.append((name_lower, lat, lng))

    return final, duplicates_removed, dedup_examples


def _names_similar(a: str, b: str) -> bool:
    """Simple name similarity check."""
    # Exact match
    if a == b:
        return True
    # One is substring of other
    if a in b or b in a:
        return True
    # Remove common suffixes and compare
    for suffix in [" cafe", " coffee", " house", " restaurant", " hotel"]:
        a_clean = a.replace(suffix, "").strip()
        b_clean = b.replace(suffix, "").strip()
        if a_clean == b_clean and len(a_clean) > 3:
            return True
    return False


# ---------------------------------------------------------------------------
# Stage 4: Clean & Normalize
# ---------------------------------------------------------------------------

def clean_to_records(places: List[RawGooglePlace]) -> List[dict]:
    """
    Transform validated Pydantic models into clean dict records
    ready for enrichment.
    """
    records = []
    for place in places:
        # Extract individual review stars for sentiment computation
        review_stars = []
        review_texts = []
        for review in (place.reviews or []):
            stars = review.get("stars") or review.get("score") or review.get("rating")
            if stars and isinstance(stars, (int, float)):
                review_stars.append(int(stars))
            text = review.get("text") or review.get("reviewText") or ""
            if text and len(text.strip()) > 10:
                review_texts.append(text.strip())

        record = {
            "place_id": place.placeId,
            "name": place.title.strip(),
            "address": place.address,
            "latitude": round(place.get_lat(), 6),
            "longitude": round(place.get_lng(), 6),
            "rating": round(place.totalScore, 2) if place.totalScore else None,
            "review_count": place.reviewsCount or 0,
            "price_level": place.get_price_level(),
            "category_raw": place.categoryName,
            "has_website": place.website is not None and len(place.website or "") > 0,
            "website_url": place.website,
            "google_maps_url": place.url,
            "image_url": place.imageUrl,
            "review_stars": review_stars,
            "review_texts": review_texts,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }
        records.append(record)

    return records


# ---------------------------------------------------------------------------
# Stage 6: Feature Engineering
# ---------------------------------------------------------------------------

def compute_features(cafes: List[dict]) -> List[dict]:
    """
    Compute competitive score and opportunity score from real fields.

    Competitive Score methodology (transparent, documented):
        competitive_score = (
            0.30 * normalized_rating +
            0.25 * normalized_review_count +
            0.20 * normalized_sentiment +
            0.15 * normalized_density_1km_inverse +
            0.10 * normalized_price_accessibility
        )

    All components are min-max normalized to [0, 1].
    Final score scaled to [0, 100].

    Fields used and why:
        - rating (30%): Direct quality signal from customers
        - review_count (25%): Social proof / popularity proxy
        - sentiment_score (20%): Customer satisfaction from review breakdown
        - 1/density_1km (15%): Less competition nearby = higher opportunity
        - price_accessibility (10%): Lower price = more accessible

    Opportunity Score methodology:
        Identifies underserved areas by measuring the gap between
        market demand signals (foot traffic proxied by review counts)
        and supply (density). Higher score = better opportunity.
    """
    if not cafes:
        return cafes

    # Extract arrays for normalization
    ratings = [c.get("rating") or 0 for c in cafes]
    reviews = [c.get("review_count", 0) for c in cafes]
    sentiments = [c.get("sentiment_score") or 0 for c in cafes]
    densities = [c.get("density_1km") or 0 for c in cafes]
    prices = [c.get("price_level") or 2 for c in cafes]

    def min_max(vals):
        mn, mx = min(vals), max(vals)
        if mn == mx:
            return [0.5] * len(vals)
        return [(v - mn) / (mx - mn) for v in vals]

    norm_rating = min_max(ratings)
    norm_reviews = min_max(reviews)
    norm_sentiment = min_max(sentiments)
    # Inverse density: fewer competitors nearby → higher score
    max_density = max(densities) if max(densities) > 0 else 1
    norm_density_inv = [1.0 - (d / max_density) for d in densities]
    # Price accessibility: lower price → higher accessibility
    norm_price_access = [1.0 - ((p - 1) / 3.0) for p in prices]

    weights = {
        "rating": 0.30,
        "review_count": 0.25,
        "sentiment_score": 0.20,
        "density_inverse": 0.15,
        "price_accessibility": 0.10,
    }

    for i, cafe in enumerate(cafes):
        comp_score = (
            weights["rating"] * norm_rating[i] +
            weights["review_count"] * norm_reviews[i] +
            weights["sentiment_score"] * norm_sentiment[i] +
            weights["density_inverse"] * norm_density_inv[i] +
            weights["price_accessibility"] * norm_price_access[i]
        )
        cafe["competitive_score"] = round(comp_score * 100, 1)

        # Opportunity score: high demand signals + low supply = opportunity
        # Demand proxy: review count relative to neighborhood average
        # Supply: density
        demand_signal = norm_reviews[i]
        supply_signal = densities[i] / max_density if max_density > 0 else 0.5
        cafe["opportunity_score"] = round(
            ((1.0 - supply_signal) * 0.6 + demand_signal * 0.4) * 100, 1
        )

    return cafes


# ---------------------------------------------------------------------------
# Stage 7: Save
# ---------------------------------------------------------------------------

def save_processed(cafes: List[dict], path: str) -> pd.DataFrame:
    """Save processed café data to CSV."""
    # Select columns for output (drop raw review lists)
    output_cols = [
        "place_id", "name", "address", "neighborhood", "zone",
        "latitude", "longitude", "rating", "review_count",
        "price_level", "category_raw", "cafe_type",
        "has_website", "website_url", "google_maps_url", "image_url",
        "sentiment_score", "sentiment_positive_pct", "sentiment_negative_pct",
        "reviews_analyzed",
        "density_500m", "density_1km", "density_2km",
        "competitive_score", "opportunity_score",
        "extracted_at",
    ]

    df = pd.DataFrame(cafes)

    # Only include columns that exist
    available_cols = [c for c in output_cols if c in df.columns]
    df = df[available_cols]

    df.to_csv(path, index=False)
    return df


# ---------------------------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(extract_first: bool = False, test_mode: bool = False):
    """Execute the full ETL pipeline on real data."""
    start_time = time.time()
    run_id = str(uuid.uuid4())[:8]

    print("=" * 60)
    print("Project Polaris — ETL Pipeline (Real Data)")
    print(f"Run ID: {run_id}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    ensure_directories()

    manifest = PipelineManifest(
        pipeline_run_id=run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
    )

    # Step 0: Extract if requested
    if extract_first:
        print("STEP 0: Extracting from Google Maps via Apify")
        print("-" * 40)
        from src.etl.extractors.scrape_hyderabad_cafes import run_extraction
        items = run_extraction(test_mode=test_mode)
        if not items:
            print("ERROR: Extraction failed. Cannot continue.")
            return
        print()

    # Step 1: Load raw extract
    print("STEP 1: Loading raw extract")
    print("-" * 40)
    raw_items = load_raw_extract(RAW_EXTRACT_PATH)
    manifest.raw_items_received = len(raw_items)
    print()

    # Step 2: Validate
    print("STEP 2: Validating records")
    print("-" * 40)
    valid_places, rejections = validate_records(raw_items)
    manifest.records_validated = len(valid_places)
    manifest.records_rejected = len(rejections)

    # Count rejection reasons
    reason_counts = {}
    for rej in rejections:
        stage = rej.stage
        reason_counts[stage] = reason_counts.get(stage, 0) + 1
    manifest.rejection_reasons = reason_counts

    print(f"  Valid records: {len(valid_places)}")
    print(f"  Rejected records: {len(rejections)}")
    for stage, count in reason_counts.items():
        print(f"    {stage}: {count}")

    # Save rejections log
    rejections_data = [r.to_dict() for r in rejections]
    with open(REJECTIONS_PATH, "w") as f:
        json.dump(rejections_data, f, indent=2, default=str)
    print(f"  Saved rejection log to: {REJECTIONS_PATH}")
    print()

    # Step 3: Deduplicate
    print("STEP 3: Deduplicating")
    print("-" * 40)
    deduped, n_dups, dup_examples = deduplicate(valid_places)
    manifest.duplicates_removed = n_dups
    manifest.duplicates_examples = dup_examples[:5]  # First 5 examples

    print(f"  Duplicates removed: {n_dups}")
    print(f"  Unique cafés: {len(deduped)}")
    if dup_examples:
        print(f"  Example dedup:")
        for ex in dup_examples[:3]:
            print(f"    Dropped '{ex['dropped']}' — {ex['reason']}")
    print()

    # Step 4: Clean & normalize
    print("STEP 4: Cleaning and normalizing")
    print("-" * 40)
    clean_records = clean_to_records(deduped)
    print(f"  Cleaned {len(clean_records)} records")
    print()

    # Step 5: Enrich
    print("STEP 5: Enriching (neighborhoods, café types, density, sentiment)")
    print("-" * 40)
    enriched = enrich_cafes(clean_records)

    # Count enrichment results
    n_neighborhoods = sum(1 for c in enriched if c.get("neighborhood") and c["neighborhood"] != "Unknown")
    n_types = sum(1 for c in enriched if c.get("cafe_type"))
    n_sentiment = sum(1 for c in enriched if c.get("sentiment_score") is not None)
    manifest.neighborhoods_assigned = n_neighborhoods
    manifest.cafe_types_classified = n_types
    manifest.sentiment_computed = n_sentiment

    # Neighborhood distribution
    neighborhood_counts = {}
    for c in enriched:
        nb = c.get("neighborhood", "Unknown")
        neighborhood_counts[nb] = neighborhood_counts.get(nb, 0) + 1

    print(f"  Neighborhoods assigned: {n_neighborhoods}/{len(enriched)}")
    for nb, count in sorted(neighborhood_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {nb}: {count}")

    # Café type distribution
    type_counts = {}
    for c in enriched:
        ct = c.get("cafe_type", "unknown")
        type_counts[ct] = type_counts.get(ct, 0) + 1
    print(f"  Café types classified: {n_types}")
    for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        label = CAFE_TYPE_LABELS.get(ct, ct)
        print(f"    {label}: {count}")

    print(f"  Sentiment computed: {n_sentiment} (from review stars)")
    print()

    # Step 6: Feature engineering
    print("STEP 6: Feature engineering")
    print("-" * 40)
    featured = compute_features(enriched)
    manifest.features_computed = len(featured)

    scores = [c.get("competitive_score", 0) for c in featured]
    if scores:
        print(f"  Competitive score range: {min(scores):.1f} - {max(scores):.1f}")
        print(f"  Mean competitive score: {sum(scores)/len(scores):.1f}")
    print()

    # Step 7: Save
    print("STEP 7: Saving processed dataset")
    print("-" * 40)
    df = save_processed(featured, PROCESSED_PATH)
    manifest.final_record_count = len(df)
    manifest.known_gaps = [
        "No website traffic data (requires analytics integration)",
        "No social media follower counts (requires Instagram/Twitter API)",
        "No repeat customer rate (requires POS/loyalty system data)",
        "No footfall data (requires location analytics provider)",
        "Review text limited to max 5 per café (Apify cost constraint)",
        "Single time snapshot — no historical trends (requires repeated scrapes)",
    ]

    file_size = os.path.getsize(PROCESSED_PATH) / 1024
    print(f"  Output: {PROCESSED_PATH}")
    print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Size: {file_size:.1f} KB")

    # Save manifest
    manifest.completed_at = datetime.now(timezone.utc).isoformat()
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest.to_dict(), f, indent=2, default=str)
    print(f"  Saved pipeline manifest to: {MANIFEST_PATH}")

    # Save quality report
    quality_report = generate_quality_report(df, manifest)
    with open(QUALITY_REPORT_PATH, "w") as f:
        json.dump(quality_report, f, indent=2, default=str)

    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print(f"Pipeline complete in {elapsed:.1f} seconds")
    print(f"Final dataset: {len(df)} cafés across {len(neighborhood_counts)} neighborhoods")
    print("=" * 60)


def generate_quality_report(df: pd.DataFrame, manifest: PipelineManifest) -> dict:
    """Generate a data quality report from the processed dataset."""
    n = len(df)

    # Completeness
    missing_by_col = {}
    for col in df.columns:
        missing = int(df[col].isnull().sum())
        if missing > 0:
            missing_by_col[col] = {
                "missing": missing,
                "missing_pct": round(missing / n * 100, 1),
            }

    total_cells = n * len(df.columns)
    total_missing = int(df.isnull().sum().sum())
    completeness = round((1 - total_missing / total_cells) * 100, 1) if total_cells > 0 else 100

    # Rating distribution
    ratings = df["rating"].dropna()
    rating_stats = {
        "mean": round(float(ratings.mean()), 2),
        "median": round(float(ratings.median()), 2),
        "min": round(float(ratings.min()), 2),
        "max": round(float(ratings.max()), 2),
        "std": round(float(ratings.std()), 2),
    } if len(ratings) > 0 else {}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_type": "Real data — Google Maps via Apify",
        "pipeline_run_id": manifest.pipeline_run_id,
        "summary": {
            "total_cafes": n,
            "total_columns": len(df.columns),
            "neighborhoods": int(df["neighborhood"].nunique()) if "neighborhood" in df.columns else 0,
            "cafe_types": int(df["cafe_type"].nunique()) if "cafe_type" in df.columns else 0,
            "completeness_pct": completeness,
            "records_extracted": manifest.raw_items_received,
            "records_rejected": manifest.records_rejected,
            "duplicates_removed": manifest.duplicates_removed,
            "records_enriched": manifest.neighborhoods_assigned,
        },
        "rating_distribution": rating_stats,
        "missing_data": missing_by_col,
        "known_gaps": manifest.known_gaps,
        "extraction_source": manifest.source,
    }


if __name__ == "__main__":
    extract = "--extract" in sys.argv
    test = "--test" in sys.argv
    run_pipeline(extract_first=extract, test_mode=test)
