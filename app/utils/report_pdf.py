import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def build_system_report_pdf(stats: dict, recent_records: list) -> io.BytesIO:
    """
    Generates a professional administrative audit and analytics report in PDF using ReportLab.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    navy = colors.HexColor('#0B2545')
    teal = colors.HexColor('#00A896')
    text_dark = colors.HexColor('#1E293B')
    text_muted = colors.HexColor('#64748B')
    border_color = colors.HexColor('#CBD5E1')
    success_color = colors.HexColor('#059669')
    danger_color = colors.HexColor('#DC2626')

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=navy,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'RepSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=text_muted
    )

    heading_style = ParagraphStyle(
        'RepHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=navy,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=text_dark
    )

    body_bold = ParagraphStyle(
        'RepBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Header Banner
    story.append(Paragraph("SKILLVERIFY SYSTEM ANALYTICS & AUDIT REPORT", title_style))
    now_str = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
    story.append(Paragraph(f"Official Verification Platform Report &bull; Generated on {now_str}", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=teal, spaceBefore=4, spaceAfter=12))

    # 1. Executive Summary Table
    story.append(Paragraph("1. EXECUTIVE KEY PERFORMANCE METRICS", heading_style))

    kpi_data = [
        [
            Paragraph("<b>Metric</b>", body_bold),
            Paragraph("<b>Count / Value</b>", body_bold),
            Paragraph("<b>Metric</b>", body_bold),
            Paragraph("<b>Count / Value</b>", body_bold)
        ],
        [
            Paragraph("Total Registered Users", body_style),
            Paragraph(str(stats.get('total_users', 0)), body_bold),
            Paragraph("Total Candidate Profiles", body_style),
            Paragraph(str(stats.get('total_seekers', 0)), body_bold)
        ],
        [
            Paragraph("Total Uploaded Resumes", body_style),
            Paragraph(str(stats.get('total_resumes', 0)), body_bold),
            Paragraph("Total Certificate Submissions", body_style),
            Paragraph(str(stats.get('total_certificates', 0)), body_bold)
        ],
        [
            Paragraph("Verified Certificates", body_style),
            Paragraph(f"<font color='#059669'><b>{stats.get('verified_count', 0)}</b></font>", body_style),
            Paragraph("Approval Percentage", body_style),
            Paragraph(f"<b>{stats.get('approval_rate', 0)}%</b>", body_bold)
        ],
        [
            Paragraph("Rejected Certificates", body_style),
            Paragraph(f"<font color='#DC2626'><b>{stats.get('rejected_count', 0)}</b></font>", body_style),
            Paragraph("Rejection Percentage", body_style),
            Paragraph(f"<b>{stats.get('rejection_rate', 0)}%</b>", body_bold)
        ],
        [
            Paragraph("Pending Verification Queue", body_style),
            Paragraph(f"<font color='#D97706'><b>{stats.get('pending_count', 0)}</b></font>", body_style),
            Paragraph("Total Human Audits Logged", body_style),
            Paragraph(str(stats.get('total_audits', 0)), body_bold)
        ],
    ]

    kpi_table = Table(kpi_data, colWidths=[150, 120, 150, 120])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # 2. Recent Human-in-the-Loop Verification Audit Log
    story.append(Paragraph("2. RECENT VERIFICATION AUDIT DECISIONS", heading_style))

    if recent_records:
        rec_data = [[
            Paragraph("<b>Timestamp</b>", body_bold),
            Paragraph("<b>Certificate Title</b>", body_bold),
            Paragraph("<b>Candidate</b>", body_bold),
            Paragraph("<b>Action</b>", body_bold),
            Paragraph("<b>Reviewer Remarks</b>", body_bold)
        ]]

        for r in recent_records[:15]:
            ts = r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''
            cert_title = r.certificate.title if r.certificate else 'Unknown'
            candidate = r.certificate.profile.full_name if (r.certificate and r.certificate.profile) else 'N/A'
            act_color = '#059669' if r.action == 'verified' else '#DC2626'
            act_text = f"<font color='{act_color}'><b>{r.action.upper()}</b></font>"
            remarks = r.remarks or 'No remarks recorded'

            rec_data.append([
                Paragraph(ts, body_style),
                Paragraph(cert_title[:28] + ('...' if len(cert_title) > 28 else ''), body_style),
                Paragraph(candidate, body_style),
                Paragraph(act_text, body_style),
                Paragraph(remarks[:36] + ('...' if len(remarks) > 36 else ''), body_style)
            ])

        rec_table = Table(rec_data, colWidths=[90, 140, 100, 70, 140])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, border_color),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(rec_table)
    else:
        story.append(Paragraph("No verification decisions have been recorded yet.", body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=4, spaceAfter=8))
    footer_text = f"SkillVerify Platform Audit Engine &bull; Confidential Administrative Report &bull; {now_str}"
    story.append(Paragraph(footer_text, ParagraphStyle('RepFooter', parent=subtitle_style, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer
