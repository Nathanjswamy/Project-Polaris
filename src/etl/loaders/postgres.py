from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
import json
from datetime import datetime

from src.etl.config import DATABASE_URL
from src.etl.utils.logger import get_logger
from backend.app.models.business import CleanBusiness, BusinessKPI

logger = get_logger(__name__)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def load_raw_google_places(raw_json_list: list):
    """Inserts raw JSON payloads into raw.google_maps_data"""
    with engine.begin() as conn:
        for raw_data in raw_json_list:
            place_id = raw_data.get("placeId", "UNKNOWN")
            sql = text("""
            INSERT INTO raw.google_maps_data (place_id, raw_json, extracted_at)
            VALUES (:place_id, :raw_json, :extracted_at)
            """)
            conn.execute(sql, {"place_id": place_id, "raw_json": json.dumps(raw_data), "extracted_at": datetime.now()})
    logger.info(f"Loaded {len(raw_json_list)} raw records to raw.google_maps_data")

def upsert_clean_businesses(clean_places: list):
    """Upserts into clean.businesses using SQLAlchemy ON CONFLICT DO UPDATE"""
    db = SessionLocal()
    try:
        for place in clean_places:
            stmt = insert(CleanBusiness).values(
                place_id=place.place_id,
                name=place.name,
                address=place.address,
                latitude=place.latitude,
                longitude=place.longitude,
                category=place.category
            )
            # On conflict (place_id must be unique)
            stmt = stmt.on_conflict_do_update(
                index_elements=['place_id'],
                set_={
                    'name': stmt.excluded.name,
                    'address': stmt.excluded.address,
                    'category': stmt.excluded.category,
                    'updated_at': func.now()
                }
            )
            db.execute(stmt)
            
            # Now we also want to insert into analytics.business_kpis
            # We need the UUID business_id, so we must fetch it first.
            business = db.query(CleanBusiness).filter(CleanBusiness.place_id == place.place_id).first()
            if business:
                kpi_stmt = insert(BusinessKPI).values(
                    business_id=business.business_id,
                    report_date=datetime.now().date(),
                    average_rating=place.average_rating,
                    review_count=place.total_reviews
                )
                db.execute(kpi_stmt)
                
        db.commit()
        logger.info(f"Successfully upserted {len(clean_places)} clean businesses and their KPIs.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upsert clean businesses: {str(e)}")
        raise
    finally:
        db.close()
