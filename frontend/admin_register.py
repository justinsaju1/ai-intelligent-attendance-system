import streamlit as st
import json
import urllib.request
import urllib.error

BACKEND_URL = "http://127.0.0.1:5000"
st.set_page_config(page_title="Admin – Student Registration", layout="centered")

st.title("Admin – Live Student Registration (Multi-Angle)")
st.write("This opens the webcam on the same PC running Flask and saves multiple templates per student.")

student_id = st.text_input("Student ID")
name = st.text_input("Student Name")
department = st.text_input("Department")
batch = st.text_input("Batch")

st.info("When you click Register, camera opens. Rotate head slowly.")

if st.button("Register Student (Live Multi-Template Capture)"):
    payload = {
        "student_id": student_id.strip(),
        "name": name.strip(),
        "department": department.strip(),
        "batch": batch.strip()
    }

    req = urllib.request.Request(
        f"{BACKEND_URL}/admin/student/register-live",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            st.success("✅ Student registered successfully!")
            st.code(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        st.error(f"❌ Registration failed (HTTP {e.code})")
        st.code(e.read().decode("utf-8"))
    except Exception as e:
        st.error("❌ Backend not reachable. Start Flask first.")
        st.code(str(e))
