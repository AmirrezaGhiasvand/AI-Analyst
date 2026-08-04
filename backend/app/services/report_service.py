"""
PDF report generation.

Compiles the current chat session (already-computed, already-grounded
Q&A pairs and charts) into a polished PDF: title page with dataset
overview, a short AI-written executive summary, then each question,
its real answer, and its chart (if one was generated).

Supports Persian/Arabic text correctly via a bundled Unicode font
(Vazirmatn) plus reshaping/bidi-reordering — see rtl_text.py for why
both steps are necessary.
"""

import io
import json
from datetime import datetime, timezone
from typing import cast
from xml.sax.saxutils import escape

import plotly.io as pio
from app.models.conversation import Conversation
from app.models.dataset import Dataset
from app.models.message import Message
from app.models.project import Project
from app.services.llm_client import get_llm_client
from app.services.rtl_text import contains_rtl, prepare_rtl_text
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
)
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from sqlalchemy.orm import Session

_FONT_REGISTERED = False


def _ensure_fonts_registered():
    """Registers the Persian font once per process. Idempotent — safe to
    call on every report generation without re-registering repeatedly."""
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    pdfmetrics.registerFont(
        TTFont("Vazirmatn", "app/assets/fonts/Vazirmatn-Regular.ttf")
    )
    pdfmetrics.registerFont(
        TTFont("Vazirmatn-Bold", "app/assets/fonts/Vazirmatn-Bold.ttf")
    )
    # Links regular/bold together under one family name so that <b> tags
    # inside Paragraph text automatically pick the bold Persian font
    # instead of falling back to a font with no Persian glyphs.
    pdfmetrics.registerFontFamily(
        "Vazirmatn",
        normal="Vazirmatn",
        bold="Vazirmatn-Bold",
        italic="Vazirmatn",
        boldItalic="Vazirmatn-Bold",
    )
    _FONT_REGISTERED = True


def _prepare_paragraph_text(text: str) -> str:
    """Escapes XML-sensitive characters (ReportLab Paragraphs interpret
    a small XML-like markup), then applies RTL shaping if needed."""
    escaped = escape(text)
    return prepare_rtl_text(escaped)


def _prepare_list(items: list[str]) -> str:
    """Reshapes each item individually before joining — safer than
    reshaping one long joined string, which could reorder the separators
    and item boundaries in confusing ways for mixed-language lists."""
    return ", ".join(prepare_rtl_text(escape(item)) for item in items)


def _paragraph_style(
    is_rtl: bool, base_style: ParagraphStyle, bold: bool = False
) -> ParagraphStyle:
    """Returns a style using the Persian font + right alignment if
    is_rtl, otherwise the given base style unchanged."""
    if not is_rtl:
        return base_style
    return ParagraphStyle(
        f"{base_style.name}-RTL",
        parent=base_style,
        fontName="Vazirmatn-Bold" if bold else "Vazirmatn",
        alignment=TA_RIGHT,
    )


def _render_chart_image(chart_json: str) -> bytes | None:
    """Converts a stored Plotly figure JSON into a static PNG for
    embedding in the PDF, using kaleido. Returns None on failure —
    charting is an enhancement; a rendering bug shouldn't break the
    whole report."""
    try:
        figure = pio.from_json(chart_json)
        return figure.to_image(format="png", width=900, height=500, scale=2)
    except Exception:
        return None


def _generate_executive_summary(client, qa_pairs: list[tuple[str, str]]) -> str:
    """One LLM call summarizing the session. Grounded by construction —
    it can only summarize what was actually asked/answered, not invent
    new figures, since only the existing Q&A text is given as input."""
    if not qa_pairs:
        return "No questions have been asked in this session yet."

    transcript = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in qa_pairs)
    messages = [
        {
            "role": "system",
            "content": (
                "Summarize the following data analysis session in 3-5 sentences. "
                "Base the summary strictly on what's in the transcript below — "
                "do not introduce any numbers or claims not already present in it."
            ),
        },
        {"role": "user", "content": transcript},
    ]
    try:
        return client.chat(messages, temperature=0.3)
    except Exception:
        # Fallback if the LLM call fails — the report can still be
        # generated without an AI-written summary, just without one.
        return "Executive summary unavailable."


