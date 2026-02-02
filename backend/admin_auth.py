from database import get_connection

def admin_login(admin_id, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT admin_id, name, email
        FROM admins
        WHERE admin_id = %s AND password = %s
        LIMIT 1
    """, (admin_id, password))

    admin = cur.fetchone()
    cur.close()
    conn.close()
    return admin
