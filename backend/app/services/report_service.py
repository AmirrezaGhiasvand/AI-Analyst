"""
PDF report generation.

Compiles the current chat session (already-computed, already-grounded
Q&A pairs and charts) into a polished PDF: title page with dataset
overview, a short AI-written executive summary, then each question,
its real answer, and its chart (if one was generated).

Supports Persian/Arabic text correctly via a bundled Unicode font
(Vazirmatn) plus reshaping/bidi-reordering — see rtl_text.py for why
both steps are necessary.

Charts are stored as library-agnostic ChartSpec JSON (see schemas/chart.py)
— this module is where that generic spec gets converted into an actual
Plotly figure for static PNG export via kaleido. Plotly is purely an
internal PDF-rendering detail; the frontend never sees it. A dark theme
is applied ONLY here, for the PDF — the interactive chat charts stay
theme-agnostic so the frontend's own charting library controls their look.
"""

import io
import json
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak,
)
from sqlalchemy.orm import Session

from app.models.dataset import Dataset
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.project import Project
from app.services.llm_client import get_llm_client
from app.services.rtl_text import contains_rtl, prepare_rtl_text

_FONT_REGISTERED = False

# A curated dark palette for PDF charts — deliberately not just Plotly's
# stock "plotly_dark" template, which is fine but generic. Colors chosen
# for contrast and readability on a dark background.
_DARK_COLORWAY = [
    "#4FD1C5", "#F6AD55", "#FC8181", "#B794F4", "#63B3ED", "#F6E05E",
]
_DARK_BG = "#1A202C"
_DARK_GRID = "#2D3748"
_DARK_TEXT = "#E2E8F0"


def _ensure_fonts_registered():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    pdfmetrics.registerFont(TTFont("Vazirmatn", "app/assets/fonts/Vazirmatn-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Vazirmatn-Bold", "app/assets/fonts/Vazirmatn-Bold.ttf"))
    pdfmetrics.registerFontFamily(
        "Vazirmatn", normal="Vazirmatn", bold="Vazirmatn-Bold",
        italic="Vazirmatn", boldItalic="Vazirmatn-Bold",
    )
    _FONT_REGISTERED = True


def _prepare_paragraph_text(text: str) -> str:
    escaped = escape(text)
    return prepare_rtl_text(escaped)


def _prepare_list(items: list[str]) -> str:
    return ", ".join(prepare_rtl_text(escape(item)) for item in items)


def _paragraph_style(is_rtl: bool, base_style: ParagraphStyle, bold: bool = False) -> ParagraphStyle:
    if not is_rtl:
        return base_style
    return ParagraphStyle(
        f"{base_style.name}-RTL",
        parent=base_style,
        fontName="Vazirmatn-Bold" if bold else "Vazirmatn",
        alignment=TA_RIGHT,
    )


def _build_dark_figure(chart_spec: dict) -> go.Figure:
    """
    Converts a library-agnostic ChartSpec dict into an actual Plotly
    figure, styled with a dark theme. This is the ONLY place Plotly
    exists in the app now — purely an internal PDF-rendering detail.
    """
    chart_type = chart_spec["chart_type"]
    x_key = chart_spec["x_key"]
    series_keys = chart_spec["series_keys"]
    data = chart_spec["data"]
    title = chart_spec.get("title", "")

    x_values = [row.get(x_key) for row in data]
    traces = []

    if chart_type == "pie":
        values = [row.get(series_keys[0]) for row in data]
        traces.append(go.Pie(labels=x_values, values=values, marker=dict(colors=_DARK_COLORWAY)))
    elif chart_type == "scatter":
        y_values = [row.get(series_keys[0]) for row in data]
        traces.append(go.Scatter(x=x_values, y=y_values, mode="markers",
                                  marker=dict(color=_DARK_COLORWAY[0], size=9)))
    elif chart_type in ("line", "area"):
        for i, key in enumerate(series_keys):
            y_values = [row.get(key) for row in data]
            fill = "tozeroy" if chart_type == "area" else None
            traces.append(go.Scatter(x=x_values, y=y_values, mode="lines+markers", name=key,
                                      line=dict(color=_DARK_COLORWAY[i % len(_DARK_COLORWAY)]), fill=fill))
    else:  # bar, histogram, grouped bar — all render as bar traces
        for i, key in enumerate(series_keys):
            y_values = [row.get(key) for row in data]
            traces.append(go.Bar(x=x_values, y=y_values, name=key,
                                  marker=dict(color=_DARK_COLORWAY[i % len(_DARK_COLORWAY)])))

    figure = go.Figure(data=traces)
    figure.update_layout(
        title=dict(text=title, font=dict(color=_DARK_TEXT, size=18)),
        paper_bgcolor=_DARK_BG,
        plot_bgcolor=_DARK_BG,
        font=dict(color=_DARK_TEXT),
        xaxis=dict(gridcolor=_DARK_GRID, title=chart_spec.get("x_label")),
        yaxis=dict(gridcolor=_DARK_GRID, title=chart_spec.get("y_label")),
        legend=dict(font=dict(color=_DARK_TEXT)),
        margin=dict(t=60, b=40, l=50, r=30),
    )
    return figure


