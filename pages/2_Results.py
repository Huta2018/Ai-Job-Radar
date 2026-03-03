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

st.title("📊 Smart Ranked Job Results")
st.info("🚀 AI Job Radar – Pilot Version")

# -------------------------------------
# LOAD API KEY
# -------------------------------------
try:
    SERP_API_KEY = st.secrets["SERP_API_KEY"]
except Exception:
    st.error("SERP_API_KEY not found in secrets.")
    st.stop()

query = st.session_state.get("query")

if not query:
    st.warning("No search query found.")
    st.stop()

st.write(f"Searching for: **{query}**")

# -------------------------------------
# RESUME EXTRACTION
# -------------------------------------
def extract_resume_text():
    resume_bytes = st.session_state.get("resume_bytes")
    resume_name = st.session_state.get("resume_name")

    if not resume_bytes:
        return ""

    try:
        if resume_name.endswith(".pdf"):
            return extract_text(io.BytesIO(resume_bytes)).lower()
        elif resume_name.endswith(".docx"):
            doc = Document(io.BytesIO(resume_bytes))
            return "\n".join([p.text for p in doc.paragraphs]).lower()
        else:
            return resume_bytes.decode("utf-8").lower()
    except:
        return ""

# -------------------------------------
# SALARY PARSER
# -------------------------------------
def extract_salary(job):
    extensions = job.get("detected_extensions", {})
    salary_text = extensions.get("salary")

    if not salary_text:
        return None

    original = salary_text.lower()
    cleaned = original.replace(",", "")
    is_hourly = "hour" in original

    numbers = re.findall(r"\d+\.?\d*", cleaned)

    if not numbers:
        return None

    parsed = []

    for num in numbers:
        value = float(num)
        if "k" in original:
            value *= 1000
        parsed.append(int(value))

    if len(parsed) >= 2:
        low, high = parsed[0], parsed[1]
        if is_hourly:
            return f"${low:,} - ${high:,} per hour"
        else:
            return f"${low:,} - ${high:,} per year"

    value = parsed[0]

    if is_hourly:
        return f"${value:,} per hour"
    else:
        return f"${value:,} per year"

# -------------------------------------
# SCORE FUNCTION
# -------------------------------------
def compute_score(job, resume_text, query):
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()

    raw_score = 0

    for word in query.lower().split():
        if word in title:
            raw_score += 20
        if word in description:
            raw_score += 5

    resume_words = set(resume_text.split())

    for word in resume_words:
        if len(word) > 4 and word in description:
            raw_score += 1

    return min(10, max(1, raw_score // 10))

# -------------------------------------
# CALL API
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

resume_text = extract_resume_text()

ranked_jobs = []

for job in jobs:
    score = compute_score(job, resume_text, query)
    salary = extract_salary(job)
    ranked_jobs.append((score, salary, job))

ranked_jobs.sort(key=lambda x: x[0], reverse=True)

# -------------------------------------
# DISPLAY TOP 25
# -------------------------------------
top_jobs = ranked_jobs[:25]

st.success(f"Showing Top {len(top_jobs)} Ranked Jobs")

for index, (score, salary, job) in enumerate(top_jobs, start=1):

    title = job.get("title", "No title")
    company = job.get("company_name", "N/A")
    location = job.get("location", "N/A")
    description = job.get("description", "")
    related_links = job.get("related_links", [])

    st.subheader(f"{index}. {title}")
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
# FEEDBACK SECTION (ALWAYS AFTER JOBS)
# =====================================

st.markdown("## 💬 Quick Feedback")

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
            "user": st.session_state.get("user_email", "anonymous"),
            "query": query,
            "helpful": helpful,
            "would_pay": pay,
            "improvement": improvement
        }

        df = pd.DataFrame([feedback_data])

        file_path = "data/feedback.csv"

        if os.path.exists(file_path):
            df.to_csv(file_path, mode="a", header=False, index=False)
        else:
            df.to_csv(file_path, index=False)

        st.success("🙏 Thank you! Your feedback has been recorded.")
