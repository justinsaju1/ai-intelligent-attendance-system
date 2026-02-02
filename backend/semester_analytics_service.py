from database import get_connection

def get_semester_summary(class_id, semester_id):
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
        FROM student_semester_enrollment e
        JOIN students s ON s.student_id = e.student_id
        LEFT JOIN attendance a ON a.student_id = s.student_id
        LEFT JOIN periods p ON p.id = a.period_id
        WHERE e.class_id = %s
          AND e.semester_id = %s
          AND p.class_id = %s
          AND p.semester_id = %s
        GROUP BY s.student_id, s.name
        ORDER BY s.student_id
    """, (class_id, semester_id, class_id, semester_id))

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_total_classes_for_semester(class_id, semester_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(DISTINCT (a.period_id, a.date))
        FROM attendance a
        JOIN periods p ON p.id = a.period_id
        WHERE p.class_id = %s
          AND p.semester_id = %s
    """, (class_id, semester_id))

    total = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return total if total > 0 else 1
