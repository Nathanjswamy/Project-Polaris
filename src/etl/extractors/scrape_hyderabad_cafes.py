"""
Hyderabad Café Extraction — Real Data from Google Maps via Apify
================================================================

Scrapes real café data across Hyderabad neighborhoods and café types.
Saves raw JSON to data/raw/ for provenance and reproducibility.

Usage:
    python -m src.etl.extractors.scrape_hyderabad_cafes
    python -m src.etl.extractors.scrape_hyderabad_cafes --test   # small batch test
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
METADATA_DIR = os.path.join(PROJECT_ROOT, "data", "metadata")

# ---------------------------------------------------------------------------
# Search queries — designed for comprehensive Hyderabad café coverage
# ---------------------------------------------------------------------------

# Neighborhood queries: broad geographic coverage
NEIGHBORHOOD_QUERIES = [
    "cafes in Jubilee Hills Hyderabad",
    "cafes in Banjara Hills Hyderabad",
    "cafes in Gachibowli Hyderabad",
    "cafes in Madhapur Hyderabad",
    "coffee shops in HITEC City Hyderabad",
    "cafes in Kondapur Hyderabad",
    "cafes in Himayatnagar Hyderabad",
    "cafes in Secunderabad",
    "cafes in Ameerpet Hyderabad",
    "cafes in Begumpet Hyderabad",
    "cafes in Kukatpally Hyderabad",
    "cafes near Charminar Hyderabad",
    "cafes in Somajiguda Hyderabad",
    "cafes in Mehdipatnam Hyderabad",
    "cafes in Kompally Hyderabad",
    "cafes in Miyapur Hyderabad",
    "cafes in Tolichowki Hyderabad",
    "cafes in Nampally Hyderabad",
]

# Category queries: café-type texture
CATEGORY_QUERIES = [
    "Irani cafe Hyderabad",
    "filter coffee Hyderabad",
    "specialty coffee roasters Hyderabad",
    "bakery cafe Hyderabad",
    "third wave coffee Hyderabad",
]

# Small test batch for verifying the scraper works
TEST_QUERIES = [
    "cafes in Jubilee Hills Hyderabad",
    "Irani cafe Hyderabad",
]


def run_extraction(test_mode: bool = False):
    """
    Run the Apify Google Maps scraper for Hyderabad cafés.
    
    Args:
        test_mode: If True, only run 2 test queries with 3 results each.
    """
    try:
        from apify_client import ApifyClient
    except ImportError:
        print("ERROR: apify_client not installed. Run: pip install apify-client")
        sys.exit(1)

    if not APIFY_API_TOKEN or APIFY_API_TOKEN == "your_token_here":
        print("ERROR: APIFY_API_TOKEN not set in .env file.")
        sys.exit(1)

    client = ApifyClient(APIFY_API_TOKEN)

    if test_mode:
        queries = TEST_QUERIES
        max_per_query = 3
        max_reviews = 3
        print("=== TEST MODE: 2 queries, 3 results each ===")
    else:
        queries = NEIGHBORHOOD_QUERIES + CATEGORY_QUERIES
        max_per_query = 20
        max_reviews = 5
        print(f"=== FULL EXTRACTION: {len(queries)} queries, up to {max_per_query} results each ===")

    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Queries: {len(queries)}")
    print()

    # Prepare Apify actor input
    run_input = {
        "searchStringsArray": queries,
        "maxCrawledPlacesPerSearch": max_per_query,
        "language": "en",
        "maxReviews": max_reviews,
        "oneReviewPerRow": False,
        "scrapeReviewerName": False,
        "scrapeReviewerId": False,
        "scrapeReviewerUrl": False,
        "scrapeReviewId": False,
        "scrapeReviewUrl": False,
        "scrapeResponseFromOwnerText": False,
    }

    print("Starting Apify actor (compass/crawler-google-places)...")
    print("This may take 5-30 minutes depending on query count.\n")

    start_time = time.time()

    try:
        run = client.actor("compass/crawler-google-places").call(
            run_input=run_input,
        )
    except Exception as e:
        print(f"\nERROR: Apify actor failed: {e}")
        print("Check your APIFY_API_TOKEN and account credits.")
        return None

    elapsed = time.time() - start_time
    print(f"Actor finished in {elapsed:.0f} seconds.")
    print(f"Run ID: {run.id}")
    print(f"Dataset ID: {run.default_dataset_id}")

    # Fetch results
    print("\nFetching results...")
    dataset_id = run.default_dataset_id
    if not dataset_id:
        print("ERROR: No dataset ID returned from Apify run.")
        return None

    items = list(client.dataset(dataset_id).iterate_items())
    print(f"Received {len(items)} raw items from Apify.\n")

    if not items:
        print("WARNING: No items returned. Check query relevance and Apify credits.")
        return None

    # Save raw JSON for provenance
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = os.path.join(RAW_DIR, f"apify_raw_{timestamp_str}.json")

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2, default=str)
    print(f"Saved raw data to: {raw_path}")
    print(f"File size: {os.path.getsize(raw_path) / 1024:.1f} KB")

    # Also save as the "latest" raw extract
    latest_path = os.path.join(RAW_DIR, "apify_latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2, default=str)

    # Save extraction manifest
    manifest = {
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "Google Maps via Apify (compass/crawler-google-places)",
        "apify_run_id": run.id,
        "apify_dataset_id": dataset_id,
        "mode": "test" if test_mode else "full",
        "queries": queries,
        "query_count": len(queries),
        "max_results_per_query": max_per_query,
        "max_reviews_per_place": max_reviews,
        "raw_items_received": len(items),
        "elapsed_seconds": round(elapsed, 1),
        "raw_file": raw_path,
        "unique_place_ids": len(set(item.get("placeId", "") for item in items if item.get("placeId"))),
    }

    manifest_path = os.path.join(METADATA_DIR, "extraction_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved extraction manifest to: {manifest_path}")

    # Quick summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"  Total raw items: {len(items)}")
    print(f"  Unique place IDs: {manifest['unique_place_ids']}")

    # Category breakdown
    categories = {}
    for item in items:
        cat = item.get("categoryName", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
    print(f"  Categories found: {len(categories)}")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:10]:
        print(f"    {cat}: {count}")

    # Rating distribution
    ratings = [item.get("totalScore", 0) for item in items if item.get("totalScore")]
    if ratings:
        print(f"  Rating range: {min(ratings):.1f} - {max(ratings):.1f}")
        print(f"  Mean rating: {sum(ratings)/len(ratings):.2f}")

    # Review count distribution
    review_counts = [item.get("reviewsCount", 0) for item in items if item.get("reviewsCount")]
    if review_counts:
        print(f"  Review count range: {min(review_counts)} - {max(review_counts)}")

    print("=" * 60)

    return items


if __name__ == "__main__":
    test = "--test" in sys.argv
    run_extraction(test_mode=test)
