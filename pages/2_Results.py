import streamlit as st
import requests
import io

from supabase import create_client

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pdfminer.high_level import extract_text


st.title("🔎 Job Results")


# -------------------------
# Supabase connection
# -------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


# -------------------------
# Get query from session
# -------------------------

query = st.session_state.get("query")

if not query:
    st.warning("No search query found. Please go back and run a search.")
    st.stop()


# -------------------------
# Extract resume text
# -------------------------

resume_bytes = st.session_state.get("resume_bytes")
resume_text = ""

if resume_bytes:
    try:
        resume_text = extract_text(io.BytesIO(resume_bytes))
    except:
        resume_text = ""


# -------------------------
# Fetch jobs from SerpAPI
# -------------------------

SERP_API_KEY = st.secrets["SERP_API_KEY"]

params = {
    "engine": "google_jobs",
    "q": query,
    "api_key": SERP_API_KEY
}

response = requests.get(
    "https://serpapi.com/search",
    params=params
)

data = response.json()

jobs = data.get("jobs_results", [])


if not jobs:
    st.warning("No jobs found.")
    st.stop()


# -------------------------
# Compute match scores
# -------------------------

job_descriptions = []

for job in jobs:
    desc = job.get("description", "")
    job_descriptions.append(desc)


if resume_text and job_descriptions:

    documents = [resume_text] + job_descriptions

    vectorizer = TfidfVectorizer(stop_words="english")

    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity_scores = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:]
    ).flatten()

    for i, job in enumerate(jobs):
        job["match_score"] = round(similarity_scores[i] * 100, 2)

    jobs = sorted(
        jobs,
        key=lambda x: x.get("match_score", 0),
        reverse=True
    )


# -------------------------
# Display top 50 jobs
# -------------------------

for i, job in enumerate(jobs[:50], start=1):

    title = job.get("title", "Unknown")
    company = job.get("company_name", "N/A")
    location = job.get("location", "N/A")
    description = job.get("description", "")

    salary = job.get("detected_extensions", {}).get(
        "salary",
        "Not listed"
    )

    match_score = job.get("match_score", 0)


    st.markdown(f"### {i}. {title}")

    st.markdown(f"**Match Score:** {match_score}%")

    st.markdown(f"**Company:** {company}")
    st.markdown(f"**Location:** {location}")
    st.markdown(f"**Salary:** {salary}")


    # Short summary
    if description:

        short_desc = description[:350] + "..."

        st.markdown("**Summary:**")

        st.write(short_desc)


    # Full description
    if description:

        with st.expander("Read full job description"):

            st.write(description)


    # Apply links
    if job.get("apply_options"):

        st.markdown("**Apply Here:**")

        for option in job["apply_options"]:

            name = option.get("title", "Apply")
            link = option.get("link")

            if link:
                st.markdown(f"- [{name}]({link})")


    # Source (LinkedIn / Indeed etc.)
    if job.get("via"):

        st.markdown(f"**Source:** {job['via']}")


    st.markdown("---")


# -------------------------
# Feedback section
# -------------------------

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

            supabase.table("feedback").insert({

                "anonymous_id": st.session_state.get(
                    "session_id",
                    "anon"
                ),

                "helpful": helpful,
                "would_pay": pay,
                "improvement": improvement

            }).execute()

            st.success(
                "🙏 Thank you! Feedback recorded."
            )

        except Exception as e:

            st.error("Could not save feedback.")
            st.write(e)
