from flask import Flask, request, jsonify
from datetime import date

from teacher_auth import teacher_login
from admin_auth import admin_login

from face_capture import capture_face_live_multi
from student_service import add_student

from analytics_service import get_attendance_summary, get_total_classes, get_defaulters
from edit_attendance_service import update_attendance
from period_config import get_current_period, get_edit_deadline

from student_admin_service import (
    get_students, get_departments, get_batches,
    bulk_delete_students, delete_student
)

from admin_services import (
    get_teachers, add_teacher, update_teacher, delete_teacher,
    get_periods, add_period, update_period, delete_period,
    get_substitutions, assign_substitute, delete_substitution,
    get_system_attendance_summary, get_total_classes_global, get_audit_logs
)

from semester_analytics_service import get_semester_summary, get_total_classes_for_semester
from class_calendar_service import set_class_day, get_class_calendar

from database import get_connection

from admin_analytics_service import get_class_semester_average_attendance

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend Running"

# ----------------------------
# Teacher login
# ----------------------------
@app.route("/teacher/login", methods=["POST"])
def login_teacher():
    try:
        data = request.get_json(silent=True) or {}
        teacher_id = (data.get("teacher_id") or "").strip()
        password = data.get("password") or ""

        if not teacher_id or not password:
            return jsonify({"error": "teacher_id and password are required"}), 400

        teacher = teacher_login(teacher_id, password)
        if teacher:
            return jsonify({
                "message": "Login successful",
                "teacher_id": teacher[0],
                "teacher_name": teacher[1],
                "email": teacher[2] if len(teacher) > 2 else None
            }), 200

        return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Current period context
# ----------------------------
@app.route("/attendance/current-period/<teacher_id>", methods=["GET"])
def current_period(teacher_id):
    period = get_current_period(teacher_id)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM teachers WHERE teacher_id=%s", (teacher_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    teacher_name = row[0] if row else "Teacher"

    if not period:
        return jsonify({
            "teacher_name": teacher_name,
            "teacher_id": teacher_id,
            "active": False,
            "message": "No active period right now"
        })

    deadline = get_edit_deadline(period)

    return jsonify({
        "teacher_name": teacher_name,
        "teacher_id": teacher_id,
        "active": True,
        "period_id": period["id"],
        "period_start": period["start_time"].strftime("%H:%M"),
        "period_end": period["end_time"].strftime("%H:%M"),
        "edit_deadline": deadline.strftime("%H:%M"),
        "class_id": period.get("class_id"),
        "semester_id": period.get("semester_id"),
        "subject_id": period.get("subject_id")
    })

# ----------------------------
# Student registration (generic)
# ----------------------------
@app.route("/student/register", methods=["POST"])
def register_student():
    data = request.get_json(silent=True) or {}

    student_id = (data.get("student_id") or "").strip()
    name = (data.get("name") or "").strip()
    department = (data.get("department") or "").strip()
    batch = (data.get("batch") or "").strip() or None

    if not student_id or not name:
        return jsonify({"error": "student_id and name are required"}), 400

    ok = capture_face_live_multi(student_id, templates_needed=8, timeout_sec=20)
    if not ok:
        return jsonify({"message": "Live face capture failed. Try again in good lighting."}), 500

    image_path = f"dataset/student_images/{student_id}.jpg"
    add_student(student_id, name, department, image_path, batch)

    return jsonify({"message": "Student registered successfully (live capture)"}), 200

# ----------------------------
# Manual run disabled
# ----------------------------
@app.route("/attendance/run", methods=["POST"])
def run_attendance():
    return jsonify({"error": "Manual run disabled. Attendance is fully automatic."}), 403

# ----------------------------
# Analytics
# ----------------------------
@app.route("/attendance/analytics", methods=["GET"])
def attendance_analytics():
    summary = get_attendance_summary()
    total_classes = get_total_classes()

    return jsonify([
        {
            "student_id": sid,
            "name": name,
            "attendance_percentage": round((attended / total_classes) * 100, 2)
        }
        for sid, name, attended in summary
    ])

@app.route("/attendance/defaulters", methods=["GET"])
def attendance_defaulters():
    return jsonify([
        {
            "student_id": sid,
            "name": name,
            "attendance_percentage": pct
        }
        for sid, name, pct in get_defaulters()
    ])

