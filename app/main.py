# from cProfile import label
# import os
# import cv2
# import time
# import logging
# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager

# from app.services.ml_service import ml_service
# from app.services.email_service import send_violation_email
# from app.routers import detection
# from app.routers.violations import router as violations_router
# from app.services.file_service import file_service
# EMAIL_ENABLED = True
# # ----------------------------------
# # Setup
# # ----------------------------------

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# os.makedirs("violations", exist_ok=True)
# os.makedirs("uploads", exist_ok=True)

# STREAM_ACTIVE = False
# LAST_EMAIL_TIME = 0
# COOLDOWN = 15

# # ----------------------------------
# # Lifespan
# # ----------------------------------

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     logger.info("Loading YOLO model...")
#     await ml_service.load_model()
#     yield
#     logger.info("Shutting down API")

# app = FastAPI(lifespan=lifespan)

# # ----------------------------------
# # CORS
# # ----------------------------------

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ----------------------------------
# # Routers
# # ----------------------------------

# app.include_router(detection.router, prefix="/detect")
# app.include_router(violations_router)

# # ----------------------------------
# # Camera Stream
# # ----------------------------------

# def generate_frames():
#     global STREAM_ACTIVE, LAST_EMAIL_TIME

#     STREAM_ACTIVE = True
#     cap = cv2.VideoCapture(0)

#     if not cap.isOpened():
#         logger.error("Camera not accessible")
#         return

#     while STREAM_ACTIVE:
#         success, frame = cap.read()
#         if not success:
#             break

#         # 🔥 Use unified ML pipeline
#         detected = ml_service._detect_objects(frame)

#         processed = file_service.draw_detections(frame, detected)

#         violation_found = any(
#             "no" in obj.class_name.lower()
#             for obj in detected
#         )

#         now = time.time()

#         if violation_found and now - LAST_EMAIL_TIME > COOLDOWN:
#             filename = f"violations/{int(now)}.jpg"
#             cv2.imwrite(filename, processed)

#             if EMAIL_ENABLED:
#                 send_violation_email(filename)
#             LAST_EMAIL_TIME = now

#         _, buffer = cv2.imencode(".jpg", processed)

#         yield (
#             b"--frame\r\n"
#             b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
#         )

#     cap.release()

# @app.get("/video")
# def video_feed():
#     return StreamingResponse(
#         generate_frames(),
#         media_type="multipart/x-mixed-replace; boundary=frame",
#     )

# @app.get("/stop-stream")
# def stop_stream():
#     global STREAM_ACTIVE
#     STREAM_ACTIVE = False
#     return {"message": "stream stopped"}

# from fastapi import Body

# @app.post("/alert-settings")
# def update_alert_settings(settings: dict = Body(...)):
#     global EMAIL_ENABLED

#     EMAIL_ENABLED = settings.get("email", True)

#     return {"email_enabled": EMAIL_ENABLED}

# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# app.mount("/violations", StaticFiles(directory="violations"), name="violations")

import cv2
import time
import logging
from contextlib import asynccontextmanager
import winsound
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.services.face_service import check_person

from app.services.ml_service import ml_service
from app.services.file_service import file_service
from app.services.email_service import send_violation_email
from app.routers import detection
from app.routers.violations import router as violations_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------
# Globals
# -------------------------

STREAM_ACTIVE = False
EMAIL_ENABLED = True
LAST_EMAIL_TIME = 0
COOLDOWN = 10


# -------------------------
# FastAPI lifespan
# -------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading YOLO model...")
    await ml_service.load_model()
    logger.info("Model loaded")
    yield
    logger.info("API shutdown")


app = FastAPI(lifespan=lifespan)

# -------------------------
# CORS (frontend access)
# -------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Camera Stream
# -------------------------


def generate_frames(mode="ppe"):

    global STREAM_ACTIVE, LAST_EMAIL_TIME

    STREAM_ACTIVE = True
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        logger.error("Camera not accessible")
        return

    while STREAM_ACTIVE:

        success, frame = cap.read()
        if not success:
            logger.error("Frame capture failed")
            break

        frame = cv2.resize(frame, (640, 480))

        # -------------------------
        # FACE MODE (Gate Camera)
        # -------------------------
        if mode == "face":

            result = check_person(frame)

            # Default
            text = "Stranger"
            color = (0, 0, 255)

            if result and result.get("is_employee"):
                name = result.get("name") or "Employee"
                text = f"Employee: {name}"
                color = (0, 255, 0)

            # Background box
            cv2.rectangle(frame, (15, 40), (260, 85), (0, 0, 0), -1)

            # Draw text
            cv2.putText(
                frame,
                text,
                (25, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2,
                cv2.LINE_AA
            )
            # Smaller background box a little lower



            processed = frame

            print("Face result:", result)

        # -------------------------
        # PPE MODE
        # -------------------------
        else:

            objects = ml_service._detect_objects(frame)

            processed = file_service.draw_detections(frame, objects)

            violation = any("no" in o.class_name.lower() for o in objects)

            now = time.time()

            if violation and now - LAST_EMAIL_TIME > COOLDOWN:

                path = file_service.save_violation(processed)

                for _ in range(5):
                    winsound.Beep(2000, 1000)

                if EMAIL_ENABLED:
                    send_violation_email(path)

                LAST_EMAIL_TIME = now

        # -------------------------
        # STREAM FRAME
        # -------------------------

        ret, buffer = cv2.imencode(".jpg", processed)

        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )

    cap.release()
    logger.info("Camera stopped")

# -------------------------
# Stream endpoints
# -------------------------

@app.get("/video")
def video_feed(mode: str = "ppe"):
    return StreamingResponse(
        generate_frames(mode),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/stop-stream")
def stop_stream():
    global STREAM_ACTIVE
    STREAM_ACTIVE = False
    return {"message": "stream stopped"}


# -------------------------
# Email toggle endpoint
# -------------------------

@app.post("/alert-settings")
def update_alert_settings(settings: dict = Body(...)):
    global EMAIL_ENABLED
    EMAIL_ENABLED = settings.get("email", True)
    return {"email_enabled": EMAIL_ENABLED}


# -------------------------
# Routers
# -------------------------

app.include_router(detection.router, prefix="/detect")
app.include_router(violations_router)

# -------------------------
# Static folders
# -------------------------

app.mount("/violations", StaticFiles(directory="violations"), name="violations")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
