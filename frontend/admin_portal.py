import streamlit as st
import json
import urllib.request
import urllib.error
from datetime import date
from urllib.parse import quote

BACKEND_URL = "http://127.0.0.1:5000"
st.set_page_config(page_title="Admin Portal", layout="wide")

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_id" not in st.session_state:
    st.session_state.admin_id = None
if "admin_name" not in st.session_state:
    st.session_state.admin_name = None

def api_get(path):
    with urllib.request.urlopen(f"{BACKEND_URL}{path}") as r:
        return json.loads(r.read().decode("utf-8"))

def api_post(path, payload):
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))

if not st.session_state.admin_logged_in:
    st.title("Admin Login")
    admin_id = st.text_input("Admin ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if admin_id.strip() == "" or password.strip() == "":
            st.error("Enter Admin ID and Password")
            st.stop()
        try:
            resp = api_post("/admin/login", {"admin_id": admin_id.strip(), "password": password.strip()})
            st.session_state.admin_logged_in = True
            st.session_state.admin_id = resp.get("admin_id")
            st.session_state.admin_name = resp.get("name")
            st.rerun()
        except urllib.error.HTTPError as e:
            st.error(f"Login failed (HTTP {e.code})")
            st.code(e.read().decode("utf-8"))
        except Exception as e:
            st.error("Backend not reachable")
            st.code(str(e))
    st.stop()

st.sidebar.title("Admin Panel")
st.sidebar.write(f"Logged in as: **{st.session_state.admin_name}** ({st.session_state.admin_id})")

menu = st.sidebar.radio(
    "Navigation",
    ["Student Registration", "Students", "Classes Calendar", "Teachers", "Periods", "Substitutions", "System Analytics", "Audit Logs"]
)

if st.sidebar.button("Logout"):
    st.session_state.admin_logged_in = False
    st.session_state.admin_id = None
    st.session_state.admin_name = None
    st.rerun()

if menu == "Student Registration":
    st.header("Student Registration")
    sid = st.text_input("Student ID")
    sname = st.text_input("Student Name")
    sdept = st.text_input("Department")
    sbatch = st.text_input("Batch")

    st.info("Click Register → camera opens on backend PC. Rotate head slowly.")

    if st.button("Register Student (Look at Camera)"):
        if sid.strip() == "" or sname.strip() == "":
            st.error("Student ID and Student Name are required.")
            st.stop()
        try:
            resp = api_post("/admin/student/register-live", {
                "student_id": sid.strip(),
                "name": sname.strip(),
                "department": sdept.strip(),
                "batch": sbatch.strip()
            })
            st.success("✅ Student registered successfully!")
            st.code(json.dumps(resp, indent=2))
        except urllib.error.HTTPError as e:
            st.error(f"Registration failed (HTTP {e.code})")
            st.code(e.read().decode("utf-8"))
        except Exception as e:
            st.error("Backend not reachable.")
            st.code(str(e))

elif menu == "Students":
    st.header("Students List")

    departments = ["All"] + api_get("/admin/departments")
    batches = ["All"] + api_get("/admin/batches")

    c1, c2 = st.columns(2)
    with c1:
        selected_dept = st.selectbox("Filter by Department", departments)
    with c2:
        selected_batch = st.selectbox("Filter by Batch", batches)

    url = "/admin/students"
    params = []
    if selected_dept != "All":
        params.append(f"department={quote(selected_dept)}")
    if selected_batch != "All":
        params.append(f"batch={quote(selected_batch)}")
    if params:
        url += "?" + "&".join(params)

    students = api_get(url)
    st.write(f"Total students shown: **{len(students)}**")
    st.table(students)

    st.divider()
    st.subheader("Student Deletion")

    del_sid = st.text_input("Student ID to Delete", key="single_del_sid")
    confirm_one = st.checkbox("I confirm I want to permanently delete this student.", key="single_del_confirm")

    if st.button("DELETE THIS STUDENT"):
        if del_sid.strip() == "":
            st.error("Please enter Student ID.")
            st.stop()
        if not confirm_one:
            st.error("Please confirm before deleting.")
            st.stop()
        try:
            resp = api_post("/admin/students/delete", {"student_id": del_sid.strip()})
            st.success(resp["message"])
            st.rerun()
        except urllib.error.HTTPError as e:
            st.error(f"Delete failed (HTTP {e.code})")
            st.code(e.read().decode("utf-8"))
        except Exception as e:
            st.error("Backend not reachable")
            st.code(str(e))

    st.divider()
    st.subheader("Remove the Batch")
    st.warning("This will delete students + attendance + edit logs + enrollment + face images. Use carefully.")

    del_batch = st.selectbox("Select Batch to Delete", ["All"] + api_get("/admin/batches"), key="del_batch")
    del_dept = st.selectbox("Optional Department Filter", ["All"] + api_get("/admin/departments"), key="del_dept")
    confirm = st.checkbox("I understand this will permanently delete records.")

    if st.button("DELETE STUDENTS"):
        if del_batch == "All":
            st.error("Batch is required for bulk delete.")
            st.stop()
        if not confirm:
            st.error("Please confirm before deleting.")
            st.stop()
        try:
            resp = api_post("/admin/students/bulk-delete", {"batch": del_batch, "department": del_dept})
            st.success(resp["message"])
            st.rerun()
        except urllib.error.HTTPError as e:
            st.error(f"Delete failed (HTTP {e.code})")
            st.code(e.read().decode("utf-8"))

elif menu == "Classes Calendar":
    st.header("Class Working Day Calendar")
    class_id = st.number_input("Class ID", min_value=1, value=1)
    day = st.date_input("Select Date", value=date.today())
    is_working = st.selectbox("Is Working Day?", [True, False])
    reason = st.text_input("Reason (optional)")

    if st.button("Save Working Day Status"):
        try:
            resp = api_post("/admin/class-calendar", {
                "class_id": int(class_id),
                "date": str(day),
                "is_working": is_working,
                "reason": reason.strip()
            })
            st.success(resp["message"])
        except urllib.error.HTTPError as e:
            st.error(f"Failed (HTTP {e.code})")
            st.code(e.read().decode("utf-8"))

    st.divider()
    st.subheader("Recent Calendar Entries")
    try:
        entries = api_get(f"/admin/class-calendar/{int(class_id)}")
        st.table(entries)
    except Exception as e:
        st.error("Failed to load calendar")
        st.code(str(e))

elif menu == "Teachers":
    st.header("Manage Teachers")
    colA, colB = st.columns(2)

    with colA:
        st.subheader("Add Teacher")
        t_id = st.text_input("Teacher ID (new)")
        t_name = st.text_input("Teacher Name (new)")
        t_email = st.text_input("Teacher Email (new)")
        t_dept = st.text_input("Teacher Department (new)")
        t_pass = st.text_input("Teacher Password (new)", type="password")

        if st.button("Add Teacher"):
            try:
                api_post("/admin/teachers", {
                    "teacher_id": t_id.strip(),
                    "name": t_name.strip(),
                    "email": t_email.strip(),
                    "department": t_dept.strip(),
                    "password": t_pass
                })
                st.success("Teacher added")
                st.rerun()
            except urllib.error.HTTPError as e:
                st.error("Add failed")
                st.code(e.read().decode("utf-8"))

    with colB:
        st.subheader("Existing Teachers")
        try:
            teachers = api_get("/admin/teachers")
            st.table(teachers)
        except Exception as e:
            st.error("Failed to load teachers")
            st.code(str(e))

    st.subheader("Update / Delete Teacher")
    t_upd_id = st.text_input("Teacher ID (update/delete)")
    t_upd_name = st.text_input("Name (update)")
    t_upd_email = st.text_input("Email (update)")
    t_upd_dept = st.text_input("Department (update)")
    t_upd_pass = st.text_input("Password (update)", type="password")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Update Teacher"):
            api_post("/admin/teachers/update", {
                "teacher_id": t_upd_id.strip(),
                "name": t_upd_name.strip(),
                "email": t_upd_email.strip(),
                "department": t_upd_dept.strip(),
                "password": t_upd_pass
            })
            st.success("Teacher updated")
            st.rerun()
    with c2:
        if st.button("Delete Teacher"):
            try:
                api_post("/admin/teachers/delete", {"teacher_id": t_upd_id.strip()})
                st.success("Teacher deleted")
                st.rerun()
            except urllib.error.HTTPError as e:
                st.error("Delete failed")
                st.code(e.read().decode("utf-8"))

elif menu == "Periods":
    st.header("Manage Periods")
    st.subheader("Existing Periods")
    periods = api_get("/admin/periods")
    st.table(periods)

    st.subheader("Add Period")
    p_teacher = st.text_input("Teacher ID for Period")
    p_start = st.text_input("Start Time (HH:MM:SS)", value="09:00:00")
    p_end = st.text_input("End Time (HH:MM:SS)", value="09:45:00")
    p_grace = st.number_input("Grace Minutes", min_value=0, max_value=10, value=2)
    p_class_id = st.number_input("Class ID", min_value=1, value=1)
    p_sem_id = st.number_input("Semester ID", min_value=1, value=1)
    p_sub_id = st.number_input("Subject ID", min_value=1, value=1)

    if st.button("Add Period"):
        api_post("/admin/periods", {
            "teacher_id": p_teacher.strip(),
            "start_time": p_start.strip(),
            "end_time": p_end.strip(),
            "grace_minutes": int(p_grace),
            "class_id": int(p_class_id),
            "semester_id": int(p_sem_id),
            "subject_id": int(p_sub_id)
        })
        st.success("Period added")
        st.rerun()

    st.subheader("Update / Delete Period")
    p_id = st.number_input("Period ID", min_value=1, value=1)
    p_teacher2 = st.text_input("Teacher ID (update)")
    p_start2 = st.text_input("Start Time (update)", value="09:00:00")
    p_end2 = st.text_input("End Time (update)", value="09:45:00")
    p_grace2 = st.number_input("Grace Minutes (update)", min_value=0, max_value=10, value=2)
    p_class2 = st.number_input("Class ID (update)", min_value=1, value=1)
    p_sem2 = st.number_input("Semester ID (update)", min_value=1, value=1)
    p_sub2 = st.number_input("Subject ID (update)", min_value=1, value=1)

    u1, u2 = st.columns(2)
    with u1:
        if st.button("Update Period"):
            api_post("/admin/periods/update", {
                "id": int(p_id),
                "teacher_id": p_teacher2.strip(),
                "start_time": p_start2.strip(),
                "end_time": p_end2.strip(),
                "grace_minutes": int(p_grace2),
                "class_id": int(p_class2),
                "semester_id": int(p_sem2),
                "subject_id": int(p_sub2)
            })
            st.success("Period updated")
            st.rerun()
    with u2:
        if st.button("Delete Period"):
            api_post("/admin/periods/delete", {"id": int(p_id)})
            st.success("Period deleted")
            st.rerun()

elif menu == "Substitutions":
    st.header("Teacher Replacement / Substitutions")
    st.subheader("Existing Substitutions")
    subs = api_get("/admin/substitutions")
    st.table(subs)

    st.subheader("Assign Substitute")
    s_date = st.date_input("Date", value=date.today())
    s_period_id = st.number_input("Period ID", min_value=1, value=1)
    s_original = st.text_input("Original Teacher ID")
    s_substitute = st.text_input("Substitute Teacher ID")

    if st.button("Assign / Update Substitute"):
        api_post("/admin/substitutions", {
            "date": str(s_date),
            "period_id": int(s_period_id),
            "original_teacher_id": s_original.strip(),
            "substitute_teacher_id": s_substitute.strip()
        })
        st.success("Substitution saved")
        st.rerun()

    st.subheader("Delete Substitution")
    del_id = st.number_input("Substitution ID to delete", min_value=1, value=1)
    if st.button("Delete Substitution"):
        api_post("/admin/substitutions/delete", {"id": int(del_id)})
        st.success("Deleted")
        st.rerun()

elif menu == "System Analytics":
    st.header("System-wide Attendance Analytics")

    st.subheader("Class + Semester Attendance Report (Average Across Subjects)")

    # Select class + semester (simple numeric inputs since you already have tables)
    c1, c2 = st.columns(2)
    with c1:
        class_id = st.number_input("Class ID", min_value=1, value=1)
    with c2:
        semester_id = st.number_input("Semester ID", min_value=1, value=1)

    st.info(f"Selected: Class = {class_id} | Semester = {semester_id}")

    if st.button("Load Report"):
        try:
            data = api_get(f"/admin/analytics/class-semester?class_id={int(class_id)}&semester_id={int(semester_id)}")

            # Strict order:
            # Student ID, Student Name, Attendance Percentage
            st.table(data)

            # ---------- CSV DOWNLOAD ----------
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(["Student ID", "Student Name", "Attendance Percentage"])

            for row in data:
                writer.writerow([
                    row.get("student_id"),
                    row.get("student_name"),
                    row.get("attendance_percentage")
                ])

            st.download_button(
                label="Download CSV",
                data=output.getvalue().encode("utf-8"),
                file_name=f"class_{int(class_id)}_semester_{int(semester_id)}_attendance.csv",
                mime="text/csv"
            )

        except urllib.error.HTTPError as e:
            st.error(f"Report failed (HTTP {e.code})")
            st.code(e.read().decode("utf-8"))
        except Exception as e:
            st.error("Backend not reachable / report failed")
            st.code(str(e))


elif menu == "Audit Logs":
    st.header("Attendance Edit Audit Logs (Latest 200)")
    try:
        logs = api_get("/admin/audit-logs")
        st.table(logs)
    except urllib.error.HTTPError as e:
        st.error(f"Audit logs failed (HTTP {e.code})")
        st.code(e.read().decode("utf-8"))
    except Exception as e:
        st.error("Failed to load audit logs")
        st.code(str(e))
