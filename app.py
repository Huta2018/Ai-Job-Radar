import streamlit as st
import uuid

st.set_page_config(page_title="AI Job Radar", layout="wide")

st.title("🧭 AI Job Radar")
st.info("🚀 Privacy-First Beta Version")

# -----------------------------------
# Generate Anonymous Session ID
# -----------------------------------
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

st.caption("🔒 Your resume is processed in-memory only and is never stored.")

# -----------------------------------
# Resume Upload (NOT stored)
# -----------------------------------
uploaded_file = st.file_uploader(
    "Upload your resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

if uploaded_file:
    st.session_state["resume_bytes"] = uploaded_file.read()
    st.session_state["resume_name"] = uploaded_file.name
    st.success("Resume uploaded successfully.")

# -----------------------------------
# Job Search Input
# -----------------------------------
query = st.text_input("Enter job role (e.g., Data Scientist)")

if st.button("Search Jobs"):

    if not query:
        st.warning("Please enter a job title.")
    else:
        st.session_state["query"] = query
        st.switch_page("pages/2_Results.py")
