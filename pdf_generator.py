"""
pdf_generator.py
Generates a clean, single-page resume PDF from resume field data using fpdf2.
"""

from fpdf import FPDF


class ResumePDF(FPDF):
    """
    A simple FPDF subclass with a consistent footer for the resume document.
    """

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _clean_text(text: str) -> str:
    """
    Replaces characters that fpdf2's core Helvetica font (latin-1) cannot
    encode, so PDF generation never raises an encoding error.
    """
    if not text:
        return ""
    replacements = {
        "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...",
        "\u2022": "-",
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_resume_pdf(full_name: str, email: str, phone: str, location: str,
                         summary: str, skills: str) -> bytes:
    """
    Builds a formatted resume PDF from the supplied fields and returns the
    raw PDF bytes, suitable for use with st.download_button.
    """
    full_name = _clean_text(full_name) or "Untitled Resume"
    email = _clean_text(email)
    phone = _clean_text(phone)
    location = _clean_text(location)
    summary = _clean_text(summary)
    skills = _clean_text(skills)

    pdf = ResumePDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(left=18, top=18, right=18)

    # --- Name header ---
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 12, full_name, new_x="LMARGIN", new_y="NEXT")

    # --- Contact line ---
    contact_parts = [part for part in [email, phone, location] if part]
    contact_line = "   |   ".join(contact_parts)
    if contact_line:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(90, 90, 90)
        pdf.cell(0, 8, contact_line, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.4)
    pdf.line(18, pdf.get_y(), pdf.w - 18, pdf.get_y())
    pdf.ln(6)

    # --- Summary section ---
    if summary:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 8, "Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6.5, summary)
        pdf.ln(4)

    # --- Skills section ---
    if skills:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 8, "Skills", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)

        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
        skills_line = "   -   ".join(skill_list) if skill_list else skills
        pdf.multi_cell(0, 6.5, skills_line)
        pdf.ln(2)

    output = pdf.output()
    return bytes(output)
