import os
import json
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether
)


def format_nested_value_for_pdf(value) -> str:
    """
    Transforms complex/nested Python objects into clean, readable HTML-like
    formatting for ReportLab Paragraph display instead of raw Python strings.
    Guarantees cell height never exceeds page boundaries.
    """
    if value is None:
        return '<font color="#94a3b8"><i>Not available</i></font>'

    if isinstance(value, bool):
        return "<b>Yes</b>" if value else "<b>No</b>"

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        val = value.strip()
        if not val:
            return '<font color="#94a3b8"><i>Not available</i></font>'
        # Escape XML entities for ReportLab Paragraph
        val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if len(val) > 1500:
            val = val[:1500] + "... [Content truncated in PDF table; see full text in CSV/JSON export]"
        if val.startswith("http://") or val.startswith("https://"):
            return f'<font color="#2563eb"><u>{val}</u></font>'
        return val

    # List of primitives or dictionaries
    if isinstance(value, list):
        if not value:
            return '<font color="#94a3b8"><i>(Empty list)</i></font>'
        max_items = 20
        items = []
        for i, item in enumerate(value[:max_items], 1):
            if isinstance(item, dict):
                sub_lines = []
                for sk, sv in list(item.items())[:10]:
                    clean_sv = str(sv).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    if len(clean_sv) > 200:
                        clean_sv = clean_sv[:200] + "..."
                    sub_lines.append(f"&nbsp;&nbsp;&bull; <b>{sk}</b>: {clean_sv}")
                if len(item) > 10:
                    sub_lines.append(f"&nbsp;&nbsp;&bull; <i>... and {len(item) - 10} more attributes</i>")
                items.append(f"<b>{i}.</b><br/>" + "<br/>".join(sub_lines))
            else:
                clean_item = str(item).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if len(clean_item) > 300:
                    clean_item = clean_item[:300] + "..."
                items.append(f"&bull; {clean_item}")
        if len(value) > max_items:
            items.append(f"&bull; <i>... and {len(value) - max_items} more items (see full dataset in CSV/JSON export)</i>")
        return "<br/>".join(items)

    # Dictionary
    if isinstance(value, dict):
        if not value:
            return '<font color="#94a3b8"><i>(Empty dictionary)</i></font>'
        max_entries = 20
        lines = []
        for i, (k, v) in enumerate(value.items()):
            if i >= max_entries:
                lines.append(f"&bull; <i>... and {len(value) - max_entries} more entries (see full dataset in CSV/JSON export)</i>")
                break
            clean_v = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if len(clean_v) > 300:
                clean_v = clean_v[:300] + "..."
            lines.append(f"&bull; <b>{k}</b>: {clean_v}")
        return "<br/>".join(lines)

    clean_repr = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if len(clean_repr) > 1500:
        clean_repr = clean_repr[:1500] + "... [Content truncated in PDF table; see full text in CSV/JSON export]"
    return clean_repr


def prepare_csv_dict(data: dict) -> dict:
    """Formats complex types into clean strings suitable for CSV columns."""
    csv_row = {}
    for k, v in data.items():
        if v is None:
            csv_row[k] = ""
        elif isinstance(v, (dict, list)):
            csv_row[k] = json.dumps(v, ensure_ascii=False)
        else:
            csv_row[k] = str(v)
    return csv_row


