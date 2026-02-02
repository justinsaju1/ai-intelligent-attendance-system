import time
from datetime import datetime, date
from database import get_connection
from live_attendance import start_attendance

POLL_INTERVAL_SEC = 10

def get_due_periods(now_time):
    """
    Trigger only within the first 2 minutes from start_time.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, teacher_id, start_time, end_time
        FROM periods
        WHERE start_time <= %s
          AND %s <= (start_time + INTERVAL '2 minutes')
        ORDER BY start_time ASC
    """, (now_time, now_time))

    periods = cur.fetchall()
    cur.close()
    conn.close()
    return periods

def attendance_already_done(period_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 1
        FROM attendance
        WHERE period_id = %s AND date = CURRENT_DATE
        LIMIT 1
    """, (period_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def main():
    print("✅ Auto Runner started")
    print("⏱️ Attendance triggers automatically in the first 2 minutes of each period.\n")

    while True:
        try:
            now = datetime.now()
            now_time = now.time()

            due_periods = get_due_periods(now_time)
            if not due_periods:
                time.sleep(POLL_INTERVAL_SEC)
                continue

            for period_id, teacher_id, start_time, end_time in due_periods:
                if attendance_already_done(period_id):
                    continue

                print("--------------------------------------------------")
                print(f"🕒 {now.strftime('%H:%M:%S')} | Starting attendance")
                print(f"📌 Period ID: {period_id} | Teacher ID: {teacher_id}")
                print(f"⏳ Time: {start_time} -> {end_time}")
                print("--------------------------------------------------")

                # This runs until period ends
                start_attendance(None)

                print(f"✅ Completed attendance for Period {period_id} on {date.today()}\n")

            time.sleep(POLL_INTERVAL_SEC)

        except KeyboardInterrupt:
            print("\n🛑 Auto Runner stopped by user.")
            break
        except Exception as e:
            print("⚠️ Auto Runner error:", str(e))
            time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()
