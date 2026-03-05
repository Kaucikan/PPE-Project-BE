from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database import Base

class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String)
    violation_type = Column(String)
    confidence = Column(Float)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)