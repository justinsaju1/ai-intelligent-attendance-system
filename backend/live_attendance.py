import cv2
from datetime import datetime, date
from database import get_connection
from face_recognition import load_known_faces_multi, detect_faces, match_face_roi
from period_config import get_current_period, get_attendance_phase
from class_calendar_service import is_working_day

MATCH_THRESHOLD = 2_000_000   # lower = stricter
HITS_REQUIRED = 2             # must match same student in 2 frames before marking

def write_attendance(student_id, period_id, status):
    conn = get_connection()
    cur = conn.cursor()

    # Requires UNIQUE(student_id, period_id, date)
    cur.execute("""
        INSERT INTO attendance (student_id, period_id, date, status)
        VALUES (%s, %s, CURRENT_DATE, %s)
        ON CONFLICT (student_id, period_id, date)
        DO UPDATE SET status = EXCLUDED.status
    """, (student_id, period_id, status))

    conn.commit()
    cur.close()
    conn.close()

def get_students_for_period(class_id, semester_id):
    """
    Only students enrolled in this class+semester are valid for absentee marking.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT student_id
        FROM student_semester_enrollment
        WHERE class_id=%s AND semester_id=%s
    """, (class_id, semester_id))
    ids = {r[0] for r in cur.fetchall()}
    cur.close()
    conn.close()
    return ids

def start_attendance(teacher_id=None):
    """
    teacher_id optional:
    - auto_runner calls start_attendance(None)
    - teacher-specific view/edit uses teacher_id
    """
    period = get_current_period(teacher_id)
    if not period:
        print("⚠️ No active period. Attendance not started.")
        return

    class_id = period.get("class_id")
    semester_id = period.get("semester_id")
    today_str = str(date.today())

    if class_id is not None and not is_working_day(class_id, today_str):
        print(f"🚫 Skipped attendance: {today_str} NOT working day for class_id={class_id}")
        return

    period_id = period["id"]
    end_dt = datetime.combine(datetime.today(), period["end_time"])

    known_db = load_known_faces_multi()
    if not known_db:
        print("❌ No known faces found in dataset/student_images.")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("❌ Camera not available (index 0/1).")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    detected_students = set()
    hit_counts = {}

    print(f"🎥 Attendance running: period_id={period_id}, class_id={class_id}, semester_id={semester_id}")

    while True:
        if datetime.now() > end_dt:
            break

        # ensure period hasn't changed
        period_live = get_current_period(teacher_id)
        if not period_live or period_live["id"] != period_id:
            break

        phase = get_attendance_phase(period_live)
        if phase == "PRESENT":
            status_now = "Present"
        elif phase == "LATE":
            status_now = "Late"
        else:
            # closed window (no marking)
            continue

        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detect_faces(gray)

        for (x, y, w, h) in faces:
            if w < 80 or h < 80:
                continue

            face_roi = gray[y:y + h, x:x + w]
            matched_id, score = match_face_roi(face_roi, known_db)

            if matched_id and score < MATCH_THRESHOLD:
                hit_counts[matched_id] = hit_counts.get(matched_id, 0) + 1

                if hit_counts[matched_id] >= HITS_REQUIRED:
                    detected_students.add(matched_id)
                    write_attendance(matched_id, period_id, status_now)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{matched_id} ({status_now})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Live Attendance (Multi-Angle)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # ✅ SAFETY: absentee marking only if class_id + semester_id exists
    if class_id is None or semester_id is None:
        print("⚠️ Period missing class_id/semester_id. Skipping absentee marking for safety.")
    else:
        all_students = get_students_for_period(class_id, semester_id)
        absentees = all_students - detected_students
        for sid in absentees:
            write_attendance(sid, period_id, "Absent")

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Attendance completed")
