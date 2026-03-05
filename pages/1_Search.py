import streamlit as st
import os

st.title("🔎 Job Search")

user_email = st.session_state.get("user_email")

if not user_email:
    st.warning("Please login first.")
    st.stop()

# -------------------------
# Resume storage
# -------------------------

RESUME_FOLDER = "data/resumes"
os.makedirs(RESUME_FOLDER, exist_ok=True)

resume_path = os.path.join(
    RESUME_FOLDER,
    f"{user_email}.pdf"
)

resume_exists = os.path.exists(resume_path)

if resume_exists:

    st.success("Resume already uploaded.")

    if st.button("Replace Resume"):
        resume_exists = False

# -------------------------
# Upload Resume
# -------------------------

if not resume_exists:

    resume_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"]
    )

    if resume_file:

        with open(resume_path,"wb") as f:
            f.write(resume_file.getbuffer())

        st.success("Resume uploaded successfully.")

# -------------------------
# Job Search Inputs
# -------------------------

st.subheader("Search Jobs")

role = st.text_input(
    "Job Field",
    placeholder="e.g. Data Scientist"
)

country = st.selectbox(
    "Select Country",
    [
        "United States",
        "Canada",
        "United Kingdom",
        "Australia",
        "Germany",
        "Netherlands",
        "India",
        "Singapore"
    ]
)

if st.button("Search Jobs"):

    if not role:
        st.warning("Please enter a job field.")
        st.stop()

    st.session_state["query"] = role
    st.session_state["country"] = country

    # load resume
    if os.path.exists(resume_path):

        with open(resume_path,"rb") as f:

            st.session_state["resume_bytes"] = f.read()

    st.switch_page("pages/2_Results.py")
