import cv2
import os
import numpy as np

DATASET_PATH = "dataset/student_images"
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def detect_faces(gray_frame):
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    return face_cascade.detectMultiScale(gray_frame, scaleFactor=1.2, minNeighbors=5)

def load_known_faces_multi():
    """
    Returns:
    {
      "101": [img1, img2, ...],
      "102": [img1, img2, ...]
    }
    Supports files:
      101_1.jpg, 101_2.jpg ...
    """
    db = {}
    if not os.path.exists(DATASET_PATH):
        return db

    for file in os.listdir(DATASET_PATH):
        if not file.lower().endswith(".jpg"):
            continue

        base = file.split(".")[0]
        student_id = base.split("_")[0]

        img = cv2.imread(os.path.join(DATASET_PATH, file), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        img = cv2.resize(img, (100, 100))
        img = cv2.equalizeHist(img)

        db.setdefault(student_id, []).append(img)

    return db

def match_face_roi(face_roi, known_db):
    """
    Returns (best_id, best_score).
    Best score = minimum pixel difference across all templates.
    """
    face_roi = cv2.resize(face_roi, (100, 100))
    face_roi = cv2.equalizeHist(face_roi)

    best_id = None
    best_score = float("inf")

    for sid, templates in known_db.items():
        for t in templates:
            diff = np.sum(np.abs(face_roi.astype(np.int32) - t.astype(np.int32)))
            if diff < best_score:
                best_score = diff
                best_id = sid

    return best_id, best_score
