from database import get_connection

def teacher_login(teacher_id, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT teacher_id, name, email
        FROM teachers
        WHERE teacher_id = %s AND password = %s
        LIMIT 1
    """, (teacher_id, password))

    teacher = cur.fetchone()
    cur.close()
    conn.close()
    return teacher
