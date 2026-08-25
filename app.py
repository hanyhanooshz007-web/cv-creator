"""
app.py
Main Streamlit entrypoint for the Resume Generator app.
Handles routing, authentication forms, sidebar layout, and state management.
"""

import streamlit as st

import auth
import database as db
from pdf_generator import generate_resume_pdf

st.set_page_config(page_title="Resume Generator", page_icon="📄", layout="wide")

db.init_db()


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_email": None,
        "view": "dashboard",        # "dashboard" or "editor"
        "editing_resume_id": None,  # None = creating a new resume
        "confirm_delete_id": None,  # id of resume pending delete confirmation
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ---------------------------------------------------------------------------
# Auth screens
# ---------------------------------------------------------------------------

def render_login_form():
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            success, message, user = auth.login_user(email, password)
            if success:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["user_email"] = user["email"]
                st.session_state["view"] = "dashboard"
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def render_register_form():
    with st.form("register_form"):
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input(
            "Confirm password", type="password", key="register_confirm_password"
        )
        submitted = st.form_submit_button("Register", use_container_width=True)

        if submitted:
            success, message = auth.register_user(email, password, confirm_password)
            if success:
                st.success(message)
            else:
                st.error(message)


def render_auth_screen():
    st.title("📄 Resume Generator")
    st.caption("Create, edit, and export polished resumes in minutes.")

    login_tab, register_tab = st.tabs(["Log in", "Register"])
    with login_tab:
        render_login_form()
    with register_tab:
        render_register_form()


# ---------------------------------------------------------------------------
# Sidebar (only shown when logged in)
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown(f"**Signed in as**  \n{st.session_state['user_email']}")
        st.divider()

        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state["view"] = "dashboard"
            st.session_state["editing_resume_id"] = None
            st.rerun()

        if st.button("✏️ Editor", use_container_width=True):
            st.session_state["view"] = "editor"
            st.rerun()

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            for key in ("logged_in", "user_id", "user_email", "view",
                        "editing_resume_id", "confirm_delete_id"):
                st.session_state[key] = None
            st.session_state["logged_in"] = False
            st.session_state["view"] = "dashboard"
            st.rerun()


# ---------------------------------------------------------------------------
# Dashboard view
# ---------------------------------------------------------------------------

def render_dashboard():
    st.title("Your resumes")

    if st.button("+ New resume"):
        st.session_state["editing_resume_id"] = None
        st.session_state["view"] = "editor"
        st.rerun()

    st.write("")

    resumes = db.get_resumes_for_user(st.session_state["user_id"])

    if not resumes:
        st.info("No resumes yet. Click New resume to create one.")
        return

    for resume in resumes:
        with st.container(border=True):
            col_info, col_edit, col_delete = st.columns([6, 1, 1])

            with col_info:
                display_name = resume["full_name"] or "Untitled"
                st.markdown(f"**{resume['title']}**")
                st.caption(f"{display_name}  ·  last updated {resume['updated_at']}")

            with col_edit:
                if st.button("Edit", key=f"edit_{resume['id']}", use_container_width=True):
                    st.session_state["editing_resume_id"] = resume["id"]
                    st.session_state["view"] = "editor"
                    st.rerun()

            with col_delete:
                if st.button("Delete", key=f"delete_{resume['id']}", use_container_width=True):
                    st.session_state["confirm_delete_id"] = resume["id"]
                    st.rerun()

            if st.session_state["confirm_delete_id"] == resume["id"]:
                st.warning(f"Delete '{resume['title']}'? This cannot be undone.")
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("Yes, delete", key=f"confirm_delete_{resume['id']}",
                                  use_container_width=True):
                        db.delete_resume(resume["id"])
                        st.session_state["confirm_delete_id"] = None
                        st.rerun()
                with cancel_col:
                    if st.button("Cancel", key=f"cancel_delete_{resume['id']}",
                                  use_container_width=True):
                        st.session_state["confirm_delete_id"] = None
                        st.rerun()


