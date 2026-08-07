from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.business import CleanBusiness, BusinessKPI

router = APIRouter()

@router.get("/")
def get_businesses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    businesses = db.query(CleanBusiness).offset(skip).limit(limit).all()
    return businesses

@router.get("/{business_id}")
def get_business(business_id: str, db: Session = Depends(get_db)):
    business = db.query(CleanBusiness).filter(CleanBusiness.business_id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business

@router.get("/{business_id}/kpis")
def get_business_kpis(business_id: str, db: Session = Depends(get_db)):
    kpis = db.query(BusinessKPI).filter(BusinessKPI.business_id == business_id).order_by(BusinessKPI.report_date.desc()).all()
    return kpis
