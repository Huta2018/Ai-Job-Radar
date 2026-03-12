import streamlit as st
import requests
import io
import re
import uuid
from datetime import datetime

from pdfminer.high_level import extract_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openai import OpenAI
from supabase import create_client

# ---------------------------------
# Secrets / Clients
# ---------------------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SERP_API_KEY = st.secrets["SERP_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------
# Page Title
# ---------------------------------

st.title("🔎 Job Results")

# ---------------------------------
# Load session data
# ---------------------------------

query = st.session_state.get("query")
country = st.session_state.get("country_name", "United States")
resume_bytes = st.session_state.get("resume_bytes")

if not query:
    st.warning("No search query found. Please go back and run a search.")
    st.stop()

# ---------------------------------
# Extract resume text
# ---------------------------------

resume_text = ""

if resume_bytes:
    try:
        resume_text = extract_text(io.BytesIO(resume_bytes))
    except Exception:
        resume_text = ""

# ---------------------------------
# Fetch jobs from SerpAPI (robust pagination)
# ---------------------------------

all_jobs = []

# Google Jobs usually returns ~10 per page
# We fetch up to 100 using safe pagination
for start in [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]:

    params = {
        "engine": "google_jobs",
        "q": query,                 # do NOT append "jobs"
        "location": country,
        "hl": "en",
        "api_key": SERP_API_KEY,
        "start": start
    }

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params=params,
            timeout=20
        )

        data = response.json()

        new_jobs = data.get("jobs_results", [])

        if new_jobs:
            all_jobs.extend(new_jobs)

    except Exception:
        pass

jobs = all_jobs

if not jobs:
    st.warning("No jobs found. Try another title or location.")
    st.stop()

# ---------------------------------
# Resume similarity scoring
# ---------------------------------

job_descriptions = [j.get("description", "") for j in jobs]

if resume_text and job_descriptions:

    docs = [resume_text] + job_descriptions

    vectorizer = TfidfVectorizer(stop_words="english")

    tfidf = vectorizer.fit_transform(docs)

    scores = cosine_similarity(
        tfidf[0:1],
        tfidf[1:]
    ).flatten()

    for i, job in enumerate(jobs):
        job["match_score"] = round(scores[i] * 100, 2)

    jobs = sorted(
        jobs,
        key=lambda x: x.get("match_score", 0),
        reverse=True
    )

# ---------------------------------
# AI resume + cover letter generator
# ---------------------------------

def generate_application_materials(resume_text, job_title, company, job_description):

    prompt = f"""
You are a professional career assistant.

Create resume improvement suggestions and a short cover letter.

Rules:
- Do not invent experience
- Only improve wording

Return:

RESUME IMPROVEMENTS
3 bullet points

COVER LETTER

Resume:
{resume_text}

Job Title: {job_title}
Company: {company}

Job Description:
{job_description}
"""

    try:

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception:
        return "AI generation unavailable."

# ---------------------------------
# Display Jobs
# ---------------------------------

st.subheader(f"Top Job Matches ({len(jobs)} jobs found)")

for i, job in enumerate(jobs, start=1):

    title = job.get("title", "Unknown")
    company = job.get("company_name", "N/A")
    location = job.get("location", "N/A")
    description = job.get("description", "")
    score = job.get("match_score", 0)

    salary = job.get(
        "detected_extensions",
        {}
    ).get("salary", "Not listed")

    st.markdown(f"### {i}. {title}")
    st.write(f"**Match Score:** {score}%")
    st.write(f"**Company:** {company}")
    st.write(f"**Location:** {location}")
    st.write(f"**Salary:** {salary}")

    # Highlights
    if description:
        sentences = re.split(r'[.!?]', description)
        st.write("Highlights:")
        for s in sentences[:3]:
            if len(s.strip()) > 40:
                st.write("-", s.strip())

    # Full description
    if description:
        with st.expander("Full Job Description"):
            st.write(description)

    # ---------------------------------
    # Apply Links
    # ---------------------------------

    st.write("Apply Links:")

    links_found = False

    if job.get("apply_options"):

        for option in job["apply_options"]:

            name = option.get("title", "Apply")
            link = option.get("link")

            if link:
                st.markdown(f"🔗 [{name}]({link})")
                links_found = True

    # Google fallback
    google_link = f"https://www.google.com/search?q={title.replace(' ','+')}+{company.replace(' ','+')}+jobs"
    st.markdown(f"🌐 [Search this job on Google]({google_link})")

    # LinkedIn fallback
    linkedin_link = f"https://www.linkedin.com/jobs/search/?keywords={title.replace(' ','%20')}&location={country.replace(' ','%20')}"
    st.markdown(f"💼 [Find similar jobs on LinkedIn]({linkedin_link})")

    if not links_found:
        st.info("Direct apply links unavailable — use Google or LinkedIn search above.")

    # ---------------------------------
    # AI Resume + Cover Letter
    # ---------------------------------

    with st.expander("Generate Resume + Cover Letter"):

        if st.button(
            f"Generate for job {i}",
            key=f"ai_{i}"
        ):

            output = generate_application_materials(
                resume_text,
                title,
                company,
                description
            )

            st.code(output)

    st.markdown("---")

# ---------------------------------
# Feedback Section
# ---------------------------------

st.header("💬 Help Improve AI Job Radar")

rating = st.slider(
    "How useful was AI Job Radar?",
    1,
    5,
    3
)

found_unique = st.radio(
    "Did this tool show jobs you wouldn't easily find elsewhere?",
    ["Yes", "Somewhat", "No"]
)

would_pay = st.radio(
    "If this tool consistently found great job matches, would you pay for it?",
    ["Yes", "Maybe", "No"]
)

preferred_price = None

if would_pay in ["Yes", "Maybe"]:
    preferred_price = st.radio(
        "What monthly price would feel reasonable?",
        [
            "$5 / month",
            "$10 / month",
            "$15 / month",
            "$20+ / month"
        ]
    )

features = st.multiselect(
    "What features should we add next?",
    [
        "AI Resume Matching",
        "Auto Apply to Jobs",
        "Daily Job Alerts",
        "Company Insights",
        "Salary Prediction",
        "Interview Preparation",
        "LinkedIn Integration"
    ]
)

comment = st.text_area(
    "Any suggestions to improve AI Job Radar?"
)

# ---------------------------------
# Submit Feedback
# ---------------------------------

if st.button("Submit Feedback", key="submit_feedback"):

    data = {
        "anonymous_id": str(uuid.uuid4()),
        "rating": rating,
        "unique_jobs_found": found_unique,
        "would_pay": would_pay,
        "preferred_price": preferred_price,
        "requested_features": ", ".join(features),
        "comment": comment,
        "timestamp": datetime.now().isoformat()
    }

    try:
        supabase.table("feedback").insert(data).execute()
        st.success("✅ Thank you! Your feedback was submitted.")
    except Exception:
        st.warning("Feedback submission failed. Please try again.")
