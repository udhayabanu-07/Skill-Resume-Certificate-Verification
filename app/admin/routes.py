from flask import render_template, abort, send_file, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.admin import admin_bp
from app.extensions import db
from app.utils.security import admin_required
from app.models import User, JobSeekerProfile, Certificate, VerificationRecord, Resume, Notification
from app.utils.pdf_generator import build_resume_pdf


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin portal dashboard displaying system verification overview and chart analytics."""
    total_users = User.query.count()
    total_seekers = User.query.filter_by(role='job_seeker').count()
    pending_certificates = Certificate.query.filter_by(status='pending').count()
    verified_certificates = Certificate.query.filter_by(status='verified').count()
    rejected_certificates = Certificate.query.filter_by(status='rejected').count()
    total_resumes = Resume.query.count()
    recent_verifications = VerificationRecord.query.order_by(VerificationRecord.created_at.desc()).limit(10).all()

    stats = {
        'total_users': total_users,
        'total_seekers': total_seekers,
        'pending_certificates': pending_certificates,
        'verified_certificates': verified_certificates,
        'rejected_certificates': rejected_certificates,
        'total_resumes': total_resumes
    }

    return render_template('admin/dashboard.html', stats=stats, recent_verifications=recent_verifications)


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """Admin user management directory supporting search and role/status filtering."""
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = User.query

    if search:
        pattern = f"%{search}%"
        query = query.filter((User.username.ilike(pattern)) | (User.email.ilike(pattern)))

    if role_filter in ('job_seeker', 'admin'):
        query = query.filter_by(role=role_filter)

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)

    users = query.order_by(User.created_at.desc()).all()

    return render_template(
        'admin/users_list.html',
        users=users,
        search=search,
        selected_role=role_filter,
        selected_status=status_filter
    )


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Detailed inspection of a user account and associated candidate profile."""
    user = User.query.get_or_404(user_id)
    profile = user.profile
    resumes = profile.resumes.all() if profile else []
    certificates = profile.certificates.all() if profile else []

    return render_template(
        'admin/user_detail.html',
        user=user,
        profile=profile,
        resumes=resumes,
        certificates=certificates
    )


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activates or deactivates a user account."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    flash(f"Account for '{user.username}' has been {status_str}.", "success")
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/verifications')
@login_required
@admin_required
def verification_history():
    """Complete audit log of all certificate verification decisions."""
    action_filter = request.args.get('action', '').strip().lower()

    query = VerificationRecord.query

    if action_filter in ('verified', 'rejected'):
        query = query.filter_by(action=action_filter)

    records = query.order_by(VerificationRecord.created_at.desc()).all()

    return render_template('admin/verification_history.html', records=records, action_filter=action_filter)


@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications_list():
    """Lists notifications for admin user."""
    notifications = current_user.notifications.all()
    return render_template('notifications/index.html', notifications=notifications)


@admin_bp.route('/resumes')
@login_required
@admin_required
def resumes_list():
    """Admin directory of job seekers and their resumes."""
    seekers = JobSeekerProfile.query.all()
    return render_template('admin/resumes_list.html', seekers=seekers)


@admin_bp.route('/seeker/<int:user_id>/resume')
@login_required
@admin_required
def view_seeker_resume(user_id):
    """Allows an Administrator to inspect any candidate's resume preview."""
    seeker_user = User.query.get_or_404(user_id)
    profile = seeker_user.profile
    if not profile:
        abort(404, description="Candidate profile not found.")

    educations = profile.education_entries.all()
    skills = profile.skills.all()
    experiences = profile.work_experiences.all()
    projects = profile.projects.all()
    achievements = profile.achievements.all()
    certificates = profile.certificates.all()

    return render_template(
        'seeker/resume_preview.html',
        profile=profile,
        educations=educations,
        skills=skills,
        experiences=experiences,
        projects=projects,
        achievements=achievements,
        certificates=certificates,
        is_admin_view=True
    )


@admin_bp.route('/seeker/<int:user_id>/resume/pdf')
@login_required
@admin_required
def download_seeker_resume_pdf(user_id):
    """Allows an Administrator to download any candidate's resume PDF."""
    seeker_user = User.query.get_or_404(user_id)
    profile = seeker_user.profile
    if not profile:
        abort(404, description="Candidate profile not found.")

    template = request.args.get('template', 'modern')
    pdf_buffer = build_resume_pdf(profile, template=template)
    clean_name = secure_filename(profile.full_name) or f"Seeker_{profile.id}"
    filename = f"{clean_name}_Resume_{template.capitalize()}.pdf"

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
