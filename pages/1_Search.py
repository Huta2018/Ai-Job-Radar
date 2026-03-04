import streamlit as st
import os

st.title("🔍 Job Search")

# -------------------------------------
# Get user email from session
# -------------------------------------
user_email = st.session_state.get("user_email")

if not user_email:
    st.warning("Please login first.")
    st.stop()

# -------------------------------------
# Resume storage path
# -------------------------------------
RESUME_FOLDER = "data/resumes"
os.makedirs(RESUME_FOLDER, exist_ok=True)

resume_path = os.path.join(RESUME_FOLDER, f"{user_email}.pdf")

# -------------------------------------
# Check if resume already saved
# -------------------------------------
resume_exists = os.path.exists(resume_path)

if resume_exists:
    st.success("Resume already saved for this account.")
    if st.button("Replace Resume"):
        resume_exists = False

# -------------------------------------
# Upload resume if not saved
# -------------------------------------
if not resume_exists:
    resume_file = st.file_uploader(
        "Upload Resume (PDF only)",
        type=["pdf"]
    )

    if resume_file is not None:
        with open(resume_path, "wb") as f:
            f.write(resume_file.getbuffer())
        st.success("Resume saved successfully!")
# ---------------------------------------
# Job Search Input
# ---------------------------------------
role = st.text_input("Field / Role", placeholder="e.g., Data Scientist")

if st.button("Search"):

    if not role:
        st.warning("Please enter a job field.")
        st.stop()

    # Save query
    st.session_state["query"] = role

    # Load resume text into session
    if os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            st.session_state["resume_bytes"] = f.read()
            st.session_state["resume_name"] = f"{user_email}.pdf"

    # IMPORTANT: initialize job_results so Results page does not crash
    st.session_state["job_results"] = []

    # Go to results page
    st.switch_page("pages/2_Results.py")
