from database import get_connection
from datetime import date

def mark_attendance(student_id, status):
    conn = get_connection()
    cur = conn.cursor()

    today = date.today()

    # Prevent duplicate marking
    check_query = """
    SELECT * FROM attendance
    WHERE student_id = %s AND date = %s
    """
    cur.execute(check_query, (student_id, today))
    existing = cur.fetchone()

    if not existing:
        insert_query = """
        INSERT INTO attendance (student_id, date, status)
        VALUES (%s, %s, %s)
        """
        cur.execute(insert_query, (student_id, today, status))
        conn.commit()

    cur.close()
    conn.close()
