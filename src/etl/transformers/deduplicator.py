from typing import List
from src.etl.transformers.validator import CleanBusinessData
from src.etl.utils.logger import get_logger

logger = get_logger(__name__)

def deduplicate_places(normalized_places: List[CleanBusinessData]) -> List[CleanBusinessData]:
    """
    Removes exact duplicates from the current batch based on place_id 
    before sending to the database. (Database UPSERT handles the rest).
    """
    seen = set()
    unique_places = []
    
    for place in normalized_places:
        if place.place_id not in seen:
            seen.add(place.place_id)
            unique_places.append(place)
            
    duplicates_removed = len(normalized_places) - len(unique_places)
    if duplicates_removed > 0:
        logger.warning(f"Removed {duplicates_removed} intra-batch duplicates.")
        
    return unique_places
