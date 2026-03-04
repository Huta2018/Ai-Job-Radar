import streamlit as st
import pandas as pd
from supabase import create_client

# Initialize Supabase connection
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.title("🔎 Job Results")

# Check if job results exist
if "job_results" not in st.session_state:
    st.warning("No jobs found. Please go back and run a search.")
    st.stop()

jobs = st.session_state["job_results"]

# Display jobs
for i, job in enumerate(jobs[:25], start=1):

    st.markdown(f"### {i}. {job['title']}")
    st.markdown(f"**Company:** {job['company']}")
    st.markdown(f"**Location:** {job['location']}")

    if job.get("salary"):
        st.markdown(f"**Salary:** {job['salary']}")

    st.markdown("**Job Summary:**")

    if "summary" in job:
        for bullet in job["summary"]:
            st.markdown(f"- {bullet}")

    if job.get("apply_link"):
        st.markdown(f"[Apply Here]({job['apply_link']})")

    with st.expander("Full Job Description"):
        st.write(job.get("description", "No description available"))

    st.markdown("---")


# -------------------------------
# FEEDBACK SECTION
# -------------------------------

st.markdown("## 💬 Anonymous Feedback")

with st.form("feedback_form"):

    helpful = st.radio(
        "Is this ranking helpful?",
        ["Yes 👍", "Somewhat 🤔", "No 👎"]
    )

    pay = st.radio(
        "Would you pay $10/month for unlimited smart ranked job searches?",
        ["Yes 💳", "Maybe 🤷", "No ❌"]
    )

    improvement = st.text_area(
        "What should we improve?"
    )

    submitted = st.form_submit_button("Submit Feedback")

    if submitted:

        try:

            response = supabase.table("feedback").insert({
                "anonymous_id": st.session_state.get("session_id"),
                "helpful": helpful,
                "would_pay": pay,
                "improvement": improvement
            }).execute()

            st.success("🙏 Thank you! Feedback recorded securely.")

        except Exception as e:
            st.error("Error saving feedback.")
            st.write(e)
