
import asyncio
import time
import logging
from datetime import datetime
from typing import List

import cv2
import numpy as np
from ultralytics import YOLO

from app.services.face_service import check_person
from app.config import settings
from app.models.response_models import (
    DetectedObject,
    DetectionResult,
    ViolationDetail
)

logger = logging.getLogger(__name__)


class MLService:

    def __init__(self):
        self.model = None
        self.model_loaded = False

    # -------------------------
    # Load YOLO model
    # -------------------------
    async def load_model(self):

        loop = asyncio.get_event_loop()

        self.model = await loop.run_in_executor(
            None,
            lambda: YOLO(settings.MODEL_PATH)
        )

        self.model_loaded = True
        logger.info("YOLO model loaded")

    # -------------------------
    # Detect objects (YOLO)
    # -------------------------
    def _detect_objects(self, image: np.ndarray) -> List[DetectedObject]:

        if not self.model_loaded:
            raise RuntimeError("Model not loaded")

        results = self.model(
            image,
            imgsz=640,
            conf=settings.CONFIDENCE_THRESHOLD,
            iou=settings.IOU_THRESHOLD,
            verbose=False
        )[0]

        objects = []

        if results.boxes is None:
            return objects

        for box in results.boxes:

            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            class_name = self.model.names[cls]

            objects.append(
                DetectedObject(
                    class_name=class_name,
                    confidence=conf,
                    bbox=[x1, y1, x2, y2]
                )
            )

        return objects

    # -------------------------
    # Check PPE violations
    # -------------------------
    def analyze_violations(self, objects):

        violations = []

        for obj in objects:
            if "no" in obj.class_name.lower():

                violations.append(
                    ViolationDetail(
                        type="missing_ppe",
                        description=f"{obj.class_name} detected",
                        severity="high"
                    )
                )

        return violations

    # -------------------------
    # Process image
    # -------------------------
    async def process_image(self, image: np.ndarray):

        start = time.time()
        loop = asyncio.get_event_loop()

        objects = await loop.run_in_executor(
            None,
            self._detect_objects,
            image
        )

        violations = self.analyze_violations(objects)

        return DetectionResult(
            detected_objects=objects,
            violations=violations,
            violation_count=len(violations),
            total_objects=len(objects),
            processing_time=time.time() - start,
            timestamp=datetime.now()
        )

    # -------------------------
    # Process video frame
    # -------------------------
    async def process_video_frame(self, frame, mode="ppe"):

        # -------------------------
        # Gate Camera (Face Mode)
        # -------------------------
        if mode == "face":

            name = check_person(frame)

            if name:
                text = f"Employee: {name}"
                color = (0, 255, 0)
            else:
                text = "Stranger"
                color = (0, 0, 255)

            cv2.putText(
                frame,
                text,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                color,
                2
            )

            return frame, None

        # -------------------------
        # PPE Detection Mode
        # -------------------------

        detection = await self.process_image(frame)

        return frame, detection


ml_service = MLService()

# import cv2
# import numpy as np
# import time
# import logging
# import asyncio
# import threading
# from datetime import datetime
# from typing import List, Dict

# from ultralytics import YOLO

# from app.config import settings
# from app.models.response_models import DetectedObject, ViolationDetail, DetectionResult

# logger = logging.getLogger(__name__)


# class MLService:
#     def __init__(self):
#         self.model = None
#         self.model_loaded = False
#         self._lock = threading.Lock()

#     # ✅ Load model once at startup
#     async def load_model(self) -> bool:
#         try:
#             loop = asyncio.get_event_loop()
#             self.model = await loop.run_in_executor(
#                 None,
#                 lambda: YOLO(settings.MODEL_PATH)
#             )
#             self.model_loaded = True
#             logger.info(f"✅ Model loaded from {settings.MODEL_PATH}")
#             return True

#         except Exception as e:
#             logger.error(f"❌ Model load failed: {e}")
#             self.model_loaded = False
#             return False

#     # ✅ Run YOLO detection
#     def _detect_objects(self, image: np.ndarray) -> List[DetectedObject]:
#         if not self.model_loaded:
#             raise RuntimeError("Model not loaded")

