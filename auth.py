"""
auth.py
Password hashing (SHA-256 with per-user salt), input validation, and
login / registration logic for the Streamlit Resume Generator app.
"""

import hashlib
import re
import secrets

import database as db

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6


def is_valid_email(email: str) -> bool:
    """
    Returns True if the given string looks like a valid email address.
    """
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_password(password: str) -> bool:
    """
    Returns True if the password meets the minimum length requirement.
    """
    return bool(password) and len(password) >= MIN_PASSWORD_LENGTH


def hash_password(password: str, salt: str = None) -> str:
    """
    Hashes a password using SHA-256 with a random salt (generated if not
    supplied). The salt is stored alongside the hash in the format
    'salt$hash' so it can be verified later without a separate column.
    """
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifies a plaintext password against a stored 'salt$hash' string.
    """
    try:
        salt, _ = stored_hash.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, salt) == stored_hash


def register_user(email: str, password: str, confirm_password: str):
    """
    Validates registration input and creates a new user if valid.

    Returns a tuple (success: bool, message: str).
    """
    email = email.strip().lower()

    if not is_valid_email(email):
        return False, "Please enter a valid email address."

    if not is_valid_password(password):
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if password != confirm_password:
        return False, "Passwords do not match."

    if db.email_exists(email):
        return False, "An account with this email already exists."

    password_hash = hash_password(password)

    try:
        db.create_user(email, password_hash)
    except Exception as exc:  # covers sqlite3.IntegrityError and others
        return False, f"Could not create account: {exc}"

    return True, "Account created successfully. You can now log in."


def login_user(email: str, password: str):
    """
    Validates login credentials against the database.

    Returns a tuple (success: bool, message: str, user_row_or_None).
    """
    email = email.strip().lower()

    if not email or not password:
        return False, "Please enter both email and password.", None

    user = db.get_user_by_email(email)

    if user is None:
        return False, "No account found with this email.", None

    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password.", None

    return True, "Logged in successfully.", user
