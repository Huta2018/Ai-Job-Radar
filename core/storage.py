import sqlite3
from datetime import datetime

DB_PATH = "data/jobrader.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        is_paid INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS saved_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        title TEXT,
        company TEXT,
        link TEXT,
        status TEXT,
        saved_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def create_or_get_user(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()

    if not user:
        c.execute(
            "INSERT INTO users (email, created_at) VALUES (?, ?)",
            (email, datetime.now().isoformat())
        )
        conn.commit()

    conn.close()

def is_paid_user(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT is_paid FROM users WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()

    if result and result[0] == 1:
        return True
    return False

def save_job(email, title, company, link, status="saved"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    INSERT INTO saved_jobs (email, title, company, link, status, saved_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (email, title, company, link, status, datetime.now().isoformat()))

    conn.commit()
    conn.close()