#         results = self.model(
#             image,
#             conf=settings.CONFIDENCE_THRESHOLD,
#             iou=settings.IOU_THRESHOLD,
#             verbose=False
#         )

#         detected_objects = []

#         for result in results:
#             if result.boxes is None:
#                 continue

#             for box in result.boxes:
#                 x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#                 confidence = float(box.conf[0])
#                 class_id = int(box.cls[0])

#                 class_name = self.model.names[class_id]

#                 detected_objects.append(
#                     DetectedObject(
#                         class_name=class_name,
#                         confidence=confidence,
#                         bbox=[x1, y1, x2, y2]
#                     )
#                 )

#         return detected_objects

#     # ✅ PPE violation logic
#     def _analyze_violations(self, detected_objects: List[DetectedObject]) -> List[ViolationDetail]:
#         violations = []
#         detected_classes = [obj.class_name for obj in detected_objects]

#         for required_ppe in settings.REQUIRED_PPE:
#             if required_ppe not in detected_classes:
#                 violations.append(
#                     ViolationDetail(
#                         type="missing_ppe",
#                         description=f"Missing PPE: {required_ppe}",
#                         severity="high"
#                     )
#                 )

#         return violations

#     # ✅ Main processing function
#     async def process_image(self, image: np.ndarray) -> DetectionResult:
#         start_time = time.time()

#         loop = asyncio.get_event_loop()
#         detected_objects = await loop.run_in_executor(
#             None,
#             self._detect_objects,
#             image
#         )

#         violations = self._analyze_violations(detected_objects)

#         return DetectionResult(
#             detected_objects=detected_objects,
#             violations=violations,
#             violation_count=len(violations),
#             total_objects=len(detected_objects),
#             processing_time=time.time() - start_time,
#             timestamp=datetime.now()
#         )

#     async def process_video_frame(self, frame: np.ndarray) -> DetectionResult:
#         return await self.process_image(frame)

#     def get_model_info(self) -> Dict:
#         if not self.model_loaded:
#             return {"loaded": False}

#         return {
#             "loaded": True,
#             "model_path": settings.MODEL_PATH,
#             "classes": self.model.names
#         }


# # ✅ Global instance
# ml_service = MLService()



# import asyncio
# import time
# import logging
# import numpy as np
# from datetime import datetime
# from typing import List
# from app.services.face_service import check_person
# from ultralytics import YOLO

# from app.config import settings
# from app.models.response_models import (
#     DetectedObject,
#     DetectionResult,
#     ViolationDetail
# )

# logger = logging.getLogger(__name__)


# class MLService:

#     def __init__(self):
#         self.model = None
#         self.model_loaded = False

#     # -----------------------------------------
#     # Load YOLO model
#     # -----------------------------------------
#     async def load_model(self):

#         loop = asyncio.get_event_loop()

#         self.model = await loop.run_in_executor(
#             None,
#             lambda: YOLO(settings.MODEL_PATH)
#         )

#         self.model_loaded = True

#         logger.info("YOLO model loaded")

#     # -----------------------------------------
#     # Detect objects
#     # -----------------------------------------
#     def _detect_objects(self, image: np.ndarray) -> List[DetectedObject]:

#         if not self.model_loaded:
#             raise RuntimeError("Model not loaded")

#         results = self.model(
#             image,
#             imgsz=640,
#             conf=settings.CONFIDENCE_THRESHOLD,
#             iou=settings.IOU_THRESHOLD,
#             verbose=False
#         )[0]

#         objects = []

#         if results.boxes is None:
#             return objects

#         for box in results.boxes:

#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#             conf = float(box.conf[0])
#             cls = int(box.cls[0])

#             class_name = self.model.names[cls]

#             objects.append(
#                 DetectedObject(
#                     class_name=class_name,
#                     confidence=conf,
#                     bbox=[x1, y1, x2, y2]
#                 )
#             )

#         return objects

#     # -----------------------------------------
#     # Analyze PPE violations
#     # -----------------------------------------
#     def analyze_violations(self, objects):

#         violations = []

#         for obj in objects:

#             if "no" in obj.class_name.lower():

#                 violations.append(
#                     ViolationDetail(
#                         type="missing_ppe",
#                         description=f"{obj.class_name} detected",
#                         severity="high"
#                     )
#                 )

