from database import get_connection

# -----------------------------
# TEACHERS CRUD
# -----------------------------
def get_teachers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT teacher_id, name, email, department, password
        FROM teachers
        ORDER BY teacher_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_teacher(teacher_id, name, email, department, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO teachers (teacher_id, name, email, department, password)
        VALUES (%s, %s, %s, %s, %s)
    """, (teacher_id, name, email, department, password))
    conn.commit()
    cur.close()
    conn.close()

def update_teacher(teacher_id, name, email, department, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE teachers
        SET name=%s, email=%s, department=%s, password=%s
        WHERE teacher_id=%s
    """, (name, email, department, password, teacher_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_teacher(teacher_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM periods WHERE teacher_id=%s LIMIT 1", (teacher_id,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise Exception("Cannot delete teacher: periods are assigned. Delete/transfer periods first.")

    cur.execute("DELETE FROM teachers WHERE teacher_id=%s", (teacher_id,))
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# PERIODS CRUD
# -----------------------------
def get_periods():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, teacher_id, start_time, end_time, COALESCE(grace_minutes, 2), class_id, semester_id, subject_id
        FROM periods
        ORDER BY start_time
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_period(teacher_id, start_time, end_time, grace_minutes, class_id=None, semester_id=None, subject_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO periods (teacher_id, start_time, end_time, grace_minutes, class_id, semester_id, subject_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (teacher_id, start_time, end_time, grace_minutes, class_id, semester_id, subject_id))
    conn.commit()
    cur.close()
    conn.close()

def update_period(period_id, teacher_id, start_time, end_time, grace_minutes, class_id=None, semester_id=None, subject_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE periods
        SET teacher_id=%s, start_time=%s, end_time=%s, grace_minutes=%s,
            class_id=%s, semester_id=%s, subject_id=%s
        WHERE id=%s
    """, (teacher_id, start_time, end_time, grace_minutes, class_id, semester_id, subject_id, period_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_period(period_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM periods WHERE id=%s", (period_id,))
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# SUBSTITUTIONS
# -----------------------------
def get_substitutions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, date, period_id, original_teacher_id, substitute_teacher_id, created_at
        FROM substitutions
        ORDER BY date DESC, period_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def assign_substitute(date_val, period_id, original_teacher_id, substitute_teacher_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO substitutions (date, period_id, original_teacher_id, substitute_teacher_id, created_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (date, period_id)
        DO UPDATE SET
            original_teacher_id = EXCLUDED.original_teacher_id,
            substitute_teacher_id = EXCLUDED.substitute_teacher_id,
            created_at = CURRENT_TIMESTAMP
    """, (date_val, period_id, original_teacher_id, substitute_teacher_id))
    conn.commit()
    cur.close()
    conn.close()

def delete_substitution(sub_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM substitutions WHERE id=%s", (sub_id,))
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# SYSTEM ANALYTICS + AUDIT LOGS
# -----------------------------
def get_system_attendance_summary():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.student_id, s.name,
        COALESCE(SUM(
            CASE
                WHEN a.status='Present' THEN 1.0
                WHEN a.status='Late' THEN 0.5
                ELSE 0.0
            END
        ), 0) AS attended
        FROM students s
        LEFT JOIN attendance a ON a.student_id = s.student_id
        GROUP BY s.student_id, s.name
        ORDER BY s.student_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_total_classes_global():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(COUNT(DISTINCT (period_id, date)), 0) FROM attendance")
    total = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return total if total > 0 else 1

def get_audit_logs(limit=200):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT teacher_id, student_id, date, old_status, new_status, created_at
        FROM attendance_edit_logs
        ORDER BY created_at DESC NULLS LAST
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
