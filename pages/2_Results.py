import streamlit as st
import requests
import urllib.parse
import io
import re
import os
import datetime
import pandas as pd
from pdfminer.high_level import extract_text
from docx import Document
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

st.title("📊 Smart Ranked Job Results")

# -------------------------------------
# Load API Key
# -------------------------------------
try:
    SERP_API_KEY = st.secrets["SERP_API_KEY"]
except:
    st.error("API key not found.")
    st.stop()

query = st.session_state.get("query")
if not query:
    st.warning("No search query found.")
    st.stop()

st.write(f"Searching for: **{query}**")

# -------------------------------------
# Extract Resume (in memory only)
# -------------------------------------
def extract_resume_text():
    resume_bytes = st.session_state.get("resume_bytes")
    resume_name = st.session_state.get("resume_name")

    if not resume_bytes:
        return ""

    try:
        if resume_name.endswith(".pdf"):
            return extract_text(io.BytesIO(resume_bytes))
        elif resume_name.endswith(".docx"):
            doc = Document(io.BytesIO(resume_bytes))
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            return ""
    except:
        return ""

resume_text = extract_resume_text()

# -------------------------------------
# Salary Extraction
# -------------------------------------
def extract_salary(job):
    extensions = job.get("detected_extensions", {})
    salary_text = extensions.get("salary")

    if not salary_text:
        return None

    cleaned = salary_text.replace(",", "").lower()
    numbers = re.findall(r"\d+\.?\d*", cleaned)

    if not numbers:
        return salary_text

    values = []
    for num in numbers:
        val = float(num)
        if "k" in cleaned:
            val *= 1000
        values.append(int(val))

    if len(values) >= 2:
        return f"${values[0]:,} - ${values[1]:,}"
    return f"${values[0]:,}"

# -------------------------------------
# Matching Algorithm (TF-IDF)
# -------------------------------------
def compute_similarity(resume_text, job_description):

    if not resume_text:
        return 5  # neutral score if no resume

    documents = [resume_text, job_description]
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(
        tfidf_matrix[0:1], tfidf_matrix[1:2]
    )[0][0]

    score = int(similarity * 10)
    return max(1, min(10, score))

# -------------------------------------
# API Call
# -------------------------------------
params = {
    "engine": "google_jobs",
    "q": query,
    "hl": "en",
    "chips": "date_posted:3days",
    "api_key": SERP_API_KEY
}

response = requests.get("https://serpapi.com/search", params=params)
data = response.json()

jobs = data.get("jobs_results", [])

if not jobs:
    st.warning("No jobs found.")
    st.stop()

ranked_jobs = []

for job in jobs:
    description = job.get("description", "")
    score = compute_similarity(resume_text, description)
    salary = extract_salary(job)
    ranked_jobs.append((score, salary, job))

ranked_jobs.sort(key=lambda x: x[0], reverse=True)

top_jobs = ranked_jobs[:25]

st.success(f"Showing Top {len(top_jobs)} Ranked Jobs")

# -------------------------------------
# Display Jobs
# -------------------------------------
for idx, (score, salary, job) in enumerate(top_jobs, start=1):

    title = job.get("title", "No Title")
    company = job.get("company_name", "N/A")
    location = job.get("location", "N/A")
    description = job.get("description", "")
    related_links = job.get("related_links", [])

    st.subheader(f"{idx}. {title}")
    st.write(f"⭐ Match Score: {score}/10")
    st.write(f"Company: {company}")
    st.write(f"Location: {location}")

    if salary:
        st.write(f"Salary: {salary}")

    with st.expander("📖 View Full Description"):
        st.write(description)

    st.write("### 🔗 Apply Options")

    if related_links:
        for link in related_links:
            source = link.get("text", "Apply")
            url = link.get("link")
            if url:
                st.markdown(f"- [{source}]({url})")
    else:
        linkedin_search = (
            "https://www.linkedin.com/jobs/search/?keywords="
            f"{urllib.parse.quote(title + ' ' + company)}"
        )
        st.markdown(f"- [Search on LinkedIn]({linkedin_search})")

    st.markdown("---")

# =====================================
# Anonymous Feedback Section
# =====================================

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

        os.makedirs("data", exist_ok=True)

        feedback_data = {
            "timestamp": datetime.datetime.now(),
            "anonymous_id": st.session_state.get("session_id"),
            "helpful": helpful,
            "would_pay": pay,
            "improvement": improvement
        }

        df = pd.DataFrame([feedback_data])

        file_path = "data/anonymous_feedback.csv"

        if os.path.exists(file_path):
            df.to_csv(file_path, mode="a", header=False, index=False)
        else:
            df.to_csv(file_path, index=False)

        st.success("🙏 Thank you! Your feedback has been recorded anonymously.")
