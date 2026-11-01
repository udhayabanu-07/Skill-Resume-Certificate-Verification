import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, abort, send_from_directory, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.seeker import seeker_bp
from app.extensions import db
from app.models import (
    User,
    JobSeekerProfile,
    Education,
    Skill,
    WorkExperience,
    Project,
    Achievement,
    Resume,
    Certificate,
    Notification
)
from app.utils.security import seeker_required, is_allowed_file, generate_secure_stored_filename
from app.utils.pdf_generator import build_resume_pdf

ALLOWED_CERTIFICATE_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
ALLOWED_CERTIFICATE_MIME_TYPES = {
    'application/pdf',
    'image/png',
    'image/jpeg',
    'image/pjpeg'
}

ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx', 'doc'}
ALLOWED_RESUME_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/octet-stream'  # Fallback for some browsers on docx
}

ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def parse_date_input(date_str: str | None):
    """Safely parses a date string in YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def get_or_create_profile(user) -> JobSeekerProfile:
    """Ensures a JobSeekerProfile exists for the given user."""
    profile = user.profile
    if not profile:
        profile = JobSeekerProfile(
            user_id=user.id,
            first_name=user.username,
            last_name="Seeker"
        )
        db.session.add(profile)
        db.session.commit()
    return profile


# ===================================================================
# JOB SEEKER DASHBOARD
# ===================================================================

@seeker_bp.route('/dashboard')
@login_required
@seeker_required
def dashboard():
    """Job seeker portal dashboard displaying resume status and certificates."""
    profile = get_or_create_profile(current_user)

    certificates = profile.certificates.order_by(Certificate.uploaded_at.desc()).all()
    resumes = profile.resumes.order_by(Resume.uploaded_at.desc()).all()
    educations = profile.education_entries.all()
    skills = profile.skills.all()
    experiences = profile.work_experiences.all()
    projects = profile.projects.all()
    achievements = profile.achievements.all()

    stats = {
        'education_count': len(educations),
        'skill_count': len(skills),
        'experience_count': len(experiences),
        'project_count': len(projects),
        'achievement_count': len(achievements),
        'resume_count': len(resumes),
        'certificate_count': len(certificates),
        'verified_certificates': sum(1 for c in certificates if c.status == 'verified'),
        'pending_certificates': sum(1 for c in certificates if c.status == 'pending'),
        'rejected_certificates': sum(1 for c in certificates if c.status == 'rejected'),
    }

    return render_template(
        'seeker/dashboard.html',
        profile=profile,
        stats=stats,
        certificates=certificates,
        resumes=resumes,
        educations=educations,
        skills=skills,
        experiences=experiences,
        projects=projects,
        achievements=achievements
    )


# ===================================================================
# RESUME MANAGEMENT: BUILDER & EDITOR
# ===================================================================

@seeker_bp.route('/resume/builder', methods=['GET', 'POST'])
@seeker_bp.route('/resume/create', methods=['GET', 'POST'])
@seeker_bp.route('/resume/edit', methods=['GET', 'POST'])
@login_required
@seeker_required
def resume_builder():
    """
    Resume Builder / Editor: Allows Job Seekers to create and edit personal info,
    career objective, education, technical skills, work experience, projects, and achievements.
    """
    profile = get_or_create_profile(current_user)

    if request.method == 'POST':
        # Update Personal Information and Career Objective
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        headline = request.form.get('headline', '').strip()
        phone = request.form.get('phone', '').strip()
        city = request.form.get('city', '').strip()
        country = request.form.get('country', '').strip()
        address = request.form.get('address', '').strip()
        linkedin_url = request.form.get('linkedin_url', '').strip()
        github_url = request.form.get('github_url', '').strip()
        portfolio_url = request.form.get('portfolio_url', '').strip()
        career_objective = request.form.get('career_objective', '').strip()

        errors = []
        if not first_name:
            errors.append("First Name is required.")
        if not last_name:
            errors.append("Last Name is required.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return redirect(url_for('seeker.resume_builder'))

        profile.first_name = first_name
        profile.last_name = last_name
        profile.headline = headline
        profile.phone = phone
        profile.city = city
        profile.country = country
        profile.address = address
        profile.linkedin_url = linkedin_url
        profile.github_url = github_url
        profile.portfolio_url = portfolio_url
        profile.career_objective = career_objective
        profile.bio = career_objective  # Keep bio in sync for backwards compatibility

        db.session.commit()
        flash("Resume details updated successfully!", "success")
        return redirect(url_for('seeker.resume_builder'))

    educations = profile.education_entries.order_by(Education.end_date.desc()).all()
    skills = profile.skills.order_by(Skill.name.asc()).all()
    experiences = profile.work_experiences.order_by(WorkExperience.start_date.desc()).all()
    projects = profile.projects.order_by(Project.created_at.desc()).all()
    achievements = profile.achievements.order_by(Achievement.created_at.desc()).all()
    certificates = profile.certificates.order_by(Certificate.uploaded_at.desc()).all()

    return render_template(
        'seeker/resume_builder.html',
        profile=profile,
        educations=educations,
        skills=skills,
        experiences=experiences,
        projects=projects,
        achievements=achievements,
        certificates=certificates
    )


# ===================================================================
# RESUME PREVIEW & REPORTLAB PDF DOWNLOAD
# ===================================================================

@seeker_bp.route('/resume/preview')
@seeker_bp.route('/resume/view')
@login_required
@seeker_required
def resume_preview():
    """
    Displays the Job Seeker's complete resume in a professional web layout with preview controls.
    """
    profile = get_or_create_profile(current_user)

    educations = profile.education_entries.order_by(Education.end_date.desc()).all()
    skills = profile.skills.order_by(Skill.name.asc()).all()
    experiences = profile.work_experiences.order_by(WorkExperience.start_date.desc()).all()
    projects = profile.projects.order_by(Project.created_at.desc()).all()
    achievements = profile.achievements.order_by(Achievement.created_at.desc()).all()
    certificates = profile.certificates.order_by(Certificate.uploaded_at.desc()).all()

    return render_template(
        'seeker/resume_preview.html',
        profile=profile,
        educations=educations,
        skills=skills,
        experiences=experiences,
        projects=projects,
        achievements=achievements,
        certificates=certificates
    )


@seeker_bp.route('/resume/download-pdf')
@login_required
@seeker_required
def resume_download_pdf():
    """
    Generates and downloads a clean, professional PDF resume compiled using ReportLab.
    """
    profile = get_or_create_profile(current_user)
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


# ===================================================================
# UPLOAD EXISTING RESUME (PDF / DOCX)
# ===================================================================

@seeker_bp.route('/resume/upload', methods=['POST'])
@login_required
@seeker_required
def upload_existing_resume():
    """
    Uploads an existing resume document (PDF or DOCX), validates type and size,
    and stores it securely in app/uploads/resumes/.
    """
    profile = get_or_create_profile(current_user)

    if 'resume_file' not in request.files:
        flash("No file was submitted for upload.", "danger")
        return redirect(url_for('seeker.dashboard'))

    file = request.files['resume_file']
    if not file or file.filename == '':
        flash("Please select a valid resume document (PDF or DOCX).", "danger")
        return redirect(url_for('seeker.dashboard'))

    # Validate file extension
    if not is_allowed_file(file.filename, ALLOWED_RESUME_EXTENSIONS):
        flash("Invalid file format. Only PDF and DOCX resume documents are allowed.", "danger")
        return redirect(url_for('seeker.dashboard'))

    # Validate MIME type
    content_type = getattr(file, 'mimetype', '') or getattr(file, 'content_type', '')
    if content_type and content_type.lower() not in ALLOWED_RESUME_MIME_TYPES:
        flash("Invalid file type. Please upload a genuine PDF or Word document.", "danger")
        return redirect(url_for('seeker.dashboard'))

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    if file_size > max_size:
        max_mb = max_size // (1024 * 1024)
        flash(f"Resume file size exceeds the {max_mb} MB limit.", "danger")
        return redirect(url_for('seeker.dashboard'))
    elif file_size == 0:
        flash("The selected resume file is empty.", "danger")
        return redirect(url_for('seeker.dashboard'))

    # Save file securely
    stored_filename = generate_secure_stored_filename(file.filename, prefix=f"resume_{profile.id}")
    upload_folder = current_app.config['RESUME_UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    destination_path = os.path.join(upload_folder, stored_filename)

    file.save(destination_path)

    # Set as primary if it's the first resume
    is_primary = profile.resumes.count() == 0

    resume_record = Resume(
        profile_id=profile.id,
        original_filename=secure_filename(file.filename) or file.filename,
        stored_filename=stored_filename,
        file_path=destination_path,
        file_size=file_size,
        mime_type=file.mimetype or 'application/octet-stream',
        is_primary=is_primary
    )
    db.session.add(resume_record)

    notification = Notification(
        user_id=current_user.id,
        title="Resume Document Uploaded",
        message=f"Your resume '{file.filename}' was uploaded successfully.",
        notification_type="success"
    )
    db.session.add(notification)

    db.session.commit()

    flash("Resume document uploaded successfully!", "success")
    return redirect(url_for('seeker.dashboard'))


@seeker_bp.route('/resume/uploaded/<int:resume_id>/view')
@login_required
def view_uploaded_resume(resume_id):
    """
    Allows viewing or downloading an uploaded resume document.
    Access is restricted to the owning Job Seeker and authorized Administrators.
    """
    resume_item = Resume.query.get_or_404(resume_id)

    if not current_user.is_admin and resume_item.profile.user_id != current_user.id:
        abort(403)

    upload_folder = current_app.config['RESUME_UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, resume_item.stored_filename)

    if not os.path.exists(file_path):
        flash("The requested resume file does not exist on storage.", "danger")
        return redirect(url_for('seeker.dashboard'))

    return send_from_directory(
        upload_folder,
        resume_item.stored_filename,
        as_attachment=False
    )


@seeker_bp.route('/resume/uploaded/<int:resume_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_uploaded_resume(resume_id):
    """Deletes an uploaded resume document."""
    resume_item = Resume.query.get_or_404(resume_id)

    if resume_item.profile.user_id != current_user.id:
        abort(403)

    file_path = resume_item.file_path
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    db.session.delete(resume_item)
    db.session.commit()

    flash("Resume document deleted successfully.", "info")
    return redirect(url_for('seeker.dashboard'))


@seeker_bp.route('/resume/uploaded/<int:resume_id>/set-primary', methods=['POST'])
@login_required
@seeker_required
def set_primary_resume(resume_id):
    """Sets a specific uploaded resume as the candidate's primary resume."""
    profile = get_or_create_profile(current_user)
    resume_item = Resume.query.get_or_404(resume_id)

    if resume_item.profile_id != profile.id:
        abort(403)

    for r in profile.resumes:
        r.is_primary = (r.id == resume_id)

    db.session.commit()
    flash(f"'{resume_item.original_filename}' is now set as your primary resume.", "success")
    return redirect(url_for('seeker.dashboard'))


