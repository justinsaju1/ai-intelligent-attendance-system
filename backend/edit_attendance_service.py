from database import get_connection
from datetime import datetime
from period_config import get_current_period, get_edit_deadline

def update_attendance(teacher_id, student_id, date_str, new_status):
    period = get_current_period(teacher_id)
    if not period:
        raise Exception("No active period for this teacher right now")

    deadline = get_edit_deadline(period)
    now_time = datetime.now().time()
    if now_time > deadline:
        raise Exception("Attendance edit window has closed")

    conn = get_connection()
    cur = conn.cursor()

    # Get old status (period-based!)
    cur.execute("""
        SELECT status
        FROM attendance
        WHERE student_id = %s AND period_id = %s AND date = %s
    """, (student_id, period["id"], date_str))
    row = cur.fetchone()
    old_status = row[0] if row else "Absent"

    if row:
        cur.execute("""
            UPDATE attendance
            SET status = %s
            WHERE student_id = %s AND period_id = %s AND date = %s
        """, (new_status, student_id, period["id"], date_str))
    else:
        cur.execute("""
            INSERT INTO attendance (student_id, period_id, date, status)
            VALUES (%s, %s, %s, %s)
        """, (student_id, period["id"], date_str, new_status))

    # Audit log
    cur.execute("""
        INSERT INTO attendance_edit_logs
        (teacher_id, student_id, period_id, date, old_status, new_status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """, (teacher_id, student_id, period["id"], date_str, old_status, new_status))

    conn.commit()
    cur.close()
    conn.close()