# ----------------------------
# Edit attendance
# ----------------------------
@app.route("/attendance/edit", methods=["POST"])
def edit_attendance():
    data = request.get_json(silent=True) or {}
    try:
        update_attendance(
            data["teacher_id"],
            data["student_id"],
            data["date"],
            data["status"]
        )
        return jsonify({"message": "Attendance updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 403

# ------------------ ADMIN LOGIN ------------------
@app.route("/admin/login", methods=["POST"])
def login_admin():
    data = request.get_json(silent=True) or {}
    admin_id = (data.get("admin_id") or "").strip()
    password = (data.get("password") or "").strip()

    if not admin_id or not password:
        return jsonify({"error": "admin_id and password required"}), 400

    admin = admin_login(admin_id, password)
    if admin:
        return jsonify({"message": "Login successful", "admin_id": admin[0], "name": admin[1], "email": admin[2]}), 200

    return jsonify({"message": "Invalid credentials"}), 401

# ------------------ TEACHERS CRUD ------------------
@app.route("/admin/teachers", methods=["GET"])
def admin_teachers_get():
    rows = get_teachers()
    return jsonify([{"teacher_id": r[0], "name": r[1], "email": r[2], "department": r[3], "password": r[4]} for r in rows])

@app.route("/admin/teachers", methods=["POST"])
def admin_teachers_add():
    data = request.get_json(silent=True) or {}
    add_teacher(data["teacher_id"], data["name"], data.get("email"), data.get("department"), data["password"])
    return jsonify({"message": "Teacher added"}), 200

@app.route("/admin/teachers/update", methods=["POST"])
def admin_teachers_update():
    data = request.get_json(silent=True) or {}
    update_teacher(data["teacher_id"], data["name"], data.get("email"), data.get("department"), data["password"])
    return jsonify({"message": "Teacher updated"}), 200

@app.route("/admin/teachers/delete", methods=["POST"])
def admin_teachers_delete():
    data = request.get_json(silent=True) or {}
    try:
        delete_teacher(data["teacher_id"])
        return jsonify({"message": "Teacher deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------ PERIODS CRUD ------------------
@app.route("/admin/periods", methods=["GET"])
def admin_periods_get():
    rows = get_periods()
    return jsonify([
        {
            "id": r[0], "teacher_id": r[1],
            "start_time": str(r[2]), "end_time": str(r[3]),
            "grace_minutes": int(r[4]),
            "class_id": r[5], "semester_id": r[6], "subject_id": r[7]
        } for r in rows
    ])

@app.route("/admin/periods", methods=["POST"])
def admin_periods_add():
    data = request.get_json(silent=True) or {}
    add_period(
        data["teacher_id"],
        data["start_time"],
        data["end_time"],
        int(data.get("grace_minutes", 2)),
        data.get("class_id"),
        data.get("semester_id"),
        data.get("subject_id")
    )
    return jsonify({"message": "Period added"}), 200

@app.route("/admin/periods/update", methods=["POST"])
def admin_periods_update():
    data = request.get_json(silent=True) or {}
    update_period(
        int(data["id"]),
        data["teacher_id"],
        data["start_time"],
        data["end_time"],
        int(data.get("grace_minutes", 2)),
        data.get("class_id"),
        data.get("semester_id"),
        data.get("subject_id")
    )
    return jsonify({"message": "Period updated"}), 200

@app.route("/admin/periods/delete", methods=["POST"])
def admin_periods_delete():
    data = request.get_json(silent=True) or {}
    delete_period(int(data["id"]))
    return jsonify({"message": "Period deleted"}), 200

# ------------------ SUBSTITUTIONS ------------------
@app.route("/admin/substitutions", methods=["GET"])
def admin_subs_get():
    rows = get_substitutions()
    return jsonify([
        {"id": r[0], "date": str(r[1]), "period_id": r[2], "original_teacher_id": r[3], "substitute_teacher_id": r[4], "created_at": str(r[5])}
        for r in rows
    ])

@app.route("/admin/substitutions", methods=["POST"])
def admin_subs_assign():
    data = request.get_json(silent=True) or {}
    assign_substitute(data["date"], int(data["period_id"]), data["original_teacher_id"], data["substitute_teacher_id"])
    return jsonify({"message": "Substitute assigned"}), 200

@app.route("/admin/substitutions/delete", methods=["POST"])
def admin_subs_delete():
    data = request.get_json(silent=True) or {}
    delete_substitution(int(data["id"]))
    return jsonify({"message": "Substitution deleted"}), 200

# ------------------ STUDENTS ------------------
@app.route("/admin/departments", methods=["GET"])
def admin_departments():
    return jsonify(get_departments())

@app.route("/admin/batches", methods=["GET"])
def admin_batches():
    return jsonify(get_batches())

@app.route("/admin/students", methods=["GET"])
def admin_students():
    dept = request.args.get("department")
    batch = request.args.get("batch")
    rows = get_students(dept, batch)
    return jsonify([{"student_id": r[0], "name": r[1], "department": r[2], "batch": r[3], "image_path": r[4]} for r in rows])

@app.route("/admin/students/bulk-delete", methods=["POST"])
def admin_students_bulk_delete():
    data = request.get_json(silent=True) or {}
    dept = data.get("department")
    batch = data.get("batch")

    if not batch or batch == "All":
        return jsonify({"error": "Batch is required for bulk delete"}), 400

    deleted = bulk_delete_students(dept, batch)
    return jsonify({"message": f"Deleted {deleted} students", "deleted": deleted}), 200

@app.route("/admin/students/delete", methods=["POST"])
def admin_students_delete_one():
    data = request.get_json(silent=True) or {}
    student_id = (data.get("student_id") or "").strip()
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400

    ok = delete_student(student_id)
    if not ok:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"message": f"Student {student_id} deleted successfully"}), 200

# ------------------ ADMIN LIVE REGISTRATION ------------------
@app.route("/admin/student/register-live", methods=["POST"])
def admin_register_student_live():
    data = request.get_json(silent=True) or {}

    student_id = (data.get("student_id") or "").strip()
    name = (data.get("name") or "").strip()
    department = (data.get("department") or "").strip()
    batch = (data.get("batch") or "").strip() or None

    if not student_id or not name:
        return jsonify({"error": "student_id and name are required"}), 400

    ok = capture_face_live_multi(student_id, templates_needed=7, timeout_sec=15)
    if not ok:
        return jsonify({"error": "Face capture failed"}), 500

    image_path = f"dataset/student_images/{student_id}.jpg"
    add_student(student_id, name, department, image_path, batch)

    return jsonify({"message": "Student registered successfully (live capture)"}), 200

# ------------------ SYSTEM ANALYTICS ------------------
@app.route("/admin/analytics", methods=["GET"])
def admin_analytics():
    summary = get_system_attendance_summary()
    total_classes = get_total_classes_global()
    return jsonify([
        {"student_id": sid, "name": name, "attendance_percentage": round((attended / total_classes) * 100, 2)}
        for sid, name, attended in summary
    ])

# ------------------ AUDIT LOGS ------------------
@app.route("/admin/audit-logs", methods=["GET"])
def admin_audit_logs():
    rows = get_audit_logs(limit=200)
    return jsonify([
        {"teacher_id": r[0], "student_id": r[1], "date": str(r[2]), "old_status": r[3], "new_status": r[4], "created_at": str(r[5])}
        for r in rows
    ])

# ------------------ SEMESTER SUMMARY (Teacher) ------------------
@app.route("/teacher/semester-summary", methods=["GET"])
def teacher_semester_summary():
    class_id = request.args.get("class_id")
    semester_id = request.args.get("semester_id")

    if not class_id or not semester_id:
        return jsonify({"error": "class_id and semester_id required"}), 400

    class_id = int(class_id)
    semester_id = int(semester_id)

    summary = get_semester_summary(class_id, semester_id)
    total_classes = get_total_classes_for_semester(class_id, semester_id)

    return jsonify([
        {"student_id": sid, "name": name, "semester_percentage": round((attended / total_classes) * 100, 2)}
        for sid, name, attended in summary
    ])

# ------------------ CLASS CALENDAR ------------------
@app.route("/admin/class-calendar", methods=["POST"])
def admin_set_class_calendar():
    data = request.get_json(silent=True) or {}
    class_id = int(data.get("class_id"))
    date_str = data.get("date")
    is_working = bool(data.get("is_working"))
    reason = data.get("reason", "")

    set_class_day(class_id, date_str, is_working, reason)
    return jsonify({"message": "Class calendar updated"}), 200

@app.route("/admin/class-calendar/<int:class_id>", methods=["GET"])
def admin_get_class_calendar(class_id):
    from_date = request.args.get("from")
    to_date = request.args.get("to")

    rows = get_class_calendar(class_id, from_date, to_date)
    return jsonify([{"date": str(r[0]), "is_working": r[1], "reason": r[2]} for r in rows])

@app.route("/admin/analytics/class-semester", methods=["GET"])
def admin_class_semester_analytics():
    try:
        class_id = request.args.get("class_id")
        semester_id = request.args.get("semester_id")

        if not class_id or not semester_id:
            return jsonify({"error": "class_id and semester_id are required"}), 400

        class_id = int(class_id)
        semester_id = int(semester_id)

        rows = get_class_semester_average_attendance(class_id, semester_id)

        return jsonify([
            {
                "student_id": r[0],
                "student_name": r[1],
                "attendance_percentage": r[2]
            }
            for r in rows
        ]), 200

    except Exception as e:
        return jsonify({"error": f"Analytics failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
