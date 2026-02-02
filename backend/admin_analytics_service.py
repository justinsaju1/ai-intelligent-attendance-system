from database import get_connection

def get_class_semester_average_attendance(class_id: int, semester_id: int):
    """
    Returns rows:
      (student_id, student_name, final_percentage)

    Final percentage =
      AVG(subject_percentage) across all subjects that have at least 1 conducted class.
    """

    conn = get_connection()
    cur = conn.cursor()

    # Explanation of query logic:
    # 1) enrolled: students in student_semester_enrollment for class+semester
    # 2) conducted: total classes conducted per subject = count distinct (period_id, date)
    # 3) attended: weighted attendance per student per subject
    # 4) subject_pct: (attended/conducted)*100 for each subject
    # 5) final: average of subject_pct across subjects per student

    cur.execute("""
        WITH enrolled AS (
            SELECT e.student_id, s.name
            FROM student_semester_enrollment e
            JOIN students s ON s.student_id = e.student_id
            WHERE e.class_id = %s AND e.semester_id = %s
        ),
        conducted AS (
            SELECT p.subject_id,
                   COUNT(DISTINCT (a.period_id, a.date))::float AS total_classes
            FROM attendance a
            JOIN periods p ON p.id = a.period_id
            WHERE p.class_id = %s AND p.semester_id = %s
            GROUP BY p.subject_id
        ),
        attended AS (
            SELECT e.student_id,
                   p.subject_id,
                   COALESCE(SUM(
                       CASE
                           WHEN a.status='Present' THEN 1.0
                           WHEN a.status='Late' THEN 0.5
                           ELSE 0.0
                       END
                   ), 0)::float AS attended_weighted
            FROM enrolled e
            JOIN periods p
              ON p.class_id = %s AND p.semester_id = %s
            LEFT JOIN attendance a
              ON a.student_id = e.student_id AND a.period_id = p.id
            GROUP BY e.student_id, p.subject_id
        ),
        subject_pct AS (
            SELECT a.student_id,
                   a.subject_id,
                   CASE
                       WHEN c.total_classes IS NULL OR c.total_classes = 0 THEN NULL
                       ELSE (a.attended_weighted / c.total_classes) * 100.0
                   END AS subject_percentage
            FROM attended a
            LEFT JOIN conducted c ON c.subject_id = a.subject_id
        )
        SELECT e.student_id,
               e.name,
               ROUND(AVG(sp.subject_percentage)::numeric, 2) AS final_percentage
        FROM enrolled e
        LEFT JOIN subject_pct sp ON sp.student_id = e.student_id
        GROUP BY e.student_id, e.name
        ORDER BY e.student_id;
    """, (class_id, semester_id, class_id, semester_id, class_id, semester_id))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # rows contains (student_id, name, final_percentage or None)
    # If a student has no subjects conducted yet, AVG will be NULL → return 0.00 or None
    fixed = []
    for sid, name, pct in rows:
        fixed.append((sid, name, float(pct) if pct is not None else 0.0))
    return fixed
