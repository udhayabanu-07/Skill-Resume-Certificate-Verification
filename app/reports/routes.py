import io
import csv
from datetime import datetime, timedelta
from flask import render_template, request, Response, send_file
from flask_login import login_required
from app.reports import reports_bp
from app.utils.security import admin_required
from app.models import User, Certificate, VerificationRecord, Resume
from app.utils.report_pdf import build_system_report_pdf


def parse_date_filter(date_str: str | None):
    """Parses date string or returns None."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


@reports_bp.route('/')
@login_required
@admin_required
def index():
    """
    Comprehensive administrative reports, verification analytics, and metric charts.
    Supports dynamic date filtering, PDF report generation, and CSV exporting.
    """
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    start_date = parse_date_filter(start_date_str)
    end_date = parse_date_filter(end_date_str)
    if end_date:
        end_date = end_date.replace(hour=23, minute=59, second=59)

    # Base queries
    user_q = User.query
    cert_q = Certificate.query
    audit_q = VerificationRecord.query
    resume_q = Resume.query

    if start_date:
        user_q = user_q.filter(User.created_at >= start_date)
        cert_q = cert_q.filter(Certificate.uploaded_at >= start_date)
        audit_q = audit_q.filter(VerificationRecord.created_at >= start_date)
        resume_q = resume_q.filter(Resume.uploaded_at >= start_date)

    if end_date:
        user_q = user_q.filter(User.created_at <= end_date)
        cert_q = cert_q.filter(Certificate.uploaded_at <= end_date)
        audit_q = audit_q.filter(VerificationRecord.created_at <= end_date)
        resume_q = resume_q.filter(Resume.uploaded_at <= end_date)

    total_users = user_q.count()
    total_seekers = user_q.filter_by(role='job_seeker').count()
    total_resumes = resume_q.count()
    total_certificates = cert_q.count()
    verified_count = cert_q.filter_by(status='verified').count()
    rejected_count = cert_q.filter_by(status='rejected').count()
    pending_count = cert_q.filter_by(status='pending').count()
    total_audits = audit_q.count()

    total_reviewed = verified_count + rejected_count
    approval_rate = round((verified_count / total_reviewed * 100), 1) if total_reviewed > 0 else 0.0
    rejection_rate = round((rejected_count / total_reviewed * 100), 1) if total_reviewed > 0 else 0.0

    recent_verifications = audit_q.order_by(VerificationRecord.created_at.desc()).limit(25).all()

    # Calculate last 6 months activity for charts
    months_labels = []
    monthly_users = []
    monthly_certs = []

    now = datetime.utcnow()
    for i in range(5, -1, -1):
        # Approximate month bounds
        ref_date = now - timedelta(days=i * 30)
        month_label = ref_date.strftime('%b %Y')
        months_labels.append(month_label)

        m_start = datetime(ref_date.year, ref_date.month, 1)
        if ref_date.month == 12:
            m_end = datetime(ref_date.year + 1, 1, 1)
        else:
            m_end = datetime(ref_date.year, ref_date.month + 1, 1)

        u_count = User.query.filter(User.created_at >= m_start, User.created_at < m_end).count()
        c_count = Certificate.query.filter(Certificate.uploaded_at >= m_start, Certificate.uploaded_at < m_end).count()

        monthly_users.append(u_count)
        monthly_certs.append(c_count)

    stats = {
        'total_users': total_users,
        'total_seekers': total_seekers,
        'total_resumes': total_resumes,
        'total_certificates': total_certificates,
        'verified_count': verified_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'total_audits': total_audits,
        'approval_rate': approval_rate,
        'rejection_rate': rejection_rate
    }

    chart_data = {
        'months': months_labels,
        'monthly_users': monthly_users,
        'monthly_certs': monthly_certs,
        'status_counts': [verified_count, pending_count, rejected_count]
    }

    return render_template(
        'reports/index.html',
        stats=stats,
        recent=recent_verifications,
        chart_data=chart_data,
        start_date=start_date_str,
        end_date=end_date_str
    )


@reports_bp.route('/export-csv')
@login_required
@admin_required
def export_csv():
    """Generates and streams a CSV export of all verification decisions and candidate certificates."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        'Certificate ID',
        'Title',
        'Issuing Organization',
        'Candidate Name',
        'Candidate Email',
        'Status',
        'Submission Date',
        'Verification Date',
        'Reviewer ID',
        'Remarks'
    ])

    certificates = Certificate.query.order_by(Certificate.uploaded_at.desc()).all()
    for cert in certificates:
        candidate_name = cert.profile.full_name if cert.profile else 'N/A'
        candidate_email = cert.profile.user.email if (cert.profile and cert.profile.user) else 'N/A'
        sub_date = cert.uploaded_at.strftime('%Y-%m-%d %H:%M') if cert.uploaded_at else ''
        ver_date = cert.verified_at.strftime('%Y-%m-%d %H:%M') if cert.verified_at else ''

        # Get latest review remarks
        last_rec = cert.verification_records.first()
        remarks = last_rec.remarks if last_rec else ''

        writer.writerow([
            cert.id,
            cert.title,
            cert.issuing_organization,
            candidate_name,
            candidate_email,
            cert.status.upper(),
            sub_date,
            ver_date,
            cert.verified_by_id or '',
            remarks
        ])

    csv_data = output.getvalue()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"skillverify_verification_report_{timestamp}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@reports_bp.route('/pdf')
@login_required
@admin_required
def download_pdf_report():
    """Generates and downloads a comprehensive executive ReportLab PDF report."""
    total_users = User.query.count()
    total_seekers = User.query.filter_by(role='job_seeker').count()
    total_resumes = Resume.query.count()
    total_certificates = Certificate.query.count()
    verified_count = Certificate.query.filter_by(status='verified').count()
    rejected_count = Certificate.query.filter_by(status='rejected').count()
    pending_count = Certificate.query.filter_by(status='pending').count()
    total_audits = VerificationRecord.query.count()

    total_reviewed = verified_count + rejected_count
    approval_rate = round((verified_count / total_reviewed * 100), 1) if total_reviewed > 0 else 0.0
    rejection_rate = round((rejected_count / total_reviewed * 100), 1) if total_reviewed > 0 else 0.0

    recent_verifications = VerificationRecord.query.order_by(VerificationRecord.created_at.desc()).limit(20).all()

    stats = {
        'total_users': total_users,
        'total_seekers': total_seekers,
        'total_resumes': total_resumes,
        'total_certificates': total_certificates,
        'verified_count': verified_count,
        'rejected_count': rejected_count,
        'pending_count': pending_count,
        'total_audits': total_audits,
        'approval_rate': approval_rate,
        'rejection_rate': rejection_rate
    }

    pdf_buffer = build_system_report_pdf(stats, recent_verifications)
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    filename = f"SkillVerify_Audit_Report_{timestamp}.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