#         return violations

#     # -----------------------------------------
#     # Process image (USED BY /detect/upload-image)
#     # -----------------------------------------
#     async def process_image(self, image: np.ndarray):

#         start = time.time()

#         loop = asyncio.get_event_loop()

#         objects = await loop.run_in_executor(
#             None,
#             self._detect_objects,
#             image
#         )

#         violations = self.analyze_violations(objects)

#         return DetectionResult(
#             detected_objects=objects,
#             violations=violations,
#             violation_count=len(violations),
#             total_objects=len(objects),
#             processing_time=time.time() - start,
#             timestamp=datetime.now()
#         )

#     # -----------------------------------------
#     # Process video frame
#     # -----------------------------------------
#     async def process_video_frame(self, frame):

#         return await self.process_image(frame)


# ml_service = MLService()


# import asyncio
# import time
# import logging
# from datetime import datetime
# from typing import List

# import cv2
# import numpy as np
# from ultralytics import YOLO

# from app.services.face_service import check_person
# from app.config import settings
# from app.models.response_models import (
#     DetectedObject,
#     DetectionResult,
#     ViolationDetail
# )

# logger = logging.getLogger(__name__)


# class MLService:

#     def __init__(self):
#         self.model = None
#         self.model_loaded = False

#     # -----------------------------
#     # Load YOLO model
#     # -----------------------------
#     async def load_model(self):

#         loop = asyncio.get_event_loop()

#         self.model = await loop.run_in_executor(
#             None,
#             lambda: YOLO(settings.MODEL_PATH)
#         )

#         self.model_loaded = True
#         logger.info("YOLO model loaded")

#     # -----------------------------
#     # Detect objects
#     # -----------------------------
#     def _detect_objects(self, image: np.ndarray) -> List[DetectedObject]:

#         if not self.model_loaded:
#             raise RuntimeError("Model not loaded")

#         results = self.model(
#             image,
#             imgsz=640,
#             conf=settings.CONFIDENCE_THRESHOLD,
#             iou=settings.IOU_THRESHOLD,
#             verbose=False
#         )[0]

#         objects = []

#         if results.boxes is None:
#             return objects

#         for box in results.boxes:

#             x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
#             conf = float(box.conf[0])
#             cls = int(box.cls[0])

#             class_name = self.model.names[cls]

#             objects.append(
#                 DetectedObject(
#                     class_name=class_name,
#                     confidence=conf,
#                     bbox=[x1, y1, x2, y2]
#                 )
#             )

#         return objects

#     # -----------------------------
#     # Analyze PPE violations
#     # -----------------------------
#     def analyze_violations(self, objects):

#         violations = []

#         for obj in objects:
#             if "no" in obj.class_name.lower():
#                 violations.append(
#                     ViolationDetail(
#                         type="missing_ppe",
#                         description=f"{obj.class_name} detected",
#                         severity="high"
#                     )
#                 )

#         return violations

#     # -----------------------------
#     # Process image (YOLO detection)
#     # -----------------------------
#     async def process_image(self, image: np.ndarray):

#         start = time.time()
#         loop = asyncio.get_event_loop()

#         objects = await loop.run_in_executor(
#             None,
#             self._detect_objects,
#             image
#         )

#         violations = self.analyze_violations(objects)

#         return DetectionResult(
#             detected_objects=objects,
#             violations=violations,
#             violation_count=len(violations),
#             total_objects=len(objects),
#             processing_time=time.time() - start,
#             timestamp=datetime.now()
#         )

#     # -----------------------------
#     # Process video frame
#     # -----------------------------
# async def process_video_frame(self, frame):

#     # Face authentication
#     person_result = check_person(frame)

#     if person_result["is_employee"]:
#         name = person_result["name"]
#         color = (0, 255, 0)
#     else:
#         name = "Stranger"
#         color = (0, 0, 255)

#     # Draw text
#     cv2.putText(
#         frame,
#         name,
#         (20, 40),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         1,
#         color,
#         2
#     )

#     # Run PPE detection
#     detection = await self.process_image(frame)

#     return frame, detection


# ml_service = MLService()