# ===================================================================
# SUB-SECTIONS: EDUCATION, SKILLS, EXPERIENCE, PROJECTS, ACHIEVEMENTS
# ===================================================================

@seeker_bp.route('/resume/education/add', methods=['POST'])
@login_required
@seeker_required
def add_education():
    """Adds an education entry to the candidate's resume."""
    profile = get_or_create_profile(current_user)

    institution = request.form.get('institution', '').strip()
    degree = request.form.get('degree', '').strip()
    field_of_study = request.form.get('field_of_study', '').strip()
    start_date = parse_date_input(request.form.get('start_date'))
    end_date = parse_date_input(request.form.get('end_date'))
    grade_or_cgpa = request.form.get('grade_or_cgpa', '').strip()
    description = request.form.get('description', '').strip()

    if not institution or not degree:
        flash("Institution and Degree are required.", "danger")
        return redirect(url_for('seeker.resume_builder'))

    edu = Education(
        profile_id=profile.id,
        institution=institution,
        degree=degree,
        field_of_study=field_of_study or None,
        start_date=start_date,
        end_date=end_date,
        grade_or_cgpa=grade_or_cgpa or None,
        description=description or None
    )
    db.session.add(edu)
    db.session.commit()

    flash("Education entry added successfully!", "success")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/education/<int:item_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_education(item_id):
    """Deletes an education entry."""
    edu = Education.query.get_or_404(item_id)
    if edu.profile.user_id != current_user.id:
        abort(403)

    db.session.delete(edu)
    db.session.commit()
    flash("Education entry removed.", "info")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/skill/add', methods=['POST'])
