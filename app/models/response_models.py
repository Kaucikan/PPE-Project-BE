from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ---------------------------------------------------
# Object detected by YOLO
# ---------------------------------------------------
class DetectedObject(BaseModel):
    class_name: str = Field(..., description="Detected object class name")
    confidence: float = Field(..., description="Detection confidence score")
    bbox: List[int] = Field(..., description="[x1, y1, x2, y2] bounding box")


# ---------------------------------------------------
# Violation information
# ---------------------------------------------------
class ViolationDetail(BaseModel):
    type: str = Field(..., description="Violation type (missing_ppe, low_confidence)")
    description: str = Field(..., description="Human readable violation description")
    severity: str = Field(..., description="Violation severity level")


# ---------------------------------------------------
# Detection output structure
# ---------------------------------------------------
class DetectionResult(BaseModel):
    detected_objects: List[DetectedObject] = []
    violations: List[ViolationDetail] = []
    violation_count: int = 0
    total_objects: int = 0
    processing_time: float = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    file_path: Optional[str] = None


# ---------------------------------------------------
# API Response wrapper
# ---------------------------------------------------
class ProcessingResponse(BaseModel):
    success: bool
    message: str = ""
    data: Optional[DetectionResult] = None
    error: Optional[str] = None


# ---------------------------------------------------
# Health check endpoint
# ---------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    model_loaded: bool
    version: str