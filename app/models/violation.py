# from sqlalchemy import Column, Integer, String, Float, DateTime
# from datetime import datetime
# from app.database import Base

# class Violation(Base):
#     __tablename__ = "violations"

#     id = Column(Integer, primary_key=True, index=True)
#     camera_id = Column(String)
#     violation_type = Column(String)
#     confidence = Column(Float)
#     image_url = Column(String, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/violations")

_last_count = 0


@router.get("/latest")
def latest_violation():

    global _last_count

    folder = Path("violations")

    files = sorted(
        folder.glob("*.jpg"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    current = len(files)

    is_new = current > _last_count

    _last_count = current

    if not files:
        return {"new": False, "count": 0}

    return {
        "new": is_new,
        "count": current,
        "image": files[0].name
    }