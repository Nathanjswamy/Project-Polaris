from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.database import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    industry = Column(String, default="Cafe")
    location = Column(String, default="Hyderabad")
    website_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    source_type = Column(String, nullable=False) # e.g., 'google', 'instagram'
    external_url = Column(String, nullable=True)

class MetricsSnapshot(Base):
    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    raw_reviews_count = Column(Integer, default=0)
    raw_rating = Column(Float, default=0.0)
    social_followers = Column(Integer, default=0)

class DerivedKPI(Base):
    __tablename__ = "derived_kpis"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    health_score = Column(Float, default=0.0)
    visibility_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)
    dominance_score = Column(Float, default=0.0)
    growth_score = Column(Float, default=0.0)
    digital_presence_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)
    competitive_pressure_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    market_cluster = Column(String, nullable=True) # e.g., 'Leader', 'Rising Star'

class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    category = Column(String, nullable=False) # e.g., 'Risk', 'Opportunity'
    generated_insight = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
