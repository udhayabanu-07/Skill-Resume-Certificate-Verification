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
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def build_resume_pdf(profile, template: str = 'modern') -> io.BytesIO:
    """
    Generates a professional, beautifully styled resume PDF from a JobSeekerProfile using ReportLab.
    Supports multiple professional layout themes:
    - 'modern': SkillVerify signature Navy (#0B2545) & Teal (#00A896), centered header
    - 'executive': Corporate Slate (#1E293B) & Royal Blue (#1D4ED8), left-aligned header
    - 'minimal': Classic Monochrome (#111827) & Charcoal (#4B5563), clean editorial style
    Returns an in-memory BytesIO buffer containing the PDF document.
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

    template = template.lower() if template else 'modern'
    if template == 'executive':
        primary_color = colors.HexColor('#1E293B')
        secondary_color = colors.HexColor('#1D4ED8')
        accent_color = colors.HexColor('#2563EB')
        header_align = TA_LEFT
    elif template == 'minimal':
        primary_color = colors.HexColor('#111827')
        secondary_color = colors.HexColor('#374151')
        accent_color = colors.HexColor('#4B5563')
        header_align = TA_LEFT
    else:  # 'modern' (default)
        primary_color = colors.HexColor('#0B2545')
        secondary_color = colors.HexColor('#134074')
        accent_color = colors.HexColor('#00A896')
        header_align = TA_CENTER

    text_dark = colors.HexColor('#1E293B')
    text_muted = colors.HexColor('#64748B')
    border_color = colors.HexColor('#CBD5E1')
    verified_green = colors.HexColor('#059669')

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocName',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=2,
        alignment=header_align
    )

    headline_style = ParagraphStyle(
        'DocHeadline',
        parent=styles['Normal'],
        fontName='Helvetica-Bold' if template == 'executive' else 'Helvetica',
        fontSize=12,
        leading=15,
        textColor=accent_color,
        spaceAfter=5,
        alignment=header_align
    )

    contact_style = ParagraphStyle(
        'DocContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=text_muted,
        alignment=header_align
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        alignment=TA_LEFT
    )

    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    date_style = ParagraphStyle(
        'DocDate',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=text_muted,
        alignment=TA_RIGHT
    )

    verified_badge_style = ParagraphStyle(
        'VerifiedBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=verified_green,
        alignment=TA_RIGHT
    )

    story = []

    # 1. HEADER: Name, Headline & Contact Details
    full_name = profile.full_name or profile.user.username
    story.append(Paragraph(full_name, title_style))

    if profile.headline:
        story.append(Paragraph(profile.headline, headline_style))

    contact_parts = []
    if profile.user and profile.user.email:
        contact_parts.append(profile.user.email)
    if profile.phone:
        contact_parts.append(profile.phone)
    location_parts = [p for p in (profile.city, profile.country) if p]
    if location_parts:
        contact_parts.append(", ".join(location_parts))
    if profile.linkedin_url:
        contact_parts.append("LinkedIn")
    if profile.github_url:
        contact_parts.append("GitHub")

    if contact_parts:
        contact_line = " &nbsp;|&nbsp; ".join(contact_parts)
        story.append(Paragraph(contact_line, contact_style))

    # Divider bar
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=4, spaceAfter=8))

    # 2. CAREER OBJECTIVE / PROFESSIONAL SUMMARY
    career_summary = getattr(profile, 'career_objective', None) or profile.bio
    if career_summary:
        story.append(Paragraph("CAREER OBJECTIVE", section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
        story.append(Paragraph(career_summary, body_style))
        story.append(Spacer(1, 6))

    # 3. WORK EXPERIENCE
    work_list = profile.work_experiences.all()
    if work_list:
        story.append(Paragraph("WORK EXPERIENCE", section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
        for exp in work_list:
            start_str = exp.start_date.strftime('%b %Y') if exp.start_date else ''
            end_str = "Present" if exp.is_current else (exp.end_date.strftime('%b %Y') if exp.end_date else '')
            dates = f"{start_str} – {end_str}".strip(' –')

            header_table = Table(
                [[
                    Paragraph(f"<b>{exp.job_title}</b> — <font color='#134074'>{exp.company}</font>", body_style),
                    Paragraph(dates, date_style)
                ]],
                colWidths=[420, 120]
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ]))
            story.append(header_table)

            if exp.location:
                story.append(Paragraph(f"<font color='#64748B'><i>{exp.location}</i></font>", body_style))

            if exp.description:
                story.append(Spacer(1, 2))
                story.append(Paragraph(exp.description, body_style))

            story.append(Spacer(1, 6))

    # 4. EDUCATION
    edu_list = profile.education_entries.all()
    if edu_list:
        story.append(Paragraph("EDUCATION", section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
        for edu in edu_list:
            start_str = edu.start_date.strftime('%b %Y') if edu.start_date else ''
            end_str = edu.end_date.strftime('%b %Y') if edu.end_date else ''
            dates = f"{start_str} – {end_str}".strip(' –')

            degree_text = f"<b>{edu.degree}</b>"
            if edu.field_of_study:
                degree_text += f" in {edu.field_of_study}"
            degree_text += f" — <font color='#134074'>{edu.institution}</font>"

            header_table = Table(
                [[
                    Paragraph(degree_text, body_style),
                    Paragraph(dates, date_style)
                ]],
                colWidths=[420, 120]
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ]))
            story.append(header_table)

            if edu.grade_or_cgpa:
                story.append(Paragraph(f"<font color='#64748B'>Grade/CGPA: {edu.grade_or_cgpa}</font>", body_style))

            if edu.description:
                story.append(Paragraph(edu.description, body_style))

            story.append(Spacer(1, 5))

    # 5. SKILLS & COMPETENCIES
    skills_list = profile.skills.all()
    tech_skills = [s for s in skills_list if getattr(s, 'category', 'technical') != 'soft']
    soft_skills = [s for s in skills_list if getattr(s, 'category', 'technical') == 'soft']

    if tech_skills:
        story.append(Paragraph("TECHNICAL SKILLS", section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
        tech_items = []
        for s in tech_skills:
            verified_mark = " ✓" if s.is_verified else ""
            tech_items.append(f"<b>{s.name}</b> ({s.proficiency_level.capitalize()}{verified_mark})")
        story.append(Paragraph(" &nbsp;•&nbsp; ".join(tech_items), body_style))
        story.append(Spacer(1, 6))

    if soft_skills:
        story.append(Paragraph("SOFT SKILLS & COMPETENCIES", section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
        soft_items = [f"<b>{s.name}</b> ({s.proficiency_level.capitalize()})" for s in soft_skills]
        story.append(Paragraph(" &nbsp;•&nbsp; ".join(soft_items), body_style))
        story.append(Spacer(1, 6))

    # 6. PROJECTS
    if hasattr(profile, 'projects'):
        projects_list = profile.projects.all()
        if projects_list:
            story.append(Paragraph("PROJECTS", section_heading))
            story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
            for proj in projects_list:
                proj_title = f"<b>{proj.title}</b>"
                if proj.technologies:
                    proj_title += f" <font color='#64748B'>[{proj.technologies}]</font>"

                link_text = f"<font color='#00A896'>{proj.project_url}</font>" if proj.project_url else ""

                proj_table = Table(
                    [[
                        Paragraph(proj_title, body_style),
                        Paragraph(link_text, date_style)
                    ]],
                    colWidths=[400, 140]
                )
                proj_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ]))
                story.append(proj_table)

                if proj.description:
                    story.append(Paragraph(proj.description, body_style))

                story.append(Spacer(1, 5))

    # 7. CERTIFICATIONS & VERIFIED CREDENTIALS
    certs_list = profile.certificates.all()
    if certs_list:
        story.append(Paragraph("CERTIFICATIONS & CREDENTIALS", section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
        for cert in certs_list:
            date_str = cert.issue_date.strftime('%b %Y') if cert.issue_date else ''
            
            # Show verified badge if approved by admin
            if cert.status == 'verified':
                status_text = "<b><font color='#059669'>[VERIFIED CREDENTIAL]</font></b>"
            elif cert.status == 'pending':
                status_text = "<font color='#D97706'>[Pending Audit]</font>"
            else:
                status_text = ""

            cert_text = f"<b>{cert.title}</b> — <font color='#134074'>{cert.issuing_organization}</font>"
            if cert.credential_id:
                cert_text += f" <font color='#64748B'>(ID: {cert.credential_id})</font>"

            cert_table = Table(
                [[
                    Paragraph(cert_text, body_style),
                    Paragraph(f"{status_text} {date_str}".strip(), date_style)
                ]],
                colWidths=[390, 150]
            )
            cert_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ]))
            story.append(cert_table)
            story.append(Spacer(1, 4))

    # 8. ACHIEVEMENTS & AWARDS
    if hasattr(profile, 'achievements'):
        achieve_list = profile.achievements.all()
        if achieve_list:
            story.append(Paragraph("HONORS & ACHIEVEMENTS", section_heading))
            story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=1, spaceAfter=4))
            for ach in achieve_list:
                date_str = ach.date_achieved.strftime('%b %Y') if ach.date_achieved else ''
                ach_table = Table(
                    [[
                        Paragraph(f"<b>{ach.title}</b>", body_style),
                        Paragraph(date_str, date_style)
                    ]],
                    colWidths=[440, 100]
                )
                ach_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                ]))
                story.append(ach_table)
                if ach.description:
                    story.append(Paragraph(ach.description, body_style))
                story.append(Spacer(1, 4))

    # Build the document
    doc.build(story)
    buffer.seek(0)
    return buffer
