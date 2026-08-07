from typing import List, Dict, Any
from src.etl.transformers.validator import RawGooglePlace, CleanBusinessData
from src.etl.utils.logger import get_logger

logger = get_logger(__name__)

def clean_extracted_places(raw_places: List[RawGooglePlace]) -> List[CleanBusinessData]:
    """
    Cleans valid RawGooglePlace instances by handling missing values 
    and casting types for the next stage.
    """
    cleaned = []
    for place in raw_places:
        try:
            lat = place.location.get('lat') if place.location else None
            lng = place.location.get('lng') if place.location else None
            
            clean_item = CleanBusinessData(
                place_id=place.placeId,
                name=place.title.strip(),
                address=place.address.strip() if place.address else None,
                latitude=lat,
                longitude=lng,
                category=place.categoryName.strip() if place.categoryName else "Unknown",
                total_reviews=place.reviewsCount,
                average_rating=place.totalScore,
                has_website=bool(place.website)
            )
            cleaned.append(clean_item)
        except Exception as e:
            logger.error(f"Error cleaning place {place.title}: {str(e)}")
            
    logger.info(f"Successfully cleaned {len(cleaned)} out of {len(raw_places)} places.")
    return cleaned
