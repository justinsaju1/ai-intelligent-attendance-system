import os
from database import get_connection

DATASET_DIR = "dataset/student_images"

def get_departments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT department
        FROM students
        WHERE department IS NOT NULL AND department <> ''
        ORDER BY department
    """)
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

def get_batches():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT batch
        FROM students
        WHERE batch IS NOT NULL AND batch <> ''
        ORDER BY batch
    """)
    rows = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

def get_students(department=None, batch=None):
    conn = get_connection()
    cur = conn.cursor()

    base = """
        SELECT student_id, name, department, batch, image_path
        FROM students
    """
    conditions = []
    params = []

    if department and department != "All":
        conditions.append("department = %s")
        params.append(department)

    if batch and batch != "All":
        conditions.append("batch = %s")
        params.append(batch)

    if conditions:
        base += " WHERE " + " AND ".join(conditions)

    base += " ORDER BY department, batch, student_id"

    cur.execute(base, tuple(params))
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows

def _delete_student_images(student_id):
    if not os.path.exists(DATASET_DIR):
        return

    for f in os.listdir(DATASET_DIR):
        if f.startswith(f"{student_id}_") and f.lower().endswith(".jpg"):
            try:
                os.remove(os.path.join(DATASET_DIR, f))
            except:
                pass

        if f == f"{student_id}.jpg":
            try:
                os.remove(os.path.join(DATASET_DIR, f))
            except:
                pass

def bulk_delete_students(department=None, batch=None):
    conn = get_connection()
    cur = conn.cursor()

    base = "SELECT student_id FROM students"
    conditions = []
    params = []

    if department and department != "All":
        conditions.append("department = %s")
        params.append(department)

    if batch and batch != "All":
        conditions.append("batch = %s")
        params.append(batch)

    if conditions:
        base += " WHERE " + " AND ".join(conditions)

    cur.execute(base, tuple(params))
    ids = [r[0] for r in cur.fetchall()]

    if not ids:
        cur.close()
        conn.close()
        return 0

    cur.execute("DELETE FROM attendance WHERE student_id = ANY(%s)", (ids,))
    cur.execute("DELETE FROM attendance_edit_logs WHERE student_id = ANY(%s)", (ids,))
    cur.execute("DELETE FROM student_semester_enrollment WHERE student_id = ANY(%s)", (ids,))
    cur.execute("DELETE FROM students WHERE student_id = ANY(%s)", (ids,))
    conn.commit()

    cur.close()
    conn.close()

    for sid in ids:
        _delete_student_images(sid)

    return len(ids)

def delete_student(student_id: str) -> bool:
    student_id = str(student_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM students WHERE student_id=%s LIMIT 1", (student_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return False

    cur.execute("DELETE FROM attendance WHERE student_id=%s", (student_id,))
    cur.execute("DELETE FROM attendance_edit_logs WHERE student_id=%s", (student_id,))
    cur.execute("DELETE FROM student_semester_enrollment WHERE student_id=%s", (student_id,))
    cur.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
    conn.commit()

    cur.close()
    conn.close()

    _delete_student_images(student_id)
    return True