@login_required
@seeker_required
def add_skill():
    """Adds a technical or soft skill to the candidate's resume."""
    profile = get_or_create_profile(current_user)

    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'technical').strip().lower()
    proficiency_level = request.form.get('proficiency_level', 'intermediate').strip().lower()
    years_exp_str = request.form.get('years_of_experience', '0').strip()
    cert_id_raw = request.form.get('certificate_id', '').strip()

    if not name:
        flash("Skill name is required.", "danger")
        return redirect(url_for('seeker.resume_builder'))

    try:
        years_exp = float(years_exp_str) if years_exp_str else 0.0
    except ValueError:
        years_exp = 0.0

    cert_id = int(cert_id_raw) if cert_id_raw.isdigit() else None

    skill = Skill(
        profile_id=profile.id,
        name=name,
        category=category if category in ('technical', 'soft') else 'technical',
        proficiency_level=proficiency_level if proficiency_level in ('beginner', 'intermediate', 'advanced', 'expert') else 'intermediate',
        years_of_experience=years_exp,
        certificate_id=cert_id
    )
    db.session.add(skill)
    db.session.commit()

    flash(f"Skill '{name}' added successfully!", "success")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/skill/<int:item_id>/edit', methods=['POST'])
@login_required
@seeker_required
def edit_skill(item_id):
    """Updates an existing skill."""
    skill = Skill.query.get_or_404(item_id)
    if skill.profile.user_id != current_user.id:
        abort(403)

    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'technical').strip().lower()
    proficiency_level = request.form.get('proficiency_level', 'intermediate').strip().lower()
    years_exp_str = request.form.get('years_of_experience', '0').strip()
    cert_id_raw = request.form.get('certificate_id', '').strip()

    if not name:
        flash("Skill name cannot be empty.", "danger")
        return redirect(url_for('seeker.resume_builder'))

    try:
        years_exp = float(years_exp_str) if years_exp_str else 0.0
    except ValueError:
        years_exp = skill.years_of_experience

    skill.name = name
    skill.category = category if category in ('technical', 'soft') else 'technical'
    skill.proficiency_level = proficiency_level if proficiency_level in ('beginner', 'intermediate', 'advanced', 'expert') else 'intermediate'
    skill.years_of_experience = years_exp
    skill.certificate_id = int(cert_id_raw) if cert_id_raw.isdigit() else None

    db.session.commit()
    flash(f"Skill '{name}' updated successfully!", "success")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/skill/<int:item_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_skill(item_id):
    """Deletes a technical skill."""
    skill = Skill.query.get_or_404(item_id)
    if skill.profile.user_id != current_user.id:
        abort(403)

    db.session.delete(skill)
    db.session.commit()
    flash("Skill removed.", "info")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/experience/add', methods=['POST'])
