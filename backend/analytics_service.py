from database import get_connection

def get_total_classes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT COALESCE(COUNT(DISTINCT (period_id, date)), 0) FROM attendance""")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total if total > 0 else 1

def get_attendance_summary():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            s.student_id,
            s.name,
            COALESCE(SUM(
                CASE
                    WHEN a.status = 'Present' THEN 1.0
                    WHEN a.status = 'Late' THEN 0.5
                    ELSE 0.0
                END
            ), 0) AS attended_classes
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id
        GROUP BY s.student_id, s.name
        ORDER BY s.student_id
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def get_defaulters(threshold=75):
    summary = get_attendance_summary()
    total = get_total_classes()

    defaulters = []
    for sid, name, attended in summary:
        pct = (attended / total) * 100
        if pct < threshold:
            defaulters.append((sid, name, round(pct, 2)))

    return defaulters
