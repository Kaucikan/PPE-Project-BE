# import os
# import cv2
# import uuid
# import base64
# import logging
# import numpy as np
# from datetime import datetime

# logger = logging.getLogger(__name__)


# class FileService:

#     # -----------------------------------------
#     # Save uploaded file
#     # -----------------------------------------
#     async def save_uploaded_file(self, content: bytes, filename: str, folder: str):
#         ext = filename.split(".")[-1]
#         unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"

#         save_path = os.path.join("uploads", folder + "s")
#         os.makedirs(save_path, exist_ok=True)

#         full_path = os.path.join(save_path, unique_name)

#         with open(full_path, "wb") as f:
#             f.write(content)

#         logger.info(f"File saved: {full_path}")
#         return full_path

#     # -----------------------------------------
#     # Load image
#     # -----------------------------------------
#     def load_image(self, path: str):
#         image = cv2.imread(path)
#         return image

#     # -----------------------------------------
#     # Save processed image
#     # -----------------------------------------
#     def save_processed_image(self, image, original_name: str = None):
#         os.makedirs("uploads/processed", exist_ok=True)

#         name = (
#             f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
#             if not original_name
#             else f"processed_{original_name}"
#         )

#         path = os.path.join("uploads/processed", name)
#         cv2.imwrite(path, image)

#         return path

#     # -----------------------------------------
#     # Decode Base64 Image
#     # -----------------------------------------
#     def decode_base64_image(self, image_str: str):
#         header, encoded = image_str.split(",", 1)
#         image_bytes = base64.b64decode(encoded)
#         np_array = np.frombuffer(image_bytes, np.uint8)
#         image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
#         return image

#     # -----------------------------------------
#     # Draw Detections (FIXED VERSION)
#     # -----------------------------------------
#     def draw_detections(self, image: np.ndarray, detected_objects):
#         result_image = image.copy()
#         h, w = result_image.shape[:2]

#         for obj in detected_objects:
#             x1, y1, x2, y2 = map(int, obj.bbox)

#             # Clamp
#             x1 = max(0, min(x1, w - 1))
#             x2 = max(0, min(x2, w - 1))
#             y1 = max(0, min(y1, h - 1))
#             y2 = max(0, min(y2, h - 1))

#             class_name = obj.class_name.lower()
#             confidence = obj.confidence

#             violation = "no" in class_name

#             color = (0, 0, 255) if violation else (0, 255, 0)

#             thickness = max(2, int(min(w, h) / 300))

#             cv2.rectangle(result_image, (x1, y1), (x2, y2), color, thickness)

#             label = f"{class_name} {confidence:.2f}"

#             font_scale = max(0.5, min(w, h) / 1000)
#             font_thickness = max(1, thickness // 2)

#             (text_w, text_h), _ = cv2.getTextSize(
#                 label,
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 font_scale,
#                 font_thickness
#             )

#             label_y = y1 - 10 if y1 - 10 > text_h else y1 + text_h + 10

#             cv2.rectangle(
#                 result_image,
#                 (x1, label_y - text_h - 5),
#                 (x1 + text_w + 6, label_y),
#                 color,
#                 -1
#             )

#             cv2.putText(
#                 result_image,
#                 label,
#                 (x1 + 3, label_y - 3),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 font_scale,
#                 (255, 255, 255),
#                 font_thickness,
#                 cv2.LINE_AA
#             )

#         return result_image


# file_service = FileService()

import os
import cv2
import uuid
import base64
import logging
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class FileService:

    # -----------------------------------
    # Save uploaded image
    # -----------------------------------
    async def save_uploaded_file(self, content: bytes, filename: str, folder: str):

        ext = filename.split(".")[-1]

        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.{ext}"

        save_dir = os.path.join("uploads", folder + "s")

        os.makedirs(save_dir, exist_ok=True)

        path = os.path.join(save_dir, unique_name)

        with open(path, "wb") as f:
            f.write(content)

        logger.info(f"File saved: {path}")

        return path


    # -----------------------------------
    # Load image
    # -----------------------------------
    def load_image(self, path):

        return cv2.imread(path)


    # -----------------------------------
    # Save processed detection image
    # -----------------------------------
    def save_processed_image(self, image, original_name=None):

        os.makedirs("uploads/processed", exist_ok=True)

        if original_name:
            filename = f"processed_{original_name}"
        else:
            filename = f"{int(datetime.now().timestamp())}.jpg"

        path = os.path.join("uploads/processed", filename)

        cv2.imwrite(path, image)

        return path


    # -----------------------------------
    # Save violation snapshot
    # -----------------------------------
    def save_violation(self, image):

        os.makedirs("violations", exist_ok=True)

        filename = f"{int(datetime.now().timestamp())}.jpg"

        path = os.path.join("violations", filename)

        cv2.imwrite(path, image)

        return path


    # -----------------------------------
    # Decode base64 image
    # -----------------------------------
    def decode_base64_image(self, image_str):

        header, encoded = image_str.split(",", 1)

        img_bytes = base64.b64decode(encoded)

        np_arr = np.frombuffer(img_bytes, np.uint8)

        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


    # -----------------------------------
    # Draw detection bounding boxes
    # -----------------------------------
    def draw_detections(self, image, objects):

        img = image.copy()

        for obj in objects:

            x1, y1, x2, y2 = obj.bbox

            color = (0, 255, 0)

            if "no" in obj.class_name.lower():
                color = (0, 0, 255)

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            label = f"{obj.class_name} {obj.confidence:.2f}"

            cv2.putText(
                img,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        return img


file_service = FileService()