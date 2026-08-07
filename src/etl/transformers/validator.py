from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class RawGooglePlace(BaseModel):
    """Pydantic model for validating raw extracted data from Google Maps / Apify."""
    title: str = Field(..., min_length=1)
    placeId: str = Field(..., min_length=5)
    reviewsCount: int = Field(default=0, ge=0)
    totalScore: float = Field(default=0.0, ge=0.0, le=5.0)
    website: Optional[str] = None
    categoryName: Optional[str] = None
    address: Optional[str] = None
    location: Dict[str, float] = Field(default_factory=dict)
    
    @validator('website', pre=True)
    def clean_website(cls, v):
        if not v or not isinstance(v, str):
            return None
        return v.strip()

class CleanBusinessData(BaseModel):
    """Pydantic model for validated and cleaned business data ready for normalizer."""
    place_id: str
    name: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    category: Optional[str]
    total_reviews: int
    average_rating: float
    has_website: bool
    
    class Config:
        orm_mode = True
