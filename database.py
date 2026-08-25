"""
database.py
Database initialization, connection management, and CRUD helper functions
for the Streamlit Resume Generator app.
"""

import sqlite3
from contextlib import contextmanager

DB_NAME = "resumes.db"


@contextmanager
def get_connection():
    """
    Context manager that yields a SQLite connection with foreign keys enabled
    and row_factory set to sqlite3.Row for dict-like access to columns.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """
    Creates the users and resumes tables if they do not already exist.
    Should be called once at app startup.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT DEFAULT 'My CV',
                full_name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                summary TEXT,
                skills TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )


# ---------------------------------------------------------------------------
# User CRUD helpers
# ---------------------------------------------------------------------------

def create_user(email: str, password_hash: str) -> int:
    """
    Inserts a new user record. Returns the new user's id.
    Raises sqlite3.IntegrityError if the email is already registered.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, password_hash),
        )
        return cursor.lastrowid


def get_user_by_email(email: str):
    """
    Returns the user row (sqlite3.Row) matching the given email, or None.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()


def email_exists(email: str) -> bool:
    """
    Returns True if a user with the given email already exists.
    """
    return get_user_by_email(email) is not None


# ---------------------------------------------------------------------------
# Resume CRUD helpers
# ---------------------------------------------------------------------------

def create_resume(user_id: int, title: str, full_name: str, email: str,
                   phone: str, location: str, summary: str, skills: str) -> int:
    """
    Inserts a new resume record for the given user. Returns the new resume's id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO resumes
                (user_id, title, full_name, email, phone, location, summary, skills, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, title, full_name, email, phone, location, summary, skills),
        )
        return cursor.lastrowid


def update_resume(resume_id: int, title: str, full_name: str, email: str,
                   phone: str, location: str, summary: str, skills: str) -> None:
    """
    Updates an existing resume record and refreshes its updated_at timestamp.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE resumes
            SET title = ?, full_name = ?, email = ?, phone = ?, location = ?,
                summary = ?, skills = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, full_name, email, phone, location, summary, skills, resume_id),
        )


def delete_resume(resume_id: int) -> None:
    """
    Deletes the resume with the given id.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))


def get_resume(resume_id: int):
    """
    Returns a single resume row (sqlite3.Row) by id, or None.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        return cursor.fetchone()


def get_resumes_for_user(user_id: int):
    """
    Returns a list of all resumes belonging to a user, most recently
    updated first.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM resumes WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        )
        return cursor.fetchall()