def _render_chart_image(chart_json: str) -> bytes | None:
    """Converts a stored ChartSpec JSON string into a static dark-themed
    PNG for embedding in the PDF. Returns None on failure — charting is
    an enhancement; a rendering bug shouldn't break the whole report."""
    try:
        chart_spec = json.loads(chart_json)
        figure = _build_dark_figure(chart_spec)
        return figure.to_image(format="png", width=900, height=500, scale=2)
    except Exception:
        return None


def _generate_executive_summary(client, qa_pairs: list[tuple[str, str]]) -> str:
    if not qa_pairs:
        return "No questions have been asked in this session yet."

    transcript = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in qa_pairs)
    messages = [
        {
            "role": "system",
            "content": (
                "Summarize the following data analysis session in 3-5 sentences. "
                "Base the summary strictly on what's in the transcript below — "
                "do not introduce any numbers or claims not already present in it. "
                "Write plain prose, no markdown formatting."
            ),
        },
        {"role": "user", "content": transcript},
    ]
    try:
        return client.chat(messages, temperature=0.3)
    except Exception:
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

    conversation = db.query(Conversation).filter(Conversation.project_id == project_id).first()
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
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"{project.name} - Analysis Report")
    story = []

    # --- Title page ---
    story.append(
        Paragraph(_prepare_paragraph_text(project.name), _paragraph_style(contains_rtl(project.name), styles["Title"]))
    )
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated {datetime.now(timezone.utc).strftime('%B %d, %Y')}", styles["Normal"]))
    story.append(Spacer(1, 24))

    story.append(Paragraph("Datasets", styles["Heading2"]))
    for ds in datasets:
        profile = json.loads(ds.profile_json) if ds.profile_json else {}
        column_names = list(profile.get("columns", {}).keys())
        name_text = _prepare_paragraph_text(ds.original_filename)
        story.append(
            Paragraph(
                f"<b>{name_text}</b> — {ds.row_count} rows, {ds.column_count} columns",
                _paragraph_style(contains_rtl(ds.original_filename), styles["Normal"]),
            )
        )
        if column_names:
            columns_text = _prepare_list(column_names)
            columns_is_rtl = any(contains_rtl(c) for c in column_names)
            story.append(
                Paragraph(f"Columns: {columns_text}", _paragraph_style(columns_is_rtl, styles["Normal"]))
            )
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    client = get_llm_client()
    summary_text = _generate_executive_summary(client, [(q, a.content) for q, a in qa_pairs])
    story.append(
        Paragraph(_prepare_paragraph_text(summary_text), _paragraph_style(contains_rtl(summary_text), styles["Normal"]))
    )
    story.append(PageBreak())

    # --- Q&A sections ---
    story.append(Paragraph("Analysis Detail", styles["Heading1"]))
    story.append(Spacer(1, 12))

    for question, answer_message in qa_pairs:
        story.append(
            Paragraph(
                _prepare_paragraph_text(question),
                _paragraph_style(contains_rtl(question), styles["Heading3"], bold=True),
            )
        )
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                _prepare_paragraph_text(answer_message.content),
                _paragraph_style(contains_rtl(answer_message.content), styles["Normal"]),
            )
        )

        if answer_message.chart_json:
            image_bytes = _render_chart_image(answer_message.chart_json)
            if image_bytes:
                story.append(Spacer(1, 8))
                story.append(RLImage(io.BytesIO(image_bytes), width=6 * inch, height=3.33 * inch))

        story.append(Spacer(1, 16))

    doc.build(story)
    return buffer.getvalue()