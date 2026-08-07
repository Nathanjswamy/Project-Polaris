from typing import List
from src.etl.transformers.validator import CleanBusinessData
from src.etl.utils.logger import get_logger

logger = get_logger(__name__)

def enrich_and_create_features(unique_places: List[CleanBusinessData]) -> List[dict]:
    """
    Takes unique clean places and calculates features for the ML layer.
    In a real scenario, this would merge historical data to calculate rolling averages.
    """
    features = []
    for place in unique_places:
        # Mock feature calculation
        # e.g., if a place has high reviews and rating, we set a high 'opportunity_score'
        opportunity_score = (place.total_reviews / 1000) * (place.average_rating / 5) * 100
        
        features.append({
            "place_id": place.place_id,
            "opportunity_score": round(min(opportunity_score, 100), 2),
            "review_velocity_30d": round(place.total_reviews * 0.05, 2) # Mock 5% in 30 days
        })
        
    logger.info(f"Generated features for {len(unique_places)} businesses.")
    return features
