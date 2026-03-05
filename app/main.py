from cProfile import label
import os
import cv2
import time
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.services.ml_service import ml_service
from app.services.email_service import send_violation_email
from app.routers import detection
from app.routers.violations import router as violations_router
from app.services.file_service import file_service
EMAIL_ENABLED = True
# ----------------------------------
# Setup
# ----------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("violations", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

STREAM_ACTIVE = False
LAST_EMAIL_TIME = 0
COOLDOWN = 15

# ----------------------------------
# Lifespan
# ----------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading YOLO model...")
    await ml_service.load_model()
    yield
    logger.info("Shutting down API")

app = FastAPI(lifespan=lifespan)

# ----------------------------------
# CORS
# ----------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------
# Routers
# ----------------------------------

app.include_router(detection.router, prefix="/detect")
app.include_router(violations_router)

# ----------------------------------
# Camera Stream
# ----------------------------------

def generate_frames():
    global STREAM_ACTIVE, LAST_EMAIL_TIME

    STREAM_ACTIVE = True
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Camera not accessible")
        return

    while STREAM_ACTIVE:
        success, frame = cap.read()
        if not success:
            break

        # 🔥 Use unified ML pipeline
        detected = ml_service._detect_objects(frame)

        processed = file_service.draw_detections(frame, detected)

        violation_found = any(
            "no" in obj.class_name.lower()
            for obj in detected
        )

        now = time.time()

        if violation_found and now - LAST_EMAIL_TIME > COOLDOWN:
            filename = f"violations/{int(now)}.jpg"
            cv2.imwrite(filename, processed)

            if EMAIL_ENABLED:
                send_violation_email(filename)
            LAST_EMAIL_TIME = now

        _, buffer = cv2.imencode(".jpg", processed)

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )

    cap.release()

@app.get("/video")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )

@app.get("/stop-stream")
def stop_stream():
    global STREAM_ACTIVE
    STREAM_ACTIVE = False
    return {"message": "stream stopped"}

from fastapi import Body

@app.post("/alert-settings")
def update_alert_settings(settings: dict = Body(...)):
    global EMAIL_ENABLED

    EMAIL_ENABLED = settings.get("email", True)

    return {"email_enabled": EMAIL_ENABLED}

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/violations", StaticFiles(directory="violations"), name="violations")