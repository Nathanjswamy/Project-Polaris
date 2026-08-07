from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.models.business import AIInsight, CleanBusiness
import uuid

router = APIRouter()

class InsightRequest(BaseModel):
    business_id: str
    insight_type: str = "General"

@router.post("/generate")
def generate_insight(request: InsightRequest, db: Session = Depends(get_db)):
    # This is a placeholder for actual LLM generation (e.g., calling OpenAI or Gemini)
    # In a real scenario, we would fetch the business KPIs, send to LLM, and store the result.
    business = db.query(CleanBusiness).filter(CleanBusiness.business_id == request.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    mock_insight_text = f"Based on recent trends, {business.name} is performing well but could improve visibility."

    new_insight = AIInsight(
        business_id=request.business_id,
        insight_type=request.insight_type,
        narrative_text=mock_insight_text,
        generated_by="gemini-1.5-pro-mock"
    )
    
    db.add(new_insight)
    db.commit()
    db.refresh(new_insight)
    
    return {"message": "Insight generated", "insight": new_insight}

@router.get("/{business_id}")
def get_insights(business_id: str, db: Session = Depends(get_db)):
    insights = db.query(AIInsight).filter(AIInsight.business_id == business_id).order_by(AIInsight.generated_at.desc()).all()
    return insights
