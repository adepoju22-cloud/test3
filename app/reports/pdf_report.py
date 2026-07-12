"""
PDF report generator built with ReportLab.

Produces a professional compliance report containing:
    - Title page header
    - Executive summary
    - Compliance score
    - A severity-breakdown bar chart
    - Top recommendations
    - A detailed findings table
"""

from datetime import datetime
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from sqlalchemy.orm import Session

from app.database.models import ComplianceResult
from app.services.summary_service import build_summary
from app.utils.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

_SEVERITY_COLORS = {
    "Critical": colors.HexColor("#C0392B"),
    "High": colors.HexColor("#E67E22"),
    "Medium": colors.HexColor("#F1C40F"),
    "Low": colors.HexColor("#27AE60"),
}


def _severity_chart(breakdown: dict) -> Drawing:
    """Build a simple vertical bar chart of findings by severity."""
    drawing = Drawing(400, 200)
    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 30
    chart.height = 140
    chart.width = 300
    chart.data = [
        [
            breakdown["critical"],
            breakdown["high"],
            breakdown["medium"],
            breakdown["low"],
        ]
    ]
    chart.categoryAxis.categoryNames = ["Critical", "High", "Medium", "Low"]
    chart.bars[0].colorSamples = list(_SEVERITY_COLORS.values())
    chart.valueAxis.valueMin = 0
    drawing.add(chart)
    return drawing


def generate_pdf_report(db: Session, filename: str | None = None) -> Path:
    """
    Generate a full PDF compliance report.

    Args:
        db: Active SQLAlchemy session.
        filename: Optional explicit filename; auto-generated if omitted.

    Returns:
        Path to the generated PDF file.
    """
    summary = build_summary(db)
    findings = (
        db.query(ComplianceResult)
        .filter(ComplianceResult.status == "FAIL")
        .order_by(ComplianceResult.severity.asc())
        .all()
    )

    if filename is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"compliance_report_{timestamp}.pdf"
    output_path = settings.reports_dir / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=22, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], spaceBefore=16, spaceAfter=8
    )
    body_style = styles["BodyText"]

    elements = []

    elements.append(Paragraph(settings.app_name, title_style))
    elements.append(
        Paragraph(
            f"Compliance Scan Report &mdash; Generated "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            subtitle_style,
        )
    )

    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(
        Paragraph(
            f"This report summarizes the results of an automated compliance "
            f"scan covering {summary.total_findings} control evaluations across "
            f"the local resource inventory. The environment achieved an overall "
            f"compliance score of <b>{summary.compliance_percentage}%</b>, with "
            f"{summary.passed} controls passing and {summary.failed} controls "
            f"failing. Findings are mapped to the CIS, NIST, and ISO 27001 "
            f"frameworks to support multi-framework audit readiness.",
            body_style,
        )
    )

    elements.append(Paragraph("Compliance Score", heading_style))
    score_table = Table(
        [
            ["Compliance %", "Passed", "Failed", "Total Evaluations"],
            [
                f"{summary.compliance_percentage}%",
                str(summary.passed),
                str(summary.failed),
                str(summary.total_findings),
            ],
        ],
        colWidths=[1.6 * inch] * 4,
    )
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ECF0F1")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(score_table)

    elements.append(Paragraph("Findings by Severity", heading_style))
    sb = summary.severity_breakdown
    elements.append(
        _severity_chart(
            {
                "critical": sb.critical,
                "high": sb.high,
                "medium": sb.medium,
                "low": sb.low,
            }
        )
    )

    elements.append(Paragraph("Top Recommendations", heading_style))
    if summary.top_violated_rules:
        for rule in summary.top_violated_rules[:5]:
            elements.append(
                Paragraph(
                    f"&bull; <b>{rule['rule_id']}</b> &mdash; {rule['rule_name']} "
                    f"({rule['violations']} violation(s))",
                    body_style,
                )
            )
    else:
        elements.append(Paragraph("No outstanding violations found.", body_style))

    elements.append(PageBreak())
    elements.append(Paragraph("Detailed Findings (Failed Controls)", heading_style))

    table_data = [["Resource", "Type", "Rule", "Severity", "Framework"]]
    for f in findings:
        table_data.append(
            [
                f.resource_name,
                f.resource_type,
                f.rule_id,
                f.severity,
                f.framework[:40] + ("..." if len(f.framework) > 40 else ""),
            ]
        )

    if len(table_data) > 1:
        findings_table = Table(
            table_data,
            colWidths=[1.4 * inch, 1.1 * inch, 0.9 * inch, 0.9 * inch, 2.1 * inch],
            repeatRows=1,
        )
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        for row_index, f in enumerate(findings, start=1):
            color = _SEVERITY_COLORS.get(f.severity, colors.black)
            style_commands.append(
                ("TEXTCOLOR", (3, row_index), (3, row_index), color)
            )
        findings_table.setStyle(TableStyle(style_commands))
        elements.append(findings_table)
    else:
        elements.append(Paragraph("No failed controls to display.", body_style))

    doc.build(elements)
    logger.info("PDF report generated at %s", output_path)
    return output_path
