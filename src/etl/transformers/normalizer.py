from typing import List
from src.etl.transformers.validator import CleanBusinessData
from src.etl.utils.logger import get_logger
import re

logger = get_logger(__name__)

def normalize_category(category: str) -> str:
    """Standardizes categories to a set vocabulary."""
    if not category:
        return "Other"
        
    cat_lower = category.lower()
    if "cafe" in cat_lower or "coffee" in cat_lower:
        return "Cafe/Coffee Shop"
    if "restaurant" in cat_lower:
        return "Restaurant"
    if "bakery" in cat_lower:
        return "Bakery"
    
    return category.title()

def normalize_address(address: str) -> str:
    """Normalizes address strings to remove redundant whitespace and standard formats."""
    if not address:
        return ""
    # Remove extra spaces, line breaks
    norm = re.sub(r'\s+', ' ', address)
    return norm.strip()

def normalize_places(cleaned_places: List[CleanBusinessData]) -> List[CleanBusinessData]:
    """Applies normalization logic to cleaned business data."""
    for place in cleaned_places:
        place.category = normalize_category(place.category)
        if place.address:
            place.address = normalize_address(place.address)
            
    logger.info(f"Normalized data for {len(cleaned_places)} places.")
    return cleaned_places
