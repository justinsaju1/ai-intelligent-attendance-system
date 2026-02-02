from datetime import datetime, timedelta, date
from database import get_connection

# configurable constants
AUTO_ATTENDANCE_MINUTES = 2
EDIT_LOCK_MINUTES = 2

def _get_effective_teacher_for_period(period_id: int, day: date):
    """
    If a substitution exists for (day, period_id), return substitute_teacher_id.
    Else return None.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT substitute_teacher_id
        FROM substitutions
        WHERE date = %s AND period_id = %s
        LIMIT 1
    """, (day, period_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_current_period(teacher_id=None):
    """
    Returns the currently active period.

    If teacher_id is given:
      - period can belong to that teacher directly (periods.teacher_id)
      - OR period can be assigned via substitutions table for today.

    If teacher_id is None:
      - returns any active period (used by auto_runner when it starts attendance).

    Returned dict keys:
      id, teacher_id, start_time, end_time, grace_minutes,
      class_id, semester_id, subject_id
    """
    now = datetime.now().time()
    today = date.today()

    conn = get_connection()
    cur = conn.cursor()

    if teacher_id:
        # Get active periods, then filter by effective teacher (direct or substitution)
        cur.execute("""
            SELECT id, teacher_id, start_time, end_time, grace_minutes,
                   class_id, semester_id, subject_id
            FROM periods
            WHERE start_time <= %s AND %s <= end_time
            ORDER BY start_time DESC
        """, (now, now))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        for r in rows:
            period_id = r[0]
            direct_teacher = r[1]
            sub_teacher = _get_effective_teacher_for_period(period_id, today)

            effective_teacher = sub_teacher if sub_teacher else direct_teacher
            if str(effective_teacher) == str(teacher_id):
                return {
                    "id": r[0],
                    "teacher_id": effective_teacher,
                    "start_time": r[2],
                    "end_time": r[3],
                    "grace_minutes": int(r[4]) if r[4] is not None else 2,
                    "class_id": r[5],
                    "semester_id": r[6],
                    "subject_id": r[7]
                }

        return None

    # teacher_id None: return any active period (latest)
    cur.execute("""
        SELECT id, teacher_id, start_time, end_time, grace_minutes,
               class_id, semester_id, subject_id
        FROM periods
        WHERE start_time <= %s AND %s <= end_time
        ORDER BY start_time DESC
        LIMIT 1
    """, (now, now))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    # If period has a substitution today, effective teacher becomes substitute
    sub_teacher = _get_effective_teacher_for_period(row[0], today)
    effective_teacher = sub_teacher if sub_teacher else row[1]

    return {
        "id": row[0],
        "teacher_id": effective_teacher,
        "start_time": row[2],
        "end_time": row[3],
        "grace_minutes": int(row[4]) if row[4] is not None else 2,
        "class_id": row[5],
        "semester_id": row[6],
        "subject_id": row[7]
    }

def get_edit_deadline(period):
    """
    Returns the edit deadline as a datetime.time.
    Rule: Edit allowed until (end_time - EDIT_LOCK_MINUTES)
    """
    end_time = period["end_time"]
    end_dt = datetime.combine(datetime.today(), end_time)
    deadline_dt = end_dt - timedelta(minutes=EDIT_LOCK_MINUTES)
    return deadline_dt.time()

def get_attendance_phase(period):
    """
    Returns:
      'PRESENT' during first AUTO_ATTENDANCE_MINUTES from start_time
      'LATE' after that until edit window begins
      None when attendance should be closed
    """
    now = datetime.now()

    start_dt = datetime.combine(datetime.today(), period["start_time"])
    end_dt = datetime.combine(datetime.today(), period["end_time"])

    present_end = start_dt + timedelta(minutes=AUTO_ATTENDANCE_MINUTES)
    edit_start = end_dt - timedelta(minutes=EDIT_LOCK_MINUTES)

    if start_dt <= now <= present_end:
        return "PRESENT"

    if present_end < now < edit_start:
        return "LATE"

    return None
