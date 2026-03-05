import streamlit as st
import os

st.title("🔎 Job Search")

# -------------------------
# User Session
# -------------------------

user_email = st.session_state.get("user_email")

if not user_email:
    st.warning("Please login first.")
    st.stop()

# -------------------------
# Resume Storage
# -------------------------

RESUME_FOLDER = "data/resumes"
os.makedirs(RESUME_FOLDER, exist_ok=True)

resume_path = os.path.join(
    RESUME_FOLDER,
    f"{user_email}.pdf"
)

resume_exists = os.path.exists(resume_path)

# -------------------------
# Resume Upload
# -------------------------

if resume_exists:

    st.success("Resume already uploaded.")

    if st.button("Replace Resume"):
        os.remove(resume_path)
        resume_exists = False

if not resume_exists:

    resume_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"]
    )

    if resume_file:

        with open(resume_path, "wb") as f:
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

# Country list with code
countries = [
    ("United States", "us"),
    ("Canada", "ca"),
    ("United Kingdom", "uk"),
    ("Australia", "au"),
    ("Germany", "de"),
    ("Netherlands", "nl"),
    ("India", "in"),
    ("Singapore", "sg")
]

country = st.selectbox(
    "Select Country",
    countries,
    format_func=lambda x: x[0]
)

# -------------------------
# Search Button
# -------------------------

if st.button("Search Jobs"):

    if not role:
        st.warning("Please enter a job field.")
        st.stop()

    # Save query
    st.session_state["query"] = role

    # Save country name + code
    st.session_state["country_name"] = country[0]
    st.session_state["country_code"] = country[1]

    # Load resume bytes for matching
    if os.path.exists(resume_path):

        with open(resume_path, "rb") as f:
            st.session_state["resume_bytes"] = f.read()

    # Go to results page
    st.switch_page("pages/2_Results.py")
