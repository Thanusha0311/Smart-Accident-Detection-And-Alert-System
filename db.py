# backend/db.py
import sqlite3
import datetime


DB_PATH = "accident_history.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        email TEXT,
        vehicles INTEGER,
        severity TEXT,
        impact REAL,
        video_path TEXT
    )
    """)
    conn.commit()
    conn.close()


def log_event(email, vehicles, severity, impact, video_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO events
        (timestamp, email, vehicles, severity, impact, video_path)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            email,
            vehicles,
            severity,
            impact,
            video_path
        )
    )

    conn.commit()
    conn.close()


def get_recent_events(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT timestamp, email, vehicles, severity, impact
        FROM events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = c.fetchall()
    conn.close()

    return [
        {
            "timestamp": r[0],
            "email": r[1],
            "vehicles": r[2],
            "severity": r[3],
            "impact": r[4]
        }
        for r in rows
    ]
