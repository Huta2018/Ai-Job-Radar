import streamlit as st
import requests
import io
import re

from supabase import create_client
from pdfminer.high_level import extract_text

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.title("🔎 Job Results")

# -------------------------
# Supabase connection
# -------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------------------------
# Get query
# -------------------------

query = st.session_state.get("query")

if not query:
    st.warning("No search query found.")
    st.stop()

# -------------------------
# Resume text extraction
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
# Resume ↔ Job similarity
# -------------------------

job_descriptions = [job.get("description","") for job in jobs]

if resume_text and job_descriptions:

    documents = [resume_text] + job_descriptions

    vectorizer = TfidfVectorizer(stop_words="english")

    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(
        tfidf_matrix[0:1],
        tfidf_matrix[1:]
    ).flatten()

    for i, job in enumerate(jobs):
        job["match_score"] = round(similarity[i] * 100,2)

    jobs = sorted(
        jobs,
        key=lambda x: x.get("match_score",0),
        reverse=True
    )

# -------------------------
# Display Top 50 Jobs
# -------------------------

for i, job in enumerate(jobs[:50], start=1):

    title = job.get("title","Unknown")
    company = job.get("company_name","N/A")
    location = job.get("location","N/A")
    description = job.get("description","")

    salary = job.get("detected_extensions",{}).get(
        "salary","Not listed"
    )

    match_score = job.get("match_score",0)

    st.markdown(f"### {i}. {title}")

    st.markdown(f"**Match Score:** {match_score}%")
    st.markdown(f"**Company:** {company}")
    st.markdown(f"**Location:** {location}")
    st.markdown(f"**Salary:** {salary}")

    # Summary bullet extraction
    if description:

        sentences = re.split(r'[.!?]', description)

        bullets = sentences[:4]

        st.markdown("**Key Highlights:**")

        for b in bullets:
            if len(b.strip()) > 40:
                st.markdown(f"- {b.strip()}")

    # Full description
    if description:

        with st.expander("Read Full Job Description"):
            st.write(description)

    # Application links
    if job.get("apply_options"):

        st.markdown("**Apply Here:**")

        for option in job["apply_options"]:

            name = option.get("title","Apply")
            link = option.get("link")

            if link:
                st.markdown(f"- [{name}]({link})")

    # Source
    if job.get("via"):
        st.markdown(f"**Source:** {job['via']}")

    st.markdown("---")

# -------------------------
# SKILL GAP ANALYSIS
# -------------------------

st.markdown("## 🧠 Career Growth Suggestions")

skills = [
    "python","sql","machine learning","deep learning",
    "tensorflow","pytorch","docker","kubernetes",
    "aws","spark","pandas","data analysis",
    "statistics","data visualization","power bi",
    "tableau","cloud","nlp"
]

resume_skills = []

resume_lower = resume_text.lower()

for s in skills:
    if s in resume_lower:
        resume_skills.append(s)

job_skill_counts = {}

for job in jobs[:20]:

    desc = job.get("description","").lower()

    for s in skills:

        if s in desc:
            job_skill_counts[s] = job_skill_counts.get(s,0)+1

missing_skills = []

for skill,count in job_skill_counts.items():

    if skill not in resume_skills:
        missing_skills.append((skill,count))

missing_skills = sorted(
    missing_skills,
    key=lambda x:x[1],
    reverse=True
)

if missing_skills:

    st.markdown("### Skills To Strengthen")

    for skill,count in missing_skills[:5]:

        st.markdown(f"- **{skill.title()}** (seen in {count} jobs)")

    st.markdown("### Suggested Learning Topics")

    learning_map = {
        "sql":"Advanced SQL for Data Analytics",
        "aws":"Cloud Computing for Data Science",
        "docker":"Containerizing Machine Learning Models",
        "spark":"Big Data Processing with Spark",
        "machine learning":"Advanced Machine Learning Systems",
        "nlp":"Natural Language Processing Applications",
        "pytorch":"Deep Learning with PyTorch",
        "tensorflow":"Deep Learning with TensorFlow"
    }

    for skill,_ in missing_skills[:5]:

        topic = learning_map.get(
            skill,
            f"Advanced {skill.title()} Applications"
        )

        st.markdown(f"- {topic}")

# -------------------------
# FEEDBACK SECTION
# -------------------------

st.markdown("## 💬 Anonymous Feedback")

with st.form("feedback_form"):

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

                "helpful": helpful,
                "would_pay": pay,
                "improvement": improvement

            }).execute()

            st.success("Thank you for the feedback!")

        except Exception as e:

            st.error("Could not save feedback.")
            st.write(e)