# ---------------------------------------------------------------------------
# Editor + live preview view
# ---------------------------------------------------------------------------

def build_preview_markdown(title, full_name, email, phone, location, summary, skills):
    lines = []
    lines.append(f"### {full_name.strip() if full_name.strip() else 'Your Name'}")

    contact_parts = [p for p in [email.strip(), phone.strip(), location.strip()] if p]
    if contact_parts:
        lines.append("  \n".join(["*" + " &nbsp;|&nbsp; ".join(contact_parts) + "*"]))

    lines.append("---")

    if summary.strip():
        lines.append("**Summary**")
        lines.append(summary.strip())
        lines.append("")

    if skills.strip():
        lines.append("**Skills**")
        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        if skill_list:
            lines.append("  \n".join(f"- {s}" for s in skill_list))
        else:
            lines.append(skills.strip())

    return "\n\n".join(lines)


def render_editor():
    if st.button("← Back to dashboard"):
        st.session_state["view"] = "dashboard"
        st.session_state["editing_resume_id"] = None
        st.rerun()

    resume_id = st.session_state["editing_resume_id"]
    existing = db.get_resume(resume_id) if resume_id else None

    if existing:
        st.subheader(f"Editing: {existing['title']}")
    else:
        st.subheader("New resume")

    left_col, right_col = st.columns(2)

    with left_col:
        title = st.text_input(
            "Resume title",
            value=existing["title"] if existing else "My CV",
            key="field_title",
        )

        st.markdown("#### Personal details")
        full_name = st.text_input(
            "Full name",
            value=existing["full_name"] if existing and existing["full_name"] else "",
            key="field_full_name",
        )
        email = st.text_input(
            "Email",
            value=existing["email"] if existing and existing["email"] else "",
            key="field_email",
        )
        phone = st.text_input(
            "Phone",
            value=existing["phone"] if existing and existing["phone"] else "",
            key="field_phone",
        )
        location = st.text_input(
            "Location",
            value=existing["location"] if existing and existing["location"] else "",
            key="field_location",
        )
        summary = st.text_area(
            "Summary",
            value=existing["summary"] if existing and existing["summary"] else "",
            height=120,
            key="field_summary",
        )

        st.markdown("#### Skills")
        skills = st.text_area(
            "Comma-separated skills",
            value=existing["skills"] if existing and existing["skills"] else "",
            height=80,
            key="field_skills",
            placeholder="Python, SQL, Project Management, Communication",
        )

        st.write("")
        if st.button("💾 Save", use_container_width=True):
            if not title.strip():
                st.error("Resume title cannot be empty.")
            else:
                if existing:
                    db.update_resume(
                        resume_id, title.strip(), full_name.strip(), email.strip(),
                        phone.strip(), location.strip(), summary.strip(), skills.strip(),
                    )
                    st.success("Resume updated.")
                else:
                    new_id = db.create_resume(
                        st.session_state["user_id"], title.strip(), full_name.strip(),
                        email.strip(), phone.strip(), location.strip(),
                        summary.strip(), skills.strip(),
                    )
                    st.session_state["editing_resume_id"] = new_id
                    st.success("Resume created.")
                st.rerun()

    with right_col:
        st.markdown("#### Live preview")
        with st.container(border=True):
            preview_md = build_preview_markdown(
                title, full_name, email, phone, location, summary, skills
            )
            st.markdown(preview_md, unsafe_allow_html=True)

    st.divider()

    if st.button("📄 Generate PDF"):
        if not full_name.strip():
            st.error("Please enter at least a full name before generating a PDF.")
        else:
            pdf_bytes = generate_resume_pdf(
                full_name, email, phone, location, summary, skills
            )
            file_name = f"{(full_name.strip() or 'resume').replace(' ', '_')}_resume.pdf"
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
            )


# ---------------------------------------------------------------------------
# Main router
# ---------------------------------------------------------------------------

def main():
    if not st.session_state["logged_in"]:
        render_auth_screen()
        return

    render_sidebar()

    if st.session_state["view"] == "editor":
        render_editor()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