@login_required
@seeker_required
def add_experience():
    """Adds a work experience entry to the candidate's resume."""
    profile = get_or_create_profile(current_user)

    company = request.form.get('company', '').strip()
    job_title = request.form.get('job_title', '').strip()
    location = request.form.get('location', '').strip()
    start_date = parse_date_input(request.form.get('start_date'))
    end_date = parse_date_input(request.form.get('end_date'))
    is_current = bool(request.form.get('is_current'))
    description = request.form.get('description', '').strip()

    if not company or not job_title or not start_date:
        flash("Company, Job Title, and Start Date are required.", "danger")
        return redirect(url_for('seeker.resume_builder'))

    exp = WorkExperience(
        profile_id=profile.id,
        company=company,
        job_title=job_title,
        location=location or None,
        start_date=start_date,
        end_date=None if is_current else end_date,
        is_current=is_current,
        description=description or None
    )
    db.session.add(exp)
    db.session.commit()

    flash("Work experience added successfully!", "success")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/experience/<int:item_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_experience(item_id):
    """Deletes a work experience entry."""
    exp = WorkExperience.query.get_or_404(item_id)
    if exp.profile.user_id != current_user.id:
        abort(403)

    db.session.delete(exp)
    db.session.commit()
    flash("Work experience entry removed.", "info")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/project/add', methods=['POST'])
