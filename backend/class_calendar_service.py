from database import get_connection

def set_class_day(class_id, date_str, is_working, reason=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO class_calendar (class_id, date, is_working, reason)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (class_id, date)
        DO UPDATE SET is_working=EXCLUDED.is_working, reason=EXCLUDED.reason
    """, (class_id, date_str, is_working, reason))

    conn.commit()
    cur.close()
    conn.close()

def get_class_calendar(class_id, from_date=None, to_date=None):
    conn = get_connection()
    cur = conn.cursor()

    q = """
        SELECT date, is_working, COALESCE(reason,'')
        FROM class_calendar
        WHERE class_id=%s
    """
    params = [class_id]

    if from_date:
        q += " AND date >= %s"
        params.append(from_date)
    if to_date:
        q += " AND date <= %s"
        params.append(to_date)

    q += " ORDER BY date DESC"

    cur.execute(q, tuple(params))
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows

def is_working_day(class_id: int, date_str: str) -> bool:
    """
    Default working day rule:
    - If no row exists for (class_id, date) -> TRUE (working day)
    - If row exists -> return its is_working value
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT is_working
        FROM class_calendar
        WHERE class_id = %s AND date = %s
        LIMIT 1
    """, (class_id, date_str))

    row = cur.fetchone()
    cur.close()
    conn.close()

    return True if row is None else bool(row[0])
