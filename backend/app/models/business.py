import uuid
from sqlalchemy import Column, String, Text, Numeric, Boolean, DateTime, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CleanBusiness(Base):
    __tablename__ = "businesses"
    __table_args__ = {'schema': 'clean'}

    business_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id = Column(Text, unique=True)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    category = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BusinessKPI(Base):
    __tablename__ = "business_kpis"
    __table_args__ = {'schema': 'analytics'}

    kpi_id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("clean.businesses.business_id"))
    report_date = Column(Date)
    average_rating = Column(Numeric(3, 2))
    review_count = Column(Integer)
    sentiment_score = Column(Numeric(5, 4))
    calculated_at = Column(DateTime, server_default=func.now())

class AIInsight(Base):
    __tablename__ = "ai_insights"
    __table_args__ = {'schema': 'predictions'}

    insight_id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("clean.businesses.business_id"))
    insight_type = Column(String(100))
    narrative_text = Column(Text)
    generated_by = Column(String(50))
    generated_at = Column(DateTime, server_default=func.now())
