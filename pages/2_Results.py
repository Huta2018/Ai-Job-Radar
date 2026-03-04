import streamlit as st
import requests
from supabase import create_client

st.title("🔎 Job Results")

# ---------------------------
# Supabase connection
# ---------------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ---------------------------
# Get query from session
# ---------------------------
query = st.session_state.get("query")

if not query:
    st.warning("No search query found. Please go back and run a search.")
    st.stop()

# ---------------------------
# Fetch jobs from SerpAPI
# ---------------------------
SERP_API_KEY = st.secrets.get("SERP_API_KEY")

params = {
    "engine": "google_jobs",
    "q": query,
    "api_key": SERP_API_KEY
}

response = requests.get("https://serpapi.com/search", params=params)
data = response.json()

jobs = data.get("jobs_results", [])

if not jobs:
    st.warning("No jobs found for this query.")
    st.stop()

# ---------------------------
# Display jobs
# ---------------------------
for i, job in enumerate(jobs[:20], start=1):

    st.markdown(f"### {i}. {job.get('title','Unknown')}")

    st.markdown(f"**Company:** {job.get('company_name','N/A')}")
    st.markdown(f"**Location:** {job.get('location','N/A')}")

    if job.get("description"):
        with st.expander("Job Description"):
            st.write(job["description"])

    if job.get("related_links"):
        for link in job["related_links"]:
            st.markdown(f"[Apply Here]({link['link']})")

    st.markdown("---")


# ---------------------------
# Feedback Section
# ---------------------------
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

    improvement = st.text_area("What should we improve?")

    submitted = st.form_submit_button("Submit Feedback")

    if submitted:

        try:

            supabase.table("feedback").insert({
                "anonymous_id": st.session_state.get("user_email", "anon"),
                "helpful": helpful,
                "would_pay": pay,
                "improvement": improvement
            }).execute()

            st.success("🙏 Thank you! Feedback recorded.")

        except Exception as e:

            st.error("Could not save feedback.")
            st.write(e)