@login_required
@seeker_required
def add_project():
    """Adds a project entry to the candidate's resume."""
    profile = get_or_create_profile(current_user)

    title = request.form.get('title', '').strip()
    technologies = request.form.get('technologies', '').strip()
    project_url = request.form.get('project_url', '').strip()
    description = request.form.get('description', '').strip()

    if not title:
        flash("Project Title is required.", "danger")
        return redirect(url_for('seeker.resume_builder'))

    proj = Project(
        profile_id=profile.id,
        title=title,
        technologies=technologies or None,
        project_url=project_url or None,
        description=description or None
    )
    db.session.add(proj)
    db.session.commit()

    flash(f"Project '{title}' added successfully!", "success")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/project/<int:item_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_project(item_id):
    """Deletes a project entry."""
    proj = Project.query.get_or_404(item_id)
    if proj.profile.user_id != current_user.id:
        abort(403)

    db.session.delete(proj)
    db.session.commit()
    flash("Project removed.", "info")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/achievement/add', methods=['POST'])
@login_required
@seeker_required
def add_achievement():
    """Adds an achievement / honor to the candidate's resume."""
    profile = get_or_create_profile(current_user)

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    date_achieved = parse_date_input(request.form.get('date_achieved'))

    if not title:
        flash("Achievement Title is required.", "danger")
        return redirect(url_for('seeker.resume_builder'))

    ach = Achievement(
        profile_id=profile.id,
        title=title,
        description=description or None,
        date_achieved=date_achieved
    )
    db.session.add(ach)
    db.session.commit()

    flash(f"Achievement '{title}' added successfully!", "success")
    return redirect(url_for('seeker.resume_builder'))


