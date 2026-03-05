import streamlit as st

st.title("🔎 AI Job Radar – Search")

st.write("Upload your resume and search for matching jobs.")

# -----------------------------
# Resume Upload
# -----------------------------

resume_file = st.file_uploader(
    "Upload Resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

# -----------------------------
# Job Role Input
# -----------------------------

role = st.text_input(
    "Enter job role (e.g., Data Scientist)"
)

# -----------------------------
# Country Selection
# -----------------------------

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
    "Select country for job search",
    countries,
    format_func=lambda x: x[0]
)

# -----------------------------
# Search Button
# -----------------------------

if st.button("Search Jobs"):

    if not role:
        st.warning("Please enter a job role.")
        st.stop()

    if resume_file is None:
        st.warning("Please upload your resume.")
        st.stop()

    # Save inputs to session
    st.session_state["query"] = role
    st.session_state["country_name"] = country[0]
    st.session_state["country_code"] = country[1]

    # Save resume bytes
    st.session_state["resume_bytes"] = resume_file.read()

    # Go to results page
    st.switch_page("pages/2_Results.py")
