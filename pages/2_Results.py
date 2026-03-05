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
# OpenAI Client
# -----------------------------

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# Supabase Client
# -----------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -----------------------------
# Get Search Query
# -----------------------------

query = st.session_state.get("query")

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
# Fetch Jobs from SerpAPI
# -----------------------------

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

# -----------------------------
# Resume ↔ Job Similarity
# -----------------------------

job_descriptions = [job.get("description","") for job in jobs]

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

    prompt = f"""
You are a professional career assistant.

Goal:
Create resume improvement suggestions and a cover letter.

Rules:
- Do NOT invent experience
- Do NOT change resume meaning
- Only emphasize relevant skills
- Keep content truthful

Return exactly:

RESUME ENHANCEMENTS
3-5 bullets

SUGGESTED RESUME BULLETS
3 bullets

COVER LETTER
short professional letter

Resume:
{resume_text}

Job Title:
{job_title}

Company:
{company}

Location:
{location}

Job Description:
{job_description}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content


# -----------------------------
# Display Jobs
# -----------------------------

for i,job in enumerate(jobs[:50],start=1):

    title = job.get("title","Unknown")
    company = job.get("company_name","N/A")
    location = job.get("location","N/A")
    description = job.get("description","")

    salary = job.get(
        "detected_extensions",{}
    ).get("salary","Not listed")

    match_score = job.get("match_score",0)

    st.markdown(f"### {i}. {title}")

    st.markdown(f"**Match Score:** {match_score}%")
    st.markdown(f"**Company:** {company}")
    st.markdown(f"**Location:** {location}")
    st.markdown(f"**Salary:** {salary}")

    # Summary bullets
    if description:

        sentences = re.split(r'[.!?]',description)

        st.markdown("**Key Highlights:**")

        for s in sentences[:4]:
            if len(s.strip())>40:
                st.markdown(f"- {s.strip()}")

    # Full description
    if description:
        with st.expander("Read Full Job Description"):
            st.write(description)

    # Apply links
    if job.get("apply_options"):

        st.markdown("**Apply Here:**")

        for option in job["apply_options"]:

            name = option.get("title","Apply")
            link = option.get("link")

            if link:
                st.markdown(f"- [{name}]({link})")

    # Job source
    if job.get("via"):
        st.markdown(f"**Source:** {job['via']}")

    # AI Resume Generator
    with st.expander("🧠 Generate Resume + Cover Letter"):

        if st.button(f"Generate Materials {i}",key=f"ai_{i}"):

            if not resume_text:
                st.warning("Upload resume first.")

            else:

                with st.spinner("Generating AI suggestions..."):

                    ai_output = generate_application_materials(
                        resume_text,
                        title,
                        company,
                        location,
                        description
                    )

                st.markdown("### AI Application Assistant")
                st.code(ai_output)

    st.markdown("---")


# -----------------------------
# Skill Gap Analysis
# -----------------------------

st.markdown("## 🧠 Career Growth Suggestions")

skills = [
"python","sql","machine learning","deep learning",
"tensorflow","pytorch","docker","kubernetes",
"aws","spark","pandas","statistics",
"data visualization","power bi","tableau","nlp"
]

resume_lower = resume_text.lower()

resume_skills = [s for s in skills if s in resume_lower]

job_skill_counts = {}

for job in jobs[:20]:

    desc = job.get("description","").lower()

    for s in skills:

        if s in desc:
            job_skill_counts[s] = job_skill_counts.get(s,0)+1

missing = []

for skill,count in job_skill_counts.items():

    if skill not in resume_skills:
        missing.append((skill,count))

missing = sorted(
    missing,
    key=lambda x:x[1],
    reverse=True
)

if missing:

    st.markdown("### Skills To Strengthen")

    for skill,count in missing[:5]:
        st.markdown(f"- **{skill.title()}** (seen in {count} jobs)")

    st.markdown("### Suggested Learning Topics")

    learning_map = {
        "sql":"Advanced SQL for Data Analytics",
        "aws":"Cloud Computing for Data Science",
        "docker":"Containerizing Machine Learning Models",
        "spark":"Big Data Processing with Spark",
        "nlp":"Natural Language Processing Applications"
    }

    for skill,_ in missing[:5]:

        topic = learning_map.get(
            skill,
            f"Advanced {skill.title()} Applications"
        )

        st.markdown(f"- {topic}")

# -----------------------------
# Feedback Section
# -----------------------------

st.markdown("## 💬 Feedback")

with st.form("feedback_form"):

    st.write("Help us improve this tool!")

    last_name = st.text_input(
        "Last Name (optional – helps us understand diversity of usage)"
    )

    helpful = st.radio(
        "Is the job ranking helpful?",
        ["Yes 👍","Somewhat 🤔","No 👎"]
    )

    pay = st.radio(
        "Would you pay $10/month for unlimited smart ranked job searches?",
        ["Yes 💳","Maybe 🤷","No ❌"]
    )

    improvement = st.text_area(
        "What should we improve?"
    )

    submit = st.form_submit_button("Submit Feedback")

    if submit:

        try:

            supabase.table("feedback").insert({

                "anonymous_id": st.session_state.get(
                    "session_id","anon"
                ),

                "last_name": last_name,

                "helpful": helpful,

                "would_pay": pay,

                "improvement": improvement

            }).execute()

            st.success("Thank you for the feedback!")

        except Exception as e:

            st.error("Could not save feedback.")
            st.write(e)
