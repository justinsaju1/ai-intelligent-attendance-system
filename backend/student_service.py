from database import get_connection

def add_student(student_id, name, department, image_path, batch=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO students (student_id, name, department, image_path, batch)
        VALUES (%s, %s, %s, %s, %s)
    """, (student_id, name, department, image_path, batch))

    conn.commit()
    cur.close()
    conn.close()
