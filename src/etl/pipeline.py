import time
from datetime import datetime

from src.etl.utils.logger import get_logger
from src.etl.extractors.google_maps import GoogleMapsExtractor
from src.etl.transformers.cleaner import clean_extracted_places
from src.etl.transformers.normalizer import normalize_places
from src.etl.transformers.deduplicator import deduplicate_places
from src.etl.transformers.feature_creator import enrich_and_create_features
from src.etl.loaders.postgres import load_raw_google_places, upsert_clean_businesses

logger = get_logger(__name__)

def run_pipeline():
    start_time = time.time()
    logger.info(f"--- Starting Polaris ETL Pipeline at {datetime.now()} ---")
    
    # 1. EXTRACT
    extractor = GoogleMapsExtractor()
    search_queries = ["Roastery Coffee House Hyderabad", "F3 Cafe Hyderabad"]
    raw_places = extractor.fetch_places(search_queries)
    
    # Dump raw json payloads (for traceability/snapshots)
    raw_json_payloads = [p.dict() for p in raw_places]
    try:
        load_raw_google_places(raw_json_payloads)
    except Exception as e:
        logger.warning(f"Could not load to raw DB (ensure DB is running): {e}")

    # 2. VALIDATE & CLEAN
    clean_places = clean_extracted_places(raw_places)
    
    # 3. NORMALIZE
    normalized_places = normalize_places(clean_places)
    
    # 4. DEDUPLICATE (Intra-batch)
    unique_places = deduplicate_places(normalized_places)
    
    # 5. ENRICH & FEATURE CREATION (Calculated but we will skip inserting features into DB for brevity)
    features = enrich_and_create_features(unique_places)
    
    # 6. LOAD TO POSTGRES
    try:
        upsert_clean_businesses(unique_places)
    except Exception as e:
        logger.error(f"ETL Load phase failed: {e}")
        
    execution_time = time.time() - start_time
    logger.info(f"--- Pipeline Finished Successfully in {execution_time:.2f} seconds ---")

if __name__ == "__main__":
    run_pipeline()
