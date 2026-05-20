from database import get_connection

def enroll_student(student_id: str, class_id: int, semester_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO student_semester_enrollment (student_id, class_id, semester_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (student_id, class_id, semester_id) DO NOTHING
    """, (str(student_id), int(class_id), int(semester_id)))

    conn.commit()
    cur.close()
    conn.close()