def generate_report_pdf(db: Session, project_id: str) -> bytes:
    _ensure_fonts_registered()

    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise ValueError(f"Project '{project_id}' not found.")

    datasets = (
        db.query(Dataset)
        .filter(Dataset.project_id == project_id, Dataset.status == "ready")
        .all()
    )

    conversation = (
        db.query(Conversation).filter(Conversation.project_id == project_id).first()
    )
    messages = []
    if conversation:
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
            .all()
        )

    qa_pairs: list[tuple[str, Message]] = []
    pending_question = None
    for m in messages:
        if m.role == "user":
            pending_question = m.content
        elif m.role == "assistant" and pending_question is not None:
            qa_pairs.append((pending_question, m))
            pending_question = None

    styles = getSampleStyleSheet()
    title_style = cast(ParagraphStyle, styles["Title"])
    normal_style = cast(ParagraphStyle, styles["Normal"])
    heading1_style = cast(ParagraphStyle, styles["Heading1"])
    heading2_style = cast(ParagraphStyle, styles["Heading2"])
    heading3_style = cast(ParagraphStyle, styles["Heading3"])
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, title=f"{project.name} - Analysis Report"
    )
    story = []

    # --- Title page ---
    story.append(
        Paragraph(
            _prepare_paragraph_text(project.name),
            _paragraph_style(contains_rtl(project.name), title_style),
        )
    )
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            f"Generated {datetime.now(timezone.utc).strftime('%B %d, %Y')}",
            normal_style,
        )
    )
    story.append(Spacer(1, 24))

    story.append(Paragraph("Datasets", heading2_style))
    for ds in datasets:
        profile = json.loads(ds.profile_json) if ds.profile_json else {}
        column_names = list(profile.get("columns", {}).keys())
        name_text = _prepare_paragraph_text(ds.original_filename)
        story.append(
            Paragraph(
                f"<b>{name_text}</b> — {ds.row_count} rows, {ds.column_count} columns",
                _paragraph_style(contains_rtl(ds.original_filename), normal_style),
            )
        )
        if column_names:
            columns_text = _prepare_list(column_names)
            columns_is_rtl = any(contains_rtl(c) for c in column_names)
            story.append(
                Paragraph(
                    f"Columns: {columns_text}",
                    _paragraph_style(columns_is_rtl, normal_style),
                )
            )
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Executive Summary", heading2_style))
    client = get_llm_client()
    summary_text = _generate_executive_summary(
        client, [(q, a.content) for q, a in qa_pairs]
    )
    story.append(
        Paragraph(
            _prepare_paragraph_text(summary_text),
            _paragraph_style(contains_rtl(summary_text), normal_style),
        )
    )
    story.append(PageBreak())

    # --- Q&A sections ---
    story.append(Paragraph("Analysis Detail", heading1_style))
    story.append(Spacer(1, 12))

    for question, answer_message in qa_pairs:
        story.append(
            Paragraph(
                _prepare_paragraph_text(question),
                _paragraph_style(contains_rtl(question), heading3_style, bold=True),
            )
        )
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                _prepare_paragraph_text(answer_message.content),
                _paragraph_style(contains_rtl(answer_message.content), normal_style),
            )
        )

        if answer_message.chart_json:
            image_bytes = _render_chart_image(answer_message.chart_json)
            if image_bytes:
                story.append(Spacer(1, 8))
                story.append(
                    RLImage(io.BytesIO(image_bytes), width=6 * inch, height=3.33 * inch)
                )

        story.append(Spacer(1, 16))

    doc.build(story)
    return buffer.getvalue()
