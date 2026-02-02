from database import get_connection

def get_period_details(teacher_id):
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT start_time, grace_minutes
    FROM periods
    WHERE teacher_id = %s
    LIMIT 1
    """
    cur.execute(query, (teacher_id,))
    result = cur.fetchone()

    cur.close()
    conn.close()

    return result
