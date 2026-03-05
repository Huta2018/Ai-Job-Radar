import streamlit as st
import requests
import io
import re

from pdfminer.high_level import extract_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openai import OpenAI

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
    except:
        resume_text = ""

# ---------------------------------
# Fetch jobs from SerpAPI
# ---------------------------------

SERP_API_KEY = st.secrets["SERP_API_KEY"]

params = {
    "engine": "google_jobs",
    "q": f"{query} jobs",
    "location": country,
    "hl": "en",
    "api_key": SERP_API_KEY
}

response = requests.get(
    "https://serpapi.com/search",
    params=params
)

data = response.json()

jobs = data.get("jobs_results", [])

if not jobs:
    st.warning("No jobs found. Try a broader job title.")
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
# OpenAI client
# ---------------------------------

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def generate_application_materials(
    resume_text,
    job_title,
    company,
    job_description
):

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
            messages=[{"role":"user","content":prompt}]
        )

        return response.choices[0].message.content

    except:
        return "AI generation unavailable."

# ---------------------------------
# Display jobs
# ---------------------------------

st.subheader("Top Job Matches")

for i, job in enumerate(jobs, start=1):

    title = job.get("title", "Unknown")
    company = job.get("company_name", "N/A")
    location = job.get("location", "N/A")

    description = job.get("description", "")

    salary = job.get(
        "detected_extensions",
        {}
    ).get("salary", "Not listed")

    score = job.get("match_score", 0)

    st.markdown(f"### {i}. {title}")

    st.write(f"Match Score: {score}%")
    st.write(f"Company: {company}")
    st.write(f"Location: {location}")
    st.write(f"Salary: {salary}")

    # Short summary
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

    # Apply links
    if job.get("apply_options"):

        st.write("Apply Links:")

        for option in job["apply_options"]:

            name = option.get("title", "Apply")
            link = option.get("link")

            if link:
                st.markdown(f"[{name}]({link})")

    # AI Resume + Cover Letter
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
