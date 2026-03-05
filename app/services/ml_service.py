import cv2
import numpy as np
import time
import logging
import asyncio
import threading
from datetime import datetime
from typing import List, Dict

from ultralytics import YOLO

from app.config import settings
from app.models.response_models import DetectedObject, ViolationDetail, DetectionResult

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self._lock = threading.Lock()

    # ✅ Load model once at startup
    async def load_model(self) -> bool:
        try:
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: YOLO(settings.MODEL_PATH)
            )
            self.model_loaded = True
            logger.info(f"✅ Model loaded from {settings.MODEL_PATH}")
            return True

        except Exception as e:
            logger.error(f"❌ Model load failed: {e}")
            self.model_loaded = False
            return False

    # ✅ Run YOLO detection
    def _detect_objects(self, image: np.ndarray) -> List[DetectedObject]:
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        results = self.model(
            image,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            verbose=False
        )

        detected_objects = []

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                class_name = self.model.names[class_id]

                detected_objects.append(
                    DetectedObject(
                        class_name=class_name,
                        confidence=confidence,
                        bbox=[x1, y1, x2, y2]
                    )
                )

        return detected_objects

    # ✅ PPE violation logic
    def _analyze_violations(self, detected_objects: List[DetectedObject]) -> List[ViolationDetail]:
        violations = []
        detected_classes = [obj.class_name for obj in detected_objects]

        for required_ppe in settings.REQUIRED_PPE:
            if required_ppe not in detected_classes:
                violations.append(
                    ViolationDetail(
                        type="missing_ppe",
                        description=f"Missing PPE: {required_ppe}",
                        severity="high"
                    )
                )

        return violations

    # ✅ Main processing function
    async def process_image(self, image: np.ndarray) -> DetectionResult:
        start_time = time.time()

        loop = asyncio.get_event_loop()
        detected_objects = await loop.run_in_executor(
            None,
            self._detect_objects,
            image
        )

        violations = self._analyze_violations(detected_objects)

        return DetectionResult(
            detected_objects=detected_objects,
            violations=violations,
            violation_count=len(violations),
            total_objects=len(detected_objects),
            processing_time=time.time() - start_time,
            timestamp=datetime.now()
        )

    async def process_video_frame(self, frame: np.ndarray) -> DetectionResult:
        return await self.process_image(frame)

    def get_model_info(self) -> Dict:
        if not self.model_loaded:
            return {"loaded": False}

        return {
            "loaded": True,
            "model_path": settings.MODEL_PATH,
            "classes": self.model.names
        }


# ✅ Global instance
ml_service = MLService()

# import os
# import time
# import asyncio
# import logging
# from datetime import datetime
# from typing import List, Dict

# from ultralytics import YOLO
# from app.config import settings
# from app.models.response_models import (
#     DetectedObject,
#     ViolationDetail,
#     DetectionResult
# )

# logger = logging.getLogger(__name__)


# class MLService:
#     def __init__(self):
#         self.model = None
#         self.model_loaded = False

#     # --------------------------------------------------
#     # Load model
#     # --------------------------------------------------

#     async def load_model(self) -> bool:
#         try:
#             if not os.path.exists(settings.MODEL_PATH):
#                 raise FileNotFoundError(settings.MODEL_PATH)

#             loop = asyncio.get_running_loop()
#             self.model = await loop.run_in_executor(
#                 None,
#                 lambda: YOLO(settings.MODEL_PATH)
#             )

#             self.model_loaded = True
#             logger.info("Model loaded successfully")
#             return True

#         except Exception as e:
#             logger.error(f"Model load failed: {e}")
#             self.model_loaded = False
#             return False

#     # --------------------------------------------------
#     # Detection
#     # --------------------------------------------------

#     def _detect_objects(self, image) -> List[DetectedObject]:
#         if not self.model_loaded:
#             raise RuntimeError("Model not loaded")

#         results = self.model(
#             image,
#             imgsz=640,
#             conf=0.5,
#             iou=0.5,
#             verbose=False
#         )[0]

#         detected_objects = []

#         if results.boxes is None:
#             return detected_objects

#         for box in results.boxes:
#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
#             confidence = float(box.conf[0])
#             class_id = int(box.cls[0])
#             class_name = results.names[class_id]

#             detected_objects.append(
#                 DetectedObject(
#                     class_name=class_name,
#                     confidence=confidence,
#                     bbox=[int(x1), int(y1), int(x2), int(y2)]
#                 )
#             )

#         return detected_objects

#     # --------------------------------------------------
#     # Violation Logic
#     # --------------------------------------------------

#     def _analyze_violations(self, detected_objects):
#         detected_classes = [o.class_name for o in detected_objects]

#         if "person" not in detected_classes:
#             return []

#         violations = []

#         for required in settings.REQUIRED_PPE:
#             if required not in detected_classes:
#                 violations.append(
#                     ViolationDetail(
#                         type="missing_ppe",
#                         description=f"Missing PPE: {required}",
#                         severity="high"
#                     )
#                 )

#         return violations

#     # --------------------------------------------------
#     # Main Processing
#     # --------------------------------------------------

#     async def process_image(self, image) -> DetectionResult:
#         start = time.time()

#         loop = asyncio.get_running_loop()
#         detected = await loop.run_in_executor(
#             None,
#             self._detect_objects,
#             image
#         )

#         violations = self._analyze_violations(detected)

#         return DetectionResult(
#             detected_objects=detected,
#             violations=violations,
#             violation_count=len(violations),
#             total_objects=len(detected),
#             processing_time=time.time() - start,
#             timestamp=datetime.now()
#         )

#     async def process_video_frame(self, frame):
#         return await self.process_image(frame)

#     def get_model_info(self) -> Dict:
#         return {
#             "loaded": self.model_loaded,
#             "model_path": settings.MODEL_PATH if self.model_loaded else None,
#             "classes": self.model.names if self.model_loaded else []
#         }


# ml_service = MLService()