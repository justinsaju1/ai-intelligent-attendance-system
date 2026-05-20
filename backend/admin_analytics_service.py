from database import get_connection

def get_class_semester_average_attendance(class_id, semester_id):
    """
    Report:
    Student ID | Student Name | Attendance Percentage

    - Uses ONLY actual attendance records.
    - Automatically tied to the selected class_id + semester_id
      (and therefore implicitly filtered by that class's department/batch).
    - Final % = average of subject-wise attendance % (AVG across subjects)
    """

    conn = get_connection()
    cur = conn.cursor()

    query = """
    WITH subject_stats AS (
        SELECT
            a.student_id,
            s.name AS student_name,
            p.subject_id,
            COUNT(*) AS total_classes,
            SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS attended_classes
        FROM attendance a
        JOIN periods p ON p.id = a.period_id
        JOIN students s ON s.student_id = a.student_id
        WHERE p.class_id = %s
          AND p.semester_id = %s
        GROUP BY a.student_id, s.name, p.subject_id
    ),
    student_avg AS (
        SELECT
            student_id,
            student_name,
            AVG((attended_classes::float / NULLIF(total_classes, 0)) * 100) AS avg_pct
        FROM subject_stats
        GROUP BY student_id, student_name
    )
    SELECT
        student_id,
        student_name,
        ROUND(avg_pct::numeric, 2) AS attendance_percentage
    FROM student_avg
    ORDER BY student_id;
    """

    cur.execute(query, (class_id, semester_id))
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows
