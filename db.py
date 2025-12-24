# db.py
import sqlite3
import json

DB_PATH = "content.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        title TEXT,
        content TEXT,
        keywords TEXT,
        seo_score INTEGER,
        readability_score INTEGER,
        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

def save_post(result: dict):
    conn = get_conn()
    conn.execute("""
    INSERT INTO posts (topic, title, content, keywords, seo_score, readability_score)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        result["metadata"]["topic"],
        result["title"],
        result["content"],
        json.dumps(result["keywords"]),
        result["seo_score"],
        result.get("readability_score")
    ))
    conn.commit()
