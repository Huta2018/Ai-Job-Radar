import streamlit as st
import requests
import io
import re

from pdfminer.high_level import extract_text
from supabase import create_client
from openai import OpenAI

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


st.title("🔎 Job Results")

# -----------------------------
# OpenAI
# -----------------------------

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Supabase
# -----------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -----------------------------
# Query + Country
# -----------------------------

query = st.session_state.get("query")
country = st.session_state.get("country","United States")

if not query:
    st.warning("No search query found.")
    st.stop()

# -----------------------------
# Resume Extraction
# -----------------------------

resume_bytes = st.session_state.get("resume_bytes")

resume_text = ""

if resume_bytes:
    try:
        resume_text = extract_text(io.BytesIO(resume_bytes))
    except:
        resume_text = ""

# -----------------------------
# Fetch Jobs (Multiple Pages)
# -----------------------------

SERP_API_KEY = st.secrets["SERP_API_KEY"]

jobs = []

for page in range(5):

    params = {
        "engine":"google_jobs",
        "q":query,
        "location":country,
        "start":page*10,
        "api_key":SERP_API_KEY
    }

    response = requests.get(
        "https://serpapi.com/search",
        params=params
    )

    data = response.json()

    new_jobs = data.get("jobs_results",[])

    jobs.extend(new_jobs)

if not jobs:
    st.warning("No jobs found.")
    st.stop()

# -----------------------------
# Resume ↔ Job Similarity
# -----------------------------

job_descriptions = [j.get("description","") for j in jobs]

if resume_text and job_descriptions:

    docs = [resume_text] + job_descriptions

    vectorizer = TfidfVectorizer(stop_words="english")

    tfidf = vectorizer.fit_transform(docs)

    scores = cosine_similarity(
        tfidf[0:1],
        tfidf[1:]
    ).flatten()

    for i,job in enumerate(jobs):
        job["match_score"] = round(scores[i]*100,2)

    jobs = sorted(
        jobs,
        key=lambda x:x.get("match_score",0),
        reverse=True
    )

# -----------------------------
# AI Resume + Cover Letter
# -----------------------------

def generate_application_materials(
    resume_text,
    job_title,
    company,
    location,
    job_description
):

    prompt=f"""
You are a professional career assistant.

Create resume improvement suggestions and a cover letter.

Rules:
- Do NOT invent experience
- Only emphasize relevant skills

Return:

RESUME ENHANCEMENTS
3 bullets

SUGGESTED BULLETS
3 bullets

COVER LETTER

Resume:
{resume_text}

Job Title:{job_title}
Company:{company}
Location:{location}

Job Description:
{job_description}
"""

    try:

        response=client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[{"role":"user","content":prompt}]
        )

        return response.choices[0].message.content

    except:
        return "AI generation temporarily unavailable."

# -----------------------------
# Display Top 25 Jobs
# -----------------------------

st.subheader("Top Job Matches")

top_jobs = jobs[:25]

for i,job in enumerate(top_jobs,start=1):

    title=job.get("title","Unknown")
    company=job.get("company_name","N/A")
    location=job.get("location","N/A")

    description=job.get("description","")

    salary=job.get(
        "detected_extensions",{}
    ).get("salary","Not listed")

    score=job.get("match_score",0)

    st.markdown(f"### {i}. {title}")

    st.write(f"Match Score: {score}%")
    st.write(company)
    st.write(location)
    st.write(f"Salary: {salary}")

    if description:

        sentences=re.split(r'[.!?]',description)

        st.write("Key Highlights:")

        for s in sentences[:4]:
            if len(s.strip())>40:
                st.write("-",s.strip())

    if description:

        with st.expander("Full Description"):
            st.write(description)

    if job.get("apply_options"):

        st.write("Apply:")

        for option in job["apply_options"]:

            name=option.get("title","Apply")
            link=option.get("link")

            if link:
                st.markdown(f"[{name}]({link})")

    with st.expander("Generate Resume + Cover Letter"):

        if st.button(
            f"Generate {i}",
            key=f"ai_{i}"
        ):

            output=generate_application_materials(
                resume_text,
                title,
                company,
                location,
                description
            )

            st.code(output)

    st.markdown("---")

# -----------------------------
# Show More Jobs
# -----------------------------

if len(jobs)>25:

    if st.button("Show More Jobs"):

        for i,job in enumerate(jobs[25:],start=26):

            title=job.get("title","Unknown")
            company=job.get("company_name","N/A")
            location=job.get("location","N/A")

            st.markdown(f"### {i}. {title}")
            st.write(company)
            st.write(location)

            st.markdown("---")

# -----------------------------
# Feedback
# -----------------------------

st.markdown("## Feedback")

with st.form("feedback"):

    last_name=st.text_input(
        "Last Name (optional)"
    )

    helpful=st.radio(
        "Is this helpful?",
        ["Yes","Somewhat","No"]
    )

    pay=st.radio(
        "Would you pay $10/month?",
        ["Yes","Maybe","No"]
    )

    improvement=st.text_area(
        "Suggestions"
    )

    submit=st.form_submit_button("Submit")

    if submit:

        try:

            supabase.table("feedback").insert({

                "last_name":last_name,
                "helpful":helpful,
                "would_pay":pay,
                "improvement":improvement

            }).execute()

            st.success("Feedback submitted")

        except:

            st.error("Could not save feedback")
