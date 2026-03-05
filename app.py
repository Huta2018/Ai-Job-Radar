import streamlit as st
import os

st.title("🧭 AI Job Radar")

st.markdown("🚀 Privacy-First Beta Version")

st.write("🔒 Your resume is processed in memory only and is never stored.")

# ------------------------
# Upload Resume
# ------------------------

resume_file = st.file_uploader(
    "Upload your resume (PDF or DOCX)",
    type=["pdf","docx"]
)

# ------------------------
# Job Role
# ------------------------

role = st.text_input(
    "Enter job role (e.g., Data Scientist)"
)

# ------------------------
# Country Selection
# ------------------------

countries = [
    ("United States","us"),
    ("Canada","ca"),
    ("United Kingdom","uk"),
    ("Australia","au"),
    ("Germany","de"),
    ("Netherlands","nl"),
    ("India","in"),
    ("Singapore","sg")
]

country = st.selectbox(
    "Select country for job search",
    countries,
    format_func=lambda x: x[0]
)

# ------------------------
# Search Button
# ------------------------

if st.button("Search Jobs"):

    if not role:
        st.warning("Please enter a job role.")
        st.stop()

    if resume_file is None:
        st.warning("Please upload your resume.")
        st.stop()

    st.session_state["query"] = role
    st.session_state["country_name"] = country[0]
    st.session_state["country_code"] = country[1]

    st.session_state["resume_bytes"] = resume_file.read()

    st.switch_page("pages/2_Results.py")
