from deepface import DeepFace
import os

AUTHORIZED_DIR = "authorized_faces"

def verify_face(frame_path):
    try:
        for person in os.listdir(AUTHORIZED_DIR):
            person_folder = os.path.join(AUTHORIZED_DIR, person)

            for image in os.listdir(person_folder):
                db_img_path = os.path.join(person_folder, image)

                result = DeepFace.verify(
                    img1_path=frame_path,
                    img2_path=db_img_path,
                    model_name="Facenet",
                    enforce_detection=False
                )

                if result["verified"]:
                    return {
                        "authorized": True,
                        "name": person,
                        "confidence": result["distance"]
                    }

        return {"authorized": False}

    except Exception as e:
        return {"authorized": False}