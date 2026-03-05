
import os
from typing import List, Dict
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    # -------------------------
    # 📧 Email
    # -------------------------
    EMAIL: str
    APP_PASS: str
    RECEIVER_EMAIL: str


    # -------------------------
    # API
    # -------------------------
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "PPE Detection API"
    VERSION: str = "1.0.0"


    # -------------------------
    # CORS
    # -------------------------
    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ])


    # -------------------------
    # File Upload
    # -------------------------
    UPLOAD_DIR: str = "uploads"
    PROCESSED_DIR: str = "uploads/processed"
    MAX_FILE_SIZE: int = 300 * 1024 * 1024


    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(default_factory=lambda: [
        ".jpg", ".jpeg", ".png", ".bmp", ".webp"
    ])

    ALLOWED_VIDEO_EXTENSIONS: List[str] = Field(default_factory=lambda: [
        ".mp4", ".avi", ".mov", ".mkv", ".webm"
    ])


    # -------------------------
    # Model
    # -------------------------
    MODEL_PATH: str = "app/models/best.pt"
    CONFIDENCE_THRESHOLD: float = 0.4
    IOU_THRESHOLD: float = 0.5


    # -------------------------
    # PPE
    # -------------------------
    PPE_CLASSES: Dict[int, str] = Field(default_factory=lambda: {
        0: "helmet",
        1: "vest",
        2: "gloves",
        3: "boots",
        4: "goggles",
        5: "mask",
    })

    REQUIRED_PPE: List[str] = Field(default_factory=lambda: [
        "helmet", "vest"
    ])


    # -------------------------
    # Logging
    # -------------------------
    LOG_LEVEL: str = "INFO"


    # -------------------------
    # Pydantic v2 Config
    # -------------------------
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# -------------------------
# Create instance
# -------------------------
settings = Settings()

# -------------------------
# Ensure folders exist
# -------------------------
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)

print(settings.EMAIL)