import streamlit as st
import requests
import urllib.parse
import io
import re
from pdfminer.high_level import extract_text
from docx import Document

st.title("📊 Smart Ranked Job Results")

# -------------------------------------
# LOAD API KEY
# -------------------------------------
try:
    SERP_API_KEY = st.secrets["SERP_API_KEY"]
except Exception:
    st.error("SERP_API_KEY not found in .streamlit/secrets.toml")
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
# PROPER SALARY PARSER (FIXED)
# -------------------------------------
def extract_salary(job):

    extensions = job.get("detected_extensions", {})
    salary_text = extensions.get("salary")

    if not salary_text:
        return None

    original = salary_text.lower()
    cleaned = original.replace(",", "")

    is_hourly = "hour" in original

    # Extract numbers including decimals
    numbers = re.findall(r"\d+\.?\d*", cleaned)

    if not numbers:
        return None

    parsed = []

    for num in numbers:
        value = float(num)

        # Handle "k"
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
# EXPERIENCE LEVEL DETECTION
# -------------------------------------
def detect_level(title):
    title = title.lower()
    if "senior" in title:
        return "Senior"
    elif "junior" in title:
        return "Junior"
    elif "lead" in title:
        return "Lead"
    elif "intern" in title:
        return "Intern"
    else:
        return "Mid"

# -------------------------------------
# STRUCTURED SUMMARY
# -------------------------------------
def generate_structured_summary(description):

    if not description:
        return [], []

    description = description.replace("\n", " ")
    sentences = description.split(". ")

    overview = []
    requirements = []

    requirement_keywords = [
        "require", "must", "experience", "proficiency",
        "degree", "skills", "knowledge", "ability",
        "familiarity", "minimum"
    ]

    for s in sentences:
        s = s.strip()

        if len(s) < 60:
            continue

        if any(k in s.lower() for k in requirement_keywords):
            if len(requirements) < 5:
                requirements.append(s + ".")
        else:
            if len(overview) < 5:
                overview.append(s + ".")

    return overview, requirements

# -------------------------------------
# RANKING FUNCTION (1–10)
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
# CALL SERPAPI
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

if "error" in data:
    st.error(data["error"])
    st.stop()

jobs = data.get("jobs_results", [])

if not jobs:
    st.warning("No jobs found.")
    st.stop()

resume_text = extract_resume_text()

# -------------------------------------
# RANK JOBS
# -------------------------------------
ranked_jobs = []

for job in jobs:
    score = compute_score(job, resume_text, query)
    salary = extract_salary(job)
    level = detect_level(job.get("title", ""))
    ranked_jobs.append((score, salary, level, job))

ranked_jobs.sort(key=lambda x: x[0], reverse=True)

# -------------------------------------
# SIDEBAR FILTERS
# -------------------------------------
st.sidebar.header("Filters")

min_salary = st.sidebar.number_input("Minimum Salary (Yearly Base)", min_value=0, value=0)

level_filter = st.sidebar.selectbox(
    "Experience Level",
    ["All", "Junior", "Mid", "Senior", "Lead", "Intern"]
)

filtered_jobs = []

for score, salary, level, job in ranked_jobs:

    if min_salary and salary:
        numbers = re.findall(r"\d+", salary.replace(",", ""))
        if numbers:
            if int(numbers[0]) < min_salary:
                continue

    if level_filter != "All" and level != level_filter:
        continue

    filtered_jobs.append((score, salary, level, job))

# -------------------------------------
# DISPLAY TOP 25
# -------------------------------------
top_jobs = filtered_jobs[:25]

st.success(f"Showing Top {len(top_jobs)} Ranked Jobs")

for index, (score, salary, level, job) in enumerate(top_jobs, start=1):

    title = job.get("title", "No title")
    company = job.get("company_name", "N/A")
    location = job.get("location", "N/A")
    description = job.get("description", "")
    related_links = job.get("related_links", [])

    st.subheader(f"{index}. {title}")
    st.write(f"⭐ Match Score: {score}/10")
    st.write(f"Level: {level}")
    st.write(f"Company: {company}")
    st.write(f"Location: {location}")

    if salary:
        st.write(f"Salary (Detected): {salary}")

    overview, requirements = generate_structured_summary(description)

    st.write("### 📝 Job Overview")
    if overview:
        for point in overview:
            st.markdown(f"- {point}")
    else:
        st.write("Overview not available.")

    st.write("### 🎯 Key Requirements")
    if requirements:
        for point in requirements:
            st.markdown(f"- {point}")
    else:
        st.write("Requirements not clearly listed.")

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

# -------------------------------------
# SHOW MORE BUTTON
# -------------------------------------
if len(filtered_jobs) > 25:
    if st.button("Show More Jobs", key="show_more_btn"):
        for index, (score, salary, level, job) in enumerate(filtered_jobs[25:], start=26):
            st.subheader(f"{index}. {job.get('title')}")
            st.write(f"⭐ {score}/10")
            st.markdown("---")
