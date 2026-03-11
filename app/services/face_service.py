import cv2
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EMPLOYEE_FOLDER = os.path.join(BASE_DIR, "employees")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

employees = {}

# Load employee images
for file in os.listdir(EMPLOYEE_FOLDER):

    path = os.path.join(EMPLOYEE_FOLDER, file)

    if file.lower().endswith((".jpg", ".png", ".jpeg")):

        name = os.path.splitext(file)[0]

        img = cv2.imread(path, 0)
        employees[name] = img


def check_person(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:

        detected_face = gray[y:y+h, x:x+w]

        for name, emp_img in employees.items():

            emp_resized = cv2.resize(emp_img, (w, h))

            diff = cv2.absdiff(detected_face, emp_resized)

            score = diff.mean()

            if score < 50:
                return {
                    "is_employee": True,
                    "name": name
                }

    return {
        "is_employee": False,
        "stranger": True
    }