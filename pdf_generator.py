"""
PDF generator using ReportLab + matplotlib for math rendering.
Produces a nicely formatted step-by-step solution PDF.
"""

import io
import re
import logging
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.mathtext as mathtext
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    HRFlowable, Table, TableStyle,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Colours ──────────────────────────────────────────────────────────────────
DARK_BG    = colors.HexColor("#1A1A2E")
ACCENT     = colors.HexColor("#E94560")
LIGHT_TEXT = colors.HexColor("#EAEAEA")
STEP_BG    = colors.HexColor("#16213E")
CODE_BG    = colors.HexColor("#0F3460")
WHITE      = colors.white
GOLD       = colors.HexColor("#F5A623")


def latex_to_image(latex_expr: str, fontsize: int = 14) -> bytes | None:
    """Render a LaTeX expression to PNG bytes via matplotlib."""
    try:
        # wrap bare expressions
        if not latex_expr.strip().startswith("$"):
            latex_expr = f"${latex_expr}$"

        fig, ax = plt.subplots(figsize=(6, 0.6))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        ax.axis("off")
        ax.text(
            0.05, 0.5, latex_expr,
            fontsize=fontsize,
            va="center", ha="left",
            usetex=False,       # use matplotlib mathtext (no LaTeX install needed)
            transform=ax.transAxes,
        )
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                    facecolor="white", pad_inches=0.05)
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        logger.warning("latex_to_image failed for %r: %s", latex_expr[:40], e)
        return None


def parse_markdown_to_stories(text: str, styles: dict) -> list:
    """Convert markdown-ish text + LaTeX to ReportLab flowables."""
    flowables = []
    lines = text.split("\n")
    step_num = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # ── Blank line ────────────────────────────────────────────────────
        if not line:
            flowables.append(Spacer(1, 0.2 * cm))
            i += 1
            continue

        # ── Numbered step heading (1. / Step 1) ──────────────────────────
        step_match = re.match(r"^(\*\*)?(?:Step\s+)?(\d+)[.)]\s*(.+?)(\*\*)?$", line, re.I)
        if step_match:
            step_num += 1
            heading = step_match.group(3).strip("*").strip()
            flowables.append(Spacer(1, 0.3 * cm))
            flowables.append(Paragraph(
                f'<font color="#F5A623">●</font> <b>Step {step_num}: {heading}</b>',
                styles["step_heading"],
            ))
            i += 1
            continue

        # ── Bold heading (## or **text**) ─────────────────────────────────
        if line.startswith("## ") or line.startswith("### "):
            heading = re.sub(r"^#+\s*", "", line)
            flowables.append(Spacer(1, 0.2 * cm))
            flowables.append(Paragraph(f"<b>{heading}</b>", styles["section"]))
            i += 1
            continue

        # ── Display math block  \[ ... \] or $$ ... $$ ────────────────────
        display_start = re.match(r"^\\\[$|^\$\$$", line)
        if display_start:
            math_lines = []
            i += 1
            while i < len(lines):
                end_line = lines[i].strip()
                if re.match(r"^\\\]$|^\$\$$", end_line):
                    i += 1
                    break
                math_lines.append(end_line)
                i += 1
            expr = " ".join(math_lines)
            img_bytes = latex_to_image(expr, fontsize=16)
            if img_bytes:
                flowables.append(Spacer(1, 0.2 * cm))
                flowables.append(RLImage(io.BytesIO(img_bytes), width=12 * cm, height=1.2 * cm))
                flowables.append(Spacer(1, 0.2 * cm))
            else:
                flowables.append(Paragraph(f"<code>{expr}</code>", styles["math_fallback"]))
            continue

        # ── Inline math  \( ... \) or $ ... $ ────────────────────────────
        # Extract and render each inline expression
        processed = _render_inline_math(line, styles, flowables)
        if not processed:
            # Plain paragraph
            clean = _md_to_rl(line)
            flowables.append(Paragraph(clean, styles["body"]))

        i += 1

    return flowables


def _render_inline_math(line: str, styles: dict, flowables: list) -> bool:
    """If line contains inline math, split and add mixed flowables. Returns True if handled."""
    pattern = r"\\\((.+?)\\\)|\$([^$]+?)\$"
    parts = re.split(pattern, line)
    if len(parts) == 1:
        return False  # no math found

    # Build a row: text + inline math images
    para_parts = []
    for idx, part in enumerate(parts):
        if part is None:
            continue
        # Every 3rd/4th group is a math capture group
        if idx % 3 == 1 or idx % 3 == 2:
            if part:
                img_bytes = latex_to_image(part, fontsize=13)
                if img_bytes:
                    para_parts.append(("img", img_bytes))
                else:
                    para_parts.append(("text", f"[{part}]"))
        else:
            if part.strip():
                para_parts.append(("text", _md_to_rl(part)))

    # Render as separate paragraph (images inline not trivial in ReportLab — use image rows)
    for kind, content in para_parts:
        if kind == "text":
            flowables.append(Paragraph(content, styles["body"]))
        else:
            flowables.append(RLImage(io.BytesIO(content), width=8 * cm, height=0.7 * cm))
    return True


def _md_to_rl(text: str) -> str:
    """Convert simple markdown bold/italic to ReportLab XML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`",       r"<code>\1</code>", text)
    # escape raw & < > not inside tags
    # (simplified — good enough for typical LLM output)
    return text


def generate_pdf_solution(question: str, answer: str) -> bytes:
    """Generate a full PDF with question + step-by-step answer."""
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title",
            parent=base_styles["Title"],
            fontSize=22,
            textColor=ACCENT,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base_styles["Normal"],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=20,
            alignment=TA_CENTER,
        ),
        "question_label": ParagraphStyle(
            "question_label",
            parent=base_styles["Normal"],
            fontSize=11,
            textColor=GOLD,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        ),
        "question": ParagraphStyle(
            "question",
            parent=base_styles["Normal"],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=16,
            leftIndent=10,
            borderPad=6,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base_styles["Normal"],
            fontSize=13,
            textColor=ACCENT,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=6,
        ),
        "step_heading": ParagraphStyle(
            "step_heading",
            parent=base_styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#2C3E50"),
            fontName="Helvetica-Bold",
            spaceBefore=8,
            spaceAfter=4,
            leftIndent=8,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base_styles["Normal"],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=4,
            leftIndent=16,
            leading=16,
        ),
        "math_fallback": ParagraphStyle(
            "math_fallback",
            parent=base_styles["Code"],
            fontSize=11,
            textColor=colors.HexColor("#1A5276"),
            spaceAfter=6,
            leftIndent=20,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base_styles["Normal"],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        ),
    }

    story = []

    # ── Header ────────────────────────────────────────────────────────────
    story.append(Paragraph("EduBot AI — Step-by-Step Solution", styles["title"]))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}  |  Powered by Llama 4 Scout",
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=12))

    # ── Question ──────────────────────────────────────────────────────────
    story.append(Paragraph("📌 Question:", styles["question_label"]))
    story.append(Paragraph(_md_to_rl(question[:500]), styles["question"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=10))

    # ── Solution ──────────────────────────────────────────────────────────
    story.append(Paragraph("📐 Solution:", styles["section"]))
    story.append(Spacer(1, 0.3 * cm))
    story.extend(parse_markdown_to_stories(answer, styles))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph(
        "EduBot AI • Bas padhai karo! 📚 • Powered by Groq + Llama 4 Scout",
        styles["footer"],
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
