"""
database.py

Handles all SQLite database setup and queries for the app.

Tables:
- sessions: a shared "room" between two people
- movies: cached movie data pulled from the streaming API
- swipes: records who swiped left/right on which movie, in which session
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "movies.db"


def get_connection():
    """
    Opens a connection to the SQLite database.
    Using `row_factory` lets us access columns by name, e.g. row["title"],
    instead of by index, e.g. row[2]. Much easier to read.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the tables if they don't already exist.
    Safe to call every time the app starts.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            title TEXT NOT NULL,
            overview TEXT,
            poster_url TEXT,
            streaming_service TEXT,
            rating REAL,
            genres TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        )
    """)

    # --- Migration for existing databases created before rating/genres existed ---
    # CREATE TABLE IF NOT EXISTS does nothing if the table already exists with
    # an older schema, so we check for the columns and add them if missing.
    existing_columns = {row["name"] for row in cursor.execute("PRAGMA table_info(movies)")}
    if "rating" not in existing_columns:
        cursor.execute("ALTER TABLE movies ADD COLUMN rating REAL")
    if "genres" not in existing_columns:
        cursor.execute("ALTER TABLE movies ADD COLUMN genres TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS swipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            movie_id INTEGER NOT NULL,
            direction TEXT NOT NULL CHECK (direction IN ('left', 'right')),
            swiped_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id),
            FOREIGN KEY (movie_id) REFERENCES movies (id),
            UNIQUE (session_id, user_name, movie_id)
        )
    """)

    conn.commit()
    conn.close()


# ---------- Session helpers ----------

def create_session(session_id: str):
    conn = get_connection()
    conn.execute("INSERT INTO sessions (id) VALUES (?)", (session_id,))
    conn.commit()
    conn.close()


def session_exists(session_id: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    return row is not None


# ---------- Movie helpers ----------

def add_movie(session_id: str, external_id: str, title: str,
              overview: str, poster_url: str, streaming_service: str,
              rating: float = None, genres: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO movies (session_id, external_id, title, overview, poster_url, streaming_service, rating, genres)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, external_id, title, overview, poster_url, streaming_service, rating, genres))
    conn.commit()
    conn.close()


def get_next_movie(session_id: str, user_name: str):
    """
    Returns the next movie in this session that `user_name` hasn't swiped on yet.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM movies
        WHERE session_id = ?
        AND id NOT IN (
            SELECT movie_id FROM swipes
            WHERE session_id = ? AND user_name = ?
        )
        LIMIT 1
    """, (session_id, session_id, user_name)).fetchone()
    conn.close()
    return dict(row) if row else None


def movie_count(session_id: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as count FROM movies WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    return row["count"]


# ---------- Swipe helpers ----------

def record_swipe(session_id: str, user_name: str, movie_id: int, direction: str):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO swipes (session_id, user_name, movie_id, direction)
        VALUES (?, ?, ?, ?)
    """, (session_id, user_name, movie_id, direction))
    conn.commit()
    conn.close()


def check_for_match(session_id: str, movie_id: int) -> bool:
    """
    A match happens when at least 2 *different* people have swiped
    'right' on the same movie in the same session.
    """
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(DISTINCT user_name) as right_swipers
        FROM swipes
        WHERE session_id = ? AND movie_id = ? AND direction = 'right'
    """, (session_id, movie_id)).fetchone()
    conn.close()
    return row["right_swipers"] >= 2


def get_matches(session_id: str):
    """
    Returns all movies in this session that have been swiped right
    by 2 or more distinct people.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT m.*, COUNT(DISTINCT s.user_name) as right_swipers
        FROM movies m
        JOIN swipes s ON s.movie_id = m.id
        WHERE m.session_id = ? AND s.direction = 'right'
        GROUP BY m.id
        HAVING right_swipers >= 2
    """, (session_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]
