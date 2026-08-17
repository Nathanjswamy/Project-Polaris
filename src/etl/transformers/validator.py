"""
Pydantic Validation Models for Project Polaris
===============================================

Validates data at every pipeline stage. Records that fail validation
are logged with rejection reasons — never silently coerced.

Models:
    RawGooglePlace — validates raw Apify/Google Maps extract
    CleanCafe — validated, cleaned business record ready for enrichment
    RejectionRecord — tracks why a record was rejected
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# Hyderabad bounding box (generous)
HYD_LAT_MIN, HYD_LAT_MAX = 17.15, 17.65
HYD_LNG_MIN, HYD_LNG_MAX = 78.20, 78.75


class RawGooglePlace(BaseModel):
    """Validates a single place result from the Apify Google Maps scraper."""

    title: str = Field(..., min_length=1, description="Business name")
    placeId: str = Field(..., min_length=5, description="Google Maps place ID")
    totalScore: Optional[float] = Field(None, ge=0.0, le=5.0, description="Overall rating 0-5")
    reviewsCount: Optional[int] = Field(None, ge=0, description="Total review count")
    categoryName: Optional[str] = Field(None, description="Google Maps category")
    address: Optional[str] = Field(None, description="Full address string")
    website: Optional[str] = Field(None, description="Business website URL")
    phone: Optional[str] = Field(None, description="Phone number")
    url: Optional[str] = Field(None, description="Google Maps URL")
    imageUrl: Optional[str] = Field(None, description="Primary image URL")

    # Location — required and must be within Hyderabad
    location: Optional[Dict[str, float]] = Field(None, description="lat/lng dict")

    # Price level — Google uses string like "$", "$$", "$$$"
    price: Optional[str] = Field(None, description="Price level string from Google")

    # Reviews — list of individual review objects
    reviews: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Individual reviews with text, stars, date"
    )

    # Opening hours
    openingHours: Optional[List[Dict[str, Any]]] = Field(None)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("website", mode="before")
    @classmethod
    def clean_website(cls, v):
        if not v or not isinstance(v, str) or len(v.strip()) == 0:
            return None
        return v.strip()

    @field_validator("address", mode="before")
    @classmethod
    def clean_address(cls, v):
        if isinstance(v, str):
            return " ".join(v.split())  # collapse whitespace
        return v

    def get_lat(self) -> Optional[float]:
        if self.location and "lat" in self.location:
            return self.location["lat"]
        return None

    def get_lng(self) -> Optional[float]:
        if self.location and "lng" in self.location:
            return self.location["lng"]
        return None

    def is_in_hyderabad(self) -> bool:
        """Check if coordinates fall within the Hyderabad bounding box."""
        lat = self.get_lat()
        lng = self.get_lng()
        if lat is None or lng is None:
            return False
        return (HYD_LAT_MIN <= lat <= HYD_LAT_MAX and
                HYD_LNG_MIN <= lng <= HYD_LNG_MAX)

    def get_price_level(self) -> Optional[int]:
        """Convert Google's price string to integer 1-4."""
        if not self.price:
            return None
        # Google returns things like "$", "$$", "$$$", "$$$$"
        # or sometimes "Moderate", "Expensive", etc.
        p = self.price.strip()
        if p.startswith("$"):
            return min(len(p), 4)
        price_map = {
            "inexpensive": 1, "moderate": 2,
            "expensive": 3, "very expensive": 4
        }
        return price_map.get(p.lower(), None)


class CleanCafe(BaseModel):
    """A validated, cleaned café record ready for enrichment and analysis."""

    place_id: str
    name: str
    address: Optional[str] = None
    latitude: float
    longitude: float
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_count: int = Field(default=0, ge=0)
    price_level: Optional[int] = Field(None, ge=1, le=4)
    category_raw: Optional[str] = None
    has_website: bool = False
    website_url: Optional[str] = None
    google_maps_url: Optional[str] = None
    image_url: Optional[str] = None

    # Review-derived sentiment (from individual review stars)
    review_stars: Optional[List[int]] = Field(
        default_factory=list,
        description="Individual review star ratings for sentiment computation"
    )
    review_texts: Optional[List[str]] = Field(
        default_factory=list,
        description="Individual review texts"
    )

    # These get filled by enrichment stage
    neighborhood: Optional[str] = None
    zone: Optional[str] = None
    cafe_type: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_positive_pct: Optional[float] = None
    sentiment_negative_pct: Optional[float] = None
    reviews_analyzed: int = 0
    density_500m: Optional[int] = None
    density_1km: Optional[int] = None
    density_2km: Optional[int] = None
    competitive_score: Optional[float] = None
    opportunity_score: Optional[float] = None

    extracted_at: Optional[str] = None


class RejectionRecord(BaseModel):
    """Tracks a record that failed validation, with the reason."""

    place_id: Optional[str] = None
    title: Optional[str] = None
    rejection_reason: str
    rejected_field: Optional[str] = None
    rejected_value: Optional[str] = None
    stage: str = "validation"  # validation, cleaning, enrichment
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return self.model_dump()


class PipelineManifest(BaseModel):
    """Tracks the full pipeline run for provenance."""

    pipeline_run_id: str
    started_at: str
    completed_at: Optional[str] = None
    source: str = "Google Maps via Apify"

    # Extraction
    extraction_timestamp: Optional[str] = None
    extraction_queries: int = 0
    raw_items_received: int = 0

    # Validation
    records_validated: int = 0
    records_rejected: int = 0
    rejection_reasons: Dict[str, int] = Field(default_factory=dict)

    # Cleaning
    duplicates_removed: int = 0
    duplicates_examples: List[Dict[str, Any]] = Field(default_factory=list)

    # Enrichment
    neighborhoods_assigned: int = 0
    cafe_types_classified: int = 0
    sentiment_computed: int = 0

    # Feature engineering
    features_computed: int = 0

    # Output
    final_record_count: int = 0
    known_gaps: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()
