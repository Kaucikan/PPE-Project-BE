from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DetectedObject(BaseModel):
    class_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]

class ViolationDetail(BaseModel):
    type: str  # "missing_ppe", "low_confidence"
    description: str
    severity: str  # "high", "medium", "low"

class DetectionResult(BaseModel):
    detected_objects: List[DetectedObject]
    violations: List[ViolationDetail]
    violation_count: int
    total_objects: int
    processing_time: float
    timestamp: datetime
    file_path: Optional[str] = None

class ProcessingResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DetectionResult] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    model_loaded: bool
    version: str
