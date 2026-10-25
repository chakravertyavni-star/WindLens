"""Generate docs/PROJECT_REPORT.pdf from docs/PROJECT_REPORT.md.

The Markdown file is the source of truth. Native ReportLab drawings are inserted
at <!-- DIAGRAM: ... --> markers so the PDF always contains readable diagrams
even when Mermaid cannot be rendered to an image.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_PATH = ROOT / "docs" / "PROJECT_REPORT.md"
PDF_PATH = ROOT / "docs" / "PROJECT_REPORT.pdf"

NAVY = colors.HexColor("#0B1F3A")
TEAL = colors.HexColor("#0E7C7B")
GOLD = colors.HexColor("#C4A35A")
INK = colors.HexColor("#1C2434")
MUTED = colors.HexColor("#5C6B7A")
LIGHT = colors.HexColor("#F4F7FB")
SOFT = colors.HexColor("#E6EEF5")
WHITE = colors.white
RULE = colors.HexColor("#C5D0DB")


class Diagram(Flowable):
    """Fixed-height architecture drawing used when Mermaid images are unavailable."""

    def __init__(self, kind: str, width: float):
        super().__init__()
        self.kind = kind
        self.width = width
        self.height = {
            "business": 92,
            "architecture": 210,
            "selection": 210,
            "processing": 230,
            "deployment": 92,
            "frontend": 120,
        }[kind]

    def draw(self) -> None:
        self.canv.setFillColor(LIGHT)
        self.canv.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        if self.kind == "business":
            self._boxes_row(
                [
                    "Elexon data",
                    "Decision cutoff",
                    "Latest eligible forecast",
                    "Match actuals",
                    "Metrics and advice",
                ]
            )
        elif self.kind == "architecture":
            self._boxes_column(
                [
                    "Browser / future React frontend",
                    "Future FastAPI JSON API",
                    "Processing: clean, select, match, score",
                    "Elexon client or validated snapshot",
                    "FUELHH actuals and WINDFOR forecasts",
                ]
            )
        elif self.kind == "selection":
            self._boxes_column(
                [
                    "Delivery period startTime",
                    "Compute configurable cutoff",
                    "Keep publishTime <= cutoff",
                    "Choose latest remaining forecast",
                    "Match actual and compute forecast - actual",
                ]
            )
        elif self.kind == "processing":
            self._boxes_column(
                [
                    "Ingest documented API extracts",
                    "Filter WIND and January 2026",
                    "Validate fields and timestamps",
                    "Select as-of forecast",
                    "Match, report coverage, calculate metrics",
                ]
            )
        elif self.kind == "frontend":
            self._boxes_row(
                [
                    "React WindLens",
                    "windApi.js fetch",
                    "FastAPI /api/metrics /api/series",
                    "Charts and KPIs",
                ]
            )
        else:
            self._boxes_row(
                [
                    "Browser",
                    "Deployed frontend",
                    "Deployed backend",
                    "Elexon or snapshot",
                ]
            )

    def _boxes_row(self, labels: list[str]) -> None:
        pad = 10
        gap = 8
        box_h = 42
        box_w = (self.width - 2 * pad - gap * (len(labels) - 1)) / len(labels)
        y = (self.height - box_h) / 2
        for index, label in enumerate(labels):
            x = pad + index * (box_w + gap)
            self._box(x, y, box_w, box_h, label)
            if index < len(labels) - 1:
                self._arrow_right(x + box_w, y + box_h / 2, gap)

    def _boxes_column(self, labels: list[str]) -> None:
        pad = 16
        gap = 10
        box_h = 28
        box_w = self.width - 2 * pad
        total = len(labels) * box_h + (len(labels) - 1) * gap
        y0 = (self.height - total) / 2
        for index, label in enumerate(labels):
            y = self.height - y0 - (index + 1) * box_h - index * gap
            self._box(pad, y, box_w, box_h, label)
            if index < len(labels) - 1:
                self._arrow_down(pad + box_w / 2, y, gap)

    def _box(self, x: float, y: float, w: float, h: float, text: str) -> None:
        self.canv.setFillColor(WHITE)
        self.canv.setStrokeColor(TEAL)
        self.canv.setLineWidth(1.2)
        self.canv.roundRect(x, y, w, h, 5, fill=1, stroke=1)
        self.canv.setFillColor(NAVY)
        self.canv.setFont("Helvetica-Bold", 8)
        self._wrapped_text(text, x + 6, y + h / 2, w - 12)

    def _wrapped_text(self, text: str, x: float, y: float, max_width: float) -> None:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if self.canv.stringWidth(trial, "Helvetica-Bold", 8) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        start = y + 4 * (len(lines) - 1)
        for offset, line in enumerate(lines[:3]):
            self.canv.drawCentredString(x + max_width / 2, start - offset * 9, line)

    def _arrow_right(self, x: float, y: float, gap: float) -> None:
        self.canv.setStrokeColor(GOLD)
        self.canv.setFillColor(GOLD)
        self.canv.setLineWidth(1.4)
        self.canv.line(x + 1, y, x + gap - 6, y)
        path = self.canv.beginPath()
        path.moveTo(x + gap - 6, y - 3)
        path.lineTo(x + gap - 1, y)
        path.lineTo(x + gap - 6, y + 3)
        path.close()
        self.canv.drawPath(path, fill=1, stroke=0)

    def _arrow_down(self, x: float, y: float, gap: float) -> None:
        self.canv.setStrokeColor(GOLD)
        self.canv.setFillColor(GOLD)
        self.canv.setLineWidth(1.4)
        self.canv.line(x, y, x, y - gap + 6)
        path = self.canv.beginPath()
        path.moveTo(x - 3, y - gap + 6)
        path.lineTo(x, y - gap + 1)
        path.lineTo(x + 3, y - gap + 6)
        path.close()
        self.canv.drawPath(path, fill=1, stroke=0)


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=13,
            leading=17,
            textColor=TEAL,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            textColor=INK,
            leftIndent=12,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            textColor=INK,
            backColor=LIGHT,
            leftIndent=4,
            rightIndent=4,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "title": ParagraphStyle(
            "TitleMain",
            fontName="Times-Bold",
            fontSize=26,
            leading=32,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "covermeta": ParagraphStyle(
            "CoverMeta",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "toc": ParagraphStyle(
            "TOC",
            fontName="Times-Roman",
            fontSize=11,
            leading=16,
            textColor=INK,
            leftIndent=8,
        ),
        "footer": ParagraphStyle(
            "Footer",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
        ),
        "th": ParagraphStyle(
            "TH",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=WHITE,
        ),
        "td": ParagraphStyle(
            "TD",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=INK,
        ),
    }


def markdown_to_xml(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    escaped = re.sub(r"`([^`]+)`", r"<font face='Courier' size='8'>\1</font>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", escaped)
    return escaped


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_divider(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def make_table(rows: list[list[str]], style_map: dict[str, ParagraphStyle], width: float) -> Table:
    col_count = max(len(row) for row in rows)
    normalised = [row + [""] * (col_count - len(row)) for row in rows]
    data = []
    for index, row in enumerate(normalised):
        paragraph_style = style_map["th"] if index == 0 else style_map["td"]
        data.append([Paragraph(markdown_to_xml(cell), paragraph_style) for cell in row])
    col_width = width / col_count
    table = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.3, RULE),
            ]
        )
    )
    return table


def parse_markdown(markdown: str, style_map: dict[str, ParagraphStyle], width: float) -> list:
    story: list = []
    lines = markdown.replace("\r\n", "\n").split("\n")
    index = 0
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    table_rows: list[list[str]] = []
    in_code = False
    code_lines: list[str] = []
    major_pagebreaks = {
        "## Executive summary",
        "## 6. Data sources and verified API behaviour",
        "## 12. Statistical formulas",
        "## 16. Important assumptions and limitations",
        "## 19. How to Explain This Project in an Interview",
    }

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            story.append(Paragraph(markdown_to_xml(" ".join(paragraph_lines)), style_map["body"]))
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items
        if not list_items:
            return
        items = [
            ListItem(Paragraph(markdown_to_xml(item), style_map["bullet"]), leftIndent=12)
            for item in list_items
        ]
        story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=18, spaceAfter=6))
        list_items = []

    def flush_table() -> None:
        nonlocal table_rows
        if table_rows:
            story.append(Spacer(1, 4))
            story.append(make_table(table_rows, style_map, width))
            story.append(Spacer(1, 8))
            table_rows = []

    diagram_captions = {
        "business": "Figure 1. Business workflow from Elexon data to decision support.",
        "architecture": "Figure 2. Planned system architecture. Only documentation exists today.",
        "selection": "Figure 3. As-of forecast selection for one delivery period.",
        "processing": "Figure 4. Planned data-processing pipeline.",
        "deployment": "Figure 5. Planned deployment path. No public URL exists yet.",
        "frontend": "Figure 6. WindLens frontend data flow (implemented).",
    }

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()
            if in_code:
                story.append(Preformatted("\n".join(code_lines) or " ", style_map["code"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            index += 1
            continue

        if in_code:
            code_lines.append(line)
            index += 1
            continue

        diagram_match = re.fullmatch(r"<!-- DIAGRAM: ([a-z]+) -->", stripped)
        if diagram_match:
            flush_paragraph()
            flush_list()
            flush_table()
            kind = diagram_match.group(1)
            story.append(Spacer(1, 6))
            story.append(Diagram(kind, width))
            story.append(Paragraph(diagram_captions[kind], style_map["caption"]))
            index += 1
            continue

        if stripped == "---":
            flush_paragraph()
            flush_list()
            flush_table()
            index += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_list()
            if is_table_divider(stripped):
                index += 1
                continue
            table_rows.append(split_table_row(stripped))
            index += 1
            continue
        flush_table()

        if stripped.startswith("#"):
            flush_paragraph()
            flush_list()
            heading = stripped.lstrip("#").strip()
            level = len(stripped) - len(stripped.lstrip("#"))
            if level == 1:
                # The Markdown H1 is represented by the designed title page.
                index += 1
                continue
            if level == 2 and stripped in major_pagebreaks and story:
                story.append(CondPageBreak(120))
            style_name = "h2" if level == 2 else "h3"
            story.append(Paragraph(markdown_to_xml(heading), style_map[style_name]))
            index += 1
            continue

        list_match = re.match(r"^[-*] (.+)$", stripped) or re.match(r"^\d+\. (.+)$", stripped)
        if list_match:
            flush_paragraph()
            list_items.append(list_match.group(1))
            index += 1
            continue
        flush_list()

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    flush_list()
    flush_table()
    return story


def cover_page(style_map: dict[str, ParagraphStyle], width: float) -> list:
    banner = Table(
        [
            [Paragraph("UK Electricity Utility Assignment", style_map["subtitle"])],
            [Spacer(1, 10)],
            [Paragraph("UK Wind Generation Forecast Accuracy", style_map["title"])],
            [Spacer(1, 8)],
            [
                Paragraph(
                    "Decision-support and forecast-accuracy report for national Elexon wind data",
                    style_map["subtitle"],
                )
            ],
        ],
        colWidths=[width],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    meta = Table(
        [
            [Paragraph("<b>Report date</b>", style_map["covermeta"]), Paragraph("25 October 2026", style_map["covermeta"])],
            [Paragraph("<b>Current milestone</b>", style_map["covermeta"]), Paragraph("3 - WindLens React dashboard", style_map["covermeta"])],
            [Paragraph("<b>Application status</b>", style_map["covermeta"]), Paragraph("Backend + WindLens frontend implemented locally", style_map["covermeta"])],
            [Paragraph("<b>API investigation</b>", style_map["covermeta"]), Paragraph("Live Elexon requests succeeded", style_map["covermeta"])],
            [Paragraph("<b>Deployment</b>", style_map["covermeta"]), Paragraph("Not deployed. No public URL exists.", style_map["covermeta"])],
            [Paragraph("<b>Data scope</b>", style_map["covermeta"]), Paragraph("WINDFOR forecasts and FUELHH WIND actuals, January 2026", style_map["covermeta"])],
        ],
        colWidths=[width * 0.32, width * 0.68],
    )
    meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, TEAL),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    summary = Paragraph(
        markdown_to_xml(
            "This printable report is generated from docs/PROJECT_REPORT.md. "
            "Milestone 1 verifies the Elexon data contracts and records the analytical "
            "rules. The React dashboard, FastAPI service, tests, Docker setup, and "
            "public deployment are planned and are not claimed as complete."
        ),
        style_map["body"],
    )
    return [
        banner,
        Spacer(1, 18),
        meta,
        Spacer(1, 16),
        summary,
        Spacer(1, 10),
        Paragraph("Contents", style_map["h2"]),
        Paragraph("1. Business problem and proposed solution", style_map["toc"]),
        Paragraph("2. Why wind generation forecasting matters", style_map["toc"]),
        Paragraph("3. Actual generation versus forecast generation", style_map["toc"]),
        Paragraph("4. startTime and publishTime", style_map["toc"]),
        Paragraph("5. Historical forecast publication times", style_map["toc"]),
        Paragraph("6. Data sources and verified API behaviour", style_map["toc"]),
        Paragraph("7-11. Pipeline, architecture, files, planned API and UI", style_map["toc"]),
        Paragraph("12. Statistical formulas and worked example", style_map["toc"]),
        Paragraph("13-15. Data quality, testing, Docker and deployment", style_map["toc"]),
        Paragraph("16-18. Assumptions, customer demo, technical review", style_map["toc"]),
        Paragraph("19. How to Explain This Project in an Interview", style_map["toc"]),
        PageBreak(),
    ]


def add_page_decorations(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, A4[1] - 14 * mm, A4[0], 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, A4[1] - 8.5 * mm, "UK Wind Generation Forecast Accuracy")
    canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 8.5 * mm, "Milestone 1 investigation")
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, A4[0], 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 5 * mm, "Generated from docs/PROJECT_REPORT.md")
    canvas.drawRightString(A4[0] - 18 * mm, 5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf(markdown_path: Path, pdf_path: Path) -> Path:
    style_map = styles()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="UK Wind Generation Forecast Accuracy",
        author="ELECTRICITY assignment workspace",
        subject="Milestone 1 investigation and architecture report",
    )
    width = A4[0] - 36 * mm
    markdown = markdown_path.read_text(encoding="utf-8")
    story = cover_page(style_map, width)
    story.extend(parse_markdown(markdown, style_map, width))
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    return pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PROJECT_REPORT.pdf from Markdown.")
    parser.add_argument("--input", type=Path, default=MARKDOWN_PATH)
    parser.add_argument("--output", type=Path, default=PDF_PATH)
    args = parser.parse_args()
    output = build_pdf(args.input, args.output)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
