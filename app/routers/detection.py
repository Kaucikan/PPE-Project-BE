import logging
import time
from fastapi import APIRouter, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.email_service import send_violation_email
from app.services.ml_service import ml_service
from app.services.file_service import file_service
from app.models.response_models import ProcessingResponse
from app.config import settings
from app.utils.validation import validate_file_size, validate_file_extension

router = APIRouter()
logger = logging.getLogger(__name__)

# ----------------------------------
# Global Email Cooldown
# ----------------------------------

LAST_EMAIL_TIME = 0
EMAIL_COOLDOWN = 15


# ======================================================
# BASE64 LIVE FRAME (Frontend → Backend)
# ======================================================

class Base64ImageRequest(BaseModel):
    image: str
    save_processed: bool = True


@router.post("/live-frame", response_model=ProcessingResponse)
async def process_live_frame(
    request: Base64ImageRequest,
    background_tasks: BackgroundTasks
):
    global LAST_EMAIL_TIME

    image = file_service.decode_base64_image(request.image)

    result = await ml_service.process_image(image)

    if request.save_processed:
        processed = file_service.draw_detections(image, result.detected_objects)
        path = file_service.save_processed_image(processed)
        result.file_path = path

        # Email with cooldown
        if (
            result.violation_count > 0
            and time.time() - LAST_EMAIL_TIME > EMAIL_COOLDOWN
        ):
            background_tasks.add_task(send_violation_email, path)
            LAST_EMAIL_TIME = time.time()

    return ProcessingResponse(success=True, data=result)


# ======================================================
# IMAGE UPLOAD
# ======================================================

@router.post("/upload-image", response_model=ProcessingResponse)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Validate
    validate_file_extension(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS)

    content = await file.read()
    validate_file_size(len(content), settings.MAX_FILE_SIZE)

    # Save upload
    file_path = await file_service.save_uploaded_file(
        content, file.filename, "image"
    )

    # Process
    image = file_service.load_image(file_path)
    result = await ml_service.process_image(image)

    # Draw boxes
    processed = file_service.draw_detections(image, result.detected_objects)
    processed_path = file_service.save_processed_image(
        processed, file.filename
    )

    result.file_path = processed_path

    # Email (no cooldown here, manual upload = single action)
    if result.violation_count > 0:
        background_tasks.add_task(send_violation_email, processed_path)

    return ProcessingResponse(
        success=True,
        message="Image processed successfully",
        data=result
    )


# ======================================================
# MODEL INFO
# ======================================================

@router.get("/model-info")
async def get_model_info():
    return JSONResponse(content=ml_service.get_model_info())