@seeker_bp.route('/resume/achievement/<int:item_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_achievement(item_id):
    """Deletes an achievement entry."""
    ach = Achievement.query.get_or_404(item_id)
    if ach.profile.user_id != current_user.id:
        abort(403)

    db.session.delete(ach)
    db.session.commit()
    flash("Achievement removed.", "info")
    return redirect(url_for('seeker.resume_builder'))


# ===================================================================
# CERTIFICATE UPLOAD (Existing Feature Preserved)
# ===================================================================

@seeker_bp.route('/upload-certificate', methods=['POST'])
@seeker_bp.route('/certificate/upload', methods=['POST'])
@login_required
@seeker_required
def upload_certificate():
    """
    Handles secure certificate uploads by authenticated Job Seekers.
    Validates certificate name, issuing organization, issue date, file type, and file size.
    Initial verification status is strictly set to 'pending'.
    """
    profile = get_or_create_profile(current_user)

    title = request.form.get('title', '').strip()
    issuing_organization = request.form.get('issuing_organization', '').strip()
    issue_date_str = request.form.get('issue_date', '').strip()
    expiration_date_str = request.form.get('expiration_date', '').strip()
    credential_id = request.form.get('credential_id', '').strip()
    credential_url = request.form.get('credential_url', '').strip()

    errors = []

    if not title:
        errors.append("Certificate Name / Title is required.")
    elif len(title) > 200:
        errors.append("Certificate Name cannot exceed 200 characters.")

    if not issuing_organization:
        errors.append("Issuing Organization is required.")
    elif len(issuing_organization) > 200:
        errors.append("Issuing Organization cannot exceed 200 characters.")

    issue_date = parse_date_input(issue_date_str)
    expiration_date = parse_date_input(expiration_date_str)

    if 'certificate_file' not in request.files:
        errors.append("Please select a certificate file to upload.")
        file = None
    else:
        file = request.files['certificate_file']
        if not file or file.filename == '':
            errors.append("Please select a valid certificate file.")

    if file and file.filename != '':
        if not is_allowed_file(file.filename, ALLOWED_CERTIFICATE_EXTENSIONS):
            errors.append("Invalid file format. Only PDF, JPG, and PNG files are allowed.")

        content_type = getattr(file, 'mimetype', '') or getattr(file, 'content_type', '')
        if content_type and content_type.lower() not in ALLOWED_CERTIFICATE_MIME_TYPES:
            errors.append("Invalid file type. File MIME type must be a valid PDF or image (JPG/PNG).")

        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        max_allowed_bytes = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        if file_size > max_allowed_bytes:
            max_mb = max_allowed_bytes // (1024 * 1024)
            errors.append(f"File size exceeds the {max_mb} MB limit.")
        elif file_size == 0:
            errors.append("The selected file is empty. Please choose a valid file.")

    if errors:
        for err in errors:
            flash(err, 'danger')
        return redirect(url_for('seeker.dashboard'))

    stored_filename = generate_secure_stored_filename(file.filename, prefix=f"cert_{profile.id}")
    upload_folder = current_app.config['CERTIFICATE_UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    destination_path = os.path.join(upload_folder, stored_filename)

    file.save(destination_path)

    certificate = Certificate(
        profile_id=profile.id,
        title=title,
        issuing_organization=issuing_organization,
        issue_date=issue_date,
        expiration_date=expiration_date,
        credential_id=credential_id if credential_id else None,
        credential_url=credential_url if credential_url else None,
        original_filename=secure_filename(file.filename) or file.filename,
        stored_filename=stored_filename,
        file_path=destination_path,
        file_size=file_size,
        mime_type=file.mimetype or 'application/octet-stream',
        status='pending'
    )
    db.session.add(certificate)

    notification = Notification(
        user_id=current_user.id,
        title="Certificate Submitted",
        message=f"Your certificate '{title}' has been uploaded and is pending review by an administrator.",
        notification_type="info"
    )
    db.session.add(notification)

    db.session.commit()

    flash("Certificate uploaded successfully! It is now pending verification by an administrator.", "success")
    return redirect(url_for('seeker.dashboard'))


@seeker_bp.route('/certificate/<int:cert_id>/view')
@login_required
def view_certificate(cert_id):
    """Secure certificate viewing endpoint."""
    certificate = Certificate.query.get_or_404(cert_id)

    if not current_user.is_admin and certificate.profile.user_id != current_user.id:
        abort(403)

    upload_folder = current_app.config['CERTIFICATE_UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, certificate.stored_filename)

    if not os.path.exists(file_path):
        flash("The requested certificate file could not be found on the server.", "danger")
        return redirect(url_for('seeker.dashboard'))

    return send_from_directory(
        upload_folder,
        certificate.stored_filename,
        as_attachment=False
    )


@seeker_bp.route('/certificate/<int:cert_id>/edit', methods=['GET', 'POST'])
@login_required
@seeker_required
def edit_certificate(cert_id):
    """Allows candidate to update metadata of an uploaded certificate."""
    certificate = Certificate.query.get_or_404(cert_id)
    if certificate.profile.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        issuing_organization = request.form.get('issuing_organization', '').strip()
        issue_date = parse_date_input(request.form.get('issue_date', ''))
        expiration_date = parse_date_input(request.form.get('expiration_date', ''))
        credential_id = request.form.get('credential_id', '').strip()
        credential_url = request.form.get('credential_url', '').strip()

        if not title or not issuing_organization:
            flash("Certificate title and issuing organization are required.", "danger")
            return render_template('seeker/certificate_edit.html', certificate=certificate)

        certificate.title = title
        certificate.issuing_organization = issuing_organization
        certificate.issue_date = issue_date
        certificate.expiration_date = expiration_date
        certificate.credential_id = credential_id if credential_id else None
        certificate.credential_url = credential_url if credential_url else None

        # Check if replacement file was uploaded
        if 'certificate_file' in request.files:
            new_file = request.files['certificate_file']
            if new_file and new_file.filename != '':
                if is_allowed_file(new_file.filename, ALLOWED_CERTIFICATE_EXTENSIONS):
                    stored_name = generate_secure_stored_filename(new_file.filename, prefix=f"cert_{certificate.profile_id}")
                    dest = os.path.join(current_app.config['CERTIFICATE_UPLOAD_FOLDER'], stored_name)
                    new_file.save(dest)
                    certificate.stored_filename = stored_name
                    certificate.original_filename = secure_filename(new_file.filename) or new_file.filename
                    certificate.file_path = dest
                    certificate.status = 'pending'

        db.session.commit()
        flash(f"Certificate '{certificate.title}' updated successfully.", "success")
        return redirect(url_for('seeker.dashboard'))

    return render_template('seeker/certificate_edit.html', certificate=certificate)


@seeker_bp.route('/certificate/<int:cert_id>/delete', methods=['POST'])
@login_required
@seeker_required
def delete_certificate(cert_id):
    """Deletes an uploaded certificate and removes the stored document."""
    certificate = Certificate.query.get_or_404(cert_id)
    if certificate.profile.user_id != current_user.id:
        abort(403)

    if certificate.file_path and os.path.exists(certificate.file_path):
        try:
            os.remove(certificate.file_path)
        except OSError:
            pass

    title = certificate.title
    db.session.delete(certificate)
    db.session.commit()

    flash(f"Certificate '{title}' removed successfully.", "info")
    return redirect(url_for('seeker.dashboard'))


# ===================================================================
# PROFILE MANAGEMENT
# ===================================================================

@seeker_bp.route('/profile')
@login_required
@seeker_required
def view_profile():
    """Displays the comprehensive profile of the authenticated Job Seeker."""
    profile = get_or_create_profile(current_user)
    return render_template('seeker/profile_view.html', profile=profile)


@seeker_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@seeker_required
def edit_profile():
    """Allows the Job Seeker to update their profile and upload a photograph."""
    profile = get_or_create_profile(current_user)

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        headline = request.form.get('headline', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = parse_date_input(request.form.get('date_of_birth', ''))
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        country = request.form.get('country', '').strip()
        career_objective = request.form.get('career_objective', '').strip()
        bio = request.form.get('bio', '').strip() or career_objective
        linkedin_url = request.form.get('linkedin_url', '').strip()
        github_url = request.form.get('github_url', '').strip()
        portfolio_url = request.form.get('portfolio_url', '').strip()

        if not first_name or not last_name:
            flash("First Name and Last Name are required.", "danger")
            return render_template('seeker/profile_edit.html', profile=profile)

        profile.first_name = first_name
        profile.last_name = last_name
        profile.headline = headline
        profile.phone = phone
        profile.date_of_birth = dob
        profile.address = address
        profile.city = city
        profile.state = state
        profile.country = country
        profile.career_objective = career_objective
        profile.bio = bio
        profile.linkedin_url = linkedin_url
        profile.github_url = github_url
        profile.portfolio_url = portfolio_url

        # Photograph Upload Validation
        if 'profile_photo' in request.files:
            photo = request.files['profile_photo']
            if photo and photo.filename != '':
                ext = photo.filename.rsplit('.', 1)[-1].lower() if '.' in photo.filename else ''
                if ext in ALLOWED_PHOTO_EXTENSIONS:
                    try:
                        from PIL import Image
                        img = Image.open(photo)
                        img.verify()
                        photo.seek(0)
                        photo_stored_name = generate_secure_stored_filename(photo.filename, prefix=f"photo_{profile.id}")
                        photo_dest = os.path.join(current_app.config['PROFILE_PICTURE_UPLOAD_FOLDER'], photo_stored_name)
                        photo.save(photo_dest)
                        profile.profile_picture = photo_stored_name
                    except Exception:
                        flash("Invalid image file uploaded. Profile picture not updated.", "warning")
                else:
                    flash("Invalid image format. Allowed formats: PNG, JPG, JPEG, WEBP.", "warning")

        # In-app notification
        notification = Notification(
            user_id=current_user.id,
            title="Profile Updated",
            message="Your job seeker profile information has been successfully updated.",
            notification_type="success"
        )
        db.session.add(notification)

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('seeker.view_profile'))

    return render_template('seeker/profile_edit.html', profile=profile)


@seeker_bp.route('/profile/photo/<int:profile_id>')
def view_profile_photo(profile_id):
    """Serves the profile photograph securely."""
    profile = JobSeekerProfile.query.get_or_404(profile_id)
    if not profile.profile_picture:
        abort(404)
    upload_folder = current_app.config['PROFILE_PICTURE_UPLOAD_FOLDER']
    return send_from_directory(upload_folder, profile.profile_picture)


# ===================================================================
# NOTIFICATIONS MANAGEMENT
# ===================================================================

@seeker_bp.route('/notifications')
@login_required
def notifications_list():
    """Lists all in-app notifications for the logged in user."""
    notifications = current_user.notifications.all()
    return render_template('notifications/index.html', notifications=notifications)


@seeker_bp.route('/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Marks an individual notification as read."""
    notif = Notification.query.get_or_404(notification_id)
    if notif.user_id != current_user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "success")
    return redirect(url_for('seeker.notifications_list'))


@seeker_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Marks all user notifications as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for('seeker.notifications_list'))
