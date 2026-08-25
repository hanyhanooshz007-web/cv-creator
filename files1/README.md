# Resume Generator (Streamlit)

A multi-user resume builder with login/registration, a dashboard of saved
resumes, a live-preview editor, and one-click PDF export.

## Files

| File               | Purpose                                              |
|--------------------|-------------------------------------------------------|
| `app.py`           | Streamlit entrypoint — routing, forms, sidebar        |
| `database.py`      | SQLite schema + CRUD helpers                          |
| `auth.py`          | Password hashing (SHA-256 + salt) and login/register  |
| `pdf_generator.py` | Builds the downloadable PDF with fpdf2                |
| `requirements.txt` | Python dependencies                                    |

## Run it locally

```bash
# 1. (Recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) — open
it in your browser. `resumes.db` is created automatically in the same
folder on first run.

## Deploy it as a public website (free, no server management)

**Streamlit Community Cloud** is the fastest path to a real public URL:

1. Push this folder to a **GitHub repository** (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, pick the repo/branch, and set the main file to `app.py`.
4. Click **Deploy**. You'll get a live URL like
   `https://your-app-name.streamlit.app`.

Notes for this deployment path:
- SQLite (`resumes.db`) lives on the container's local disk, which is
  **ephemeral** on Community Cloud — data can be wiped on redeploys or
  restarts. Fine for a demo; for a persistent production app, swap
  `database.py` to a hosted database (e.g. Postgres via `psycopg2` or
  Supabase) — the CRUD function signatures in `database.py` are written
  so the rest of the app doesn't need to change if you do this.
- No secrets or API keys are required for this app as written.

### Other hosting options
- **Docker**: `pip install -r requirements.txt` inside a Python base
  image, `EXPOSE 8501`, `CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]`,
  then deploy the container to Render, Railway, Fly.io, or any VPS.
- **Hugging Face Spaces**: create a Space with the "Streamlit" SDK and
  push these same files.

## Default behavior

- First run creates `resumes.db` with `users` and `resumes` tables.
- Passwords are never stored in plaintext — SHA-256 hashed with a
  per-user random salt.
- Each user only sees and edits their own resumes.
