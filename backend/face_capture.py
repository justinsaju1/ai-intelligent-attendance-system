import cv2
import os
import time

DATASET_DIR = "dataset/student_images"

def capture_face_live_multi(student_id, templates_needed=7, timeout_sec=10):
    """
    Captures multiple face templates live for better recognition.
    Saves images as: studentID_1.jpg, studentID_2.jpg, ...
    """
    os.makedirs(DATASET_DIR, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not accessible")
        return False

    print("📸 Live student registration started")
    print("➡️ Ask student to rotate head slowly (front, left, right, up, down)")

    captured = 0
    start_time = time.time()

    while captured < templates_needed:
        if time.time() - start_time > timeout_sec:
            print("⏱️ Registration timeout")
            break

        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # blur check
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur < 40:
            cv2.putText(frame, f"Too blurry ({int(blur)})", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Registration", frame)
            cv2.waitKey(1)
            continue

        captured += 1
        filename = f"{student_id}_{captured}.jpg"
        filepath = os.path.join(DATASET_DIR, filename)
        cv2.imwrite(filepath, gray)
        print(f"✅ Captured template {captured}/{templates_needed}")

        cv2.putText(frame, f"Captured {captured}/{templates_needed}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Registration", frame)
        cv2.waitKey(500)

    cap.release()
    cv2.destroyAllWindows()

    return captured >= templates_needed