def save_reports(data: dict, output_folder: str = "output", page_type: str = None, plan: dict = None):
    """
    Generates CSV, JSON, and professional PDF reports for the extracted data.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Resolve page type
    if not page_type:
        if plan and isinstance(plan, dict) and plan.get("page_type"):
            page_type = str(plan.get("page_type")).title()
        elif "page_type" in data:
            page_type = str(data.get("page_type")).title()
        else:
            page_type = "Web Data Extraction"

    # ==================================
    # 1. CSV EXPORT
    # ==================================
    csv_path = os.path.join(output_folder, "extracted_data.csv")
    csv_ready_data = prepare_csv_dict(data)
    df = pd.DataFrame([csv_ready_data])
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # ==================================
    # 2. JSON EXPORT
    # ==================================
    json_path = os.path.join(output_folder, "extracted_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # ==================================
    # 3. PDF EXPORT
    # ==================================
    pdf_path = os.path.join(output_folder, "extracted_report.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14
    )

    h2_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "StandardBody",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    summary_box_style = ParagraphStyle(
        "SummaryBox",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )

    cell_key_style = ParagraphStyle(
        "CellKey",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a")
    )

    cell_val_style = ParagraphStyle(
        "CellVal",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # Title & Header
    story.append(Paragraph("Intelligent Web Data Extraction Report", title_style))
    story.append(Paragraph("Autonomous Intelligence Synthesis &bull; LangGraph &bull; Groq AI", subtitle_style))

    # Metadata Banner Table
    extraction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_url = str(data.get("source_url", "Not specified"))

    meta_table_data = [
        [
            Paragraph("<b>Page Classification</b>", cell_key_style),
            Paragraph(f"<font color='#0284c7'><b>{page_type}</b></font>", cell_val_style)
        ],
        [
            Paragraph("<b>Target Source URL</b>", cell_key_style),
            Paragraph(f"<font color='#2563eb'>{source_url}</font>", cell_val_style)
        ],
        [
            Paragraph("<b>Extraction Timestamp</b>", cell_key_style),
            Paragraph(extraction_time, cell_val_style)
        ]
    ]

    meta_table = Table(meta_table_data, colWidths=[45 * mm, 135 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Summary Section
    summary = data.get("summary")
    if summary:
        story.append(Paragraph("Executive Summary", h2_style))
        clean_sum = str(summary).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        summary_table = Table([[Paragraph(clean_sum, summary_box_style)]], colWidths=[180 * mm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("LINELEFT", (0, 0), (0, -1), 3, colors.HexColor("#3b82f6")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 8))

    # Extracted Data Table
    story.append(Paragraph("Extracted Structured Intelligence", h2_style))

    data_rows = [
        [
            Paragraph("<b>Schema Field</b>", ParagraphStyle("TH1", parent=cell_key_style, textColor=colors.white)),
            Paragraph("<b>Extracted Content & Structured Details</b>", ParagraphStyle("TH2", parent=cell_key_style, textColor=colors.white))
        ]
    ]

    for key, value in data.items():
        if key in ["summary"]:
            continue  # Already prominently displayed above
        field_label = key.replace("_", " ").title()
        formatted_val = format_nested_value_for_pdf(value)
        data_rows.append([
            Paragraph(f"<b>{field_label}</b>", cell_key_style),
            Paragraph(formatted_val, cell_val_style)
        ])

    data_table = Table(data_rows, colWidths=[50 * mm, 130 * mm], repeatRows=1)
    data_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(data_table)

    story.append(Spacer(1, 12))
    footer_text = "Generated autonomously by the Intelligent Web Data Extraction Agent (LangGraph & Groq)."
    story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7.5, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)))

    doc.build(story)

    return csv_path, json_path, pdf_path


if __name__ == "__main__":
    sample_data = {
        "title": "Quantum Computing Scalability in 2026",
        "authors": ["Dr. Elena Rostova", "Prof. Liam Chen"],
        "publication_date": "2026-01-15",
        "doi": "10.1038/s41586-026-00042",
        "summary": "This paper presents a scalable error-mitigated logical qubit architecture demonstrated on a 1000-qubit processor.",
        "keywords": ["Quantum Error Correction", "Fault-tolerant Computing", "Qubits"],
        "findings": {
            "fidelity": "99.98%",
            "qubit_count": 1024,
            "error_reduction": "10x"
        },
        "source_url": "https://arxiv.org/abs/2601.00042"
    }

    c, j, p = save_reports(sample_data, page_type="Research Paper")
    print(f"Reports created:\nCSV: {c}\nJSON: {j}\nPDF: {p}")