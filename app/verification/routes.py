import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from app.verification import verification_bp
from app.extensions import db
from app.utils.security import admin_required
from app.models import Certificate, VerificationRecord, Notification


@verification_bp.route('/queue')
@login_required
@admin_required
def queue():
    """Admin queue of pending certificates requiring manual verification."""
    pending_certificates = Certificate.query.filter_by(status='pending').order_by(Certificate.uploaded_at.asc()).all()
    return render_template('verification/queue.html', certificates=pending_certificates)


@verification_bp.route('/review/<int:cert_id>', methods=['POST'])
@login_required
@admin_required
def review_certificate(cert_id):
    """
    Authorized Admin review action to verify or reject a certificate.
    Creates an immutable VerificationRecord audit log and notifies the candidate.
    """
    certificate = Certificate.query.get_or_404(cert_id)
    action = request.form.get('action', '').strip().lower()  # 'verified' or 'rejected'
    remarks = request.form.get('remarks', '').strip()

    if action not in ('verified', 'rejected'):
        flash("Invalid verification action. Action must be 'verified' or 'rejected'.", "danger")
        return redirect(url_for('verification.queue'))

    # Update certificate status
    certificate.status = action
    certificate.verified_at = datetime.utcnow()
    certificate.verified_by_id = current_user.id

    # Create immutable audit record
    record = VerificationRecord(
        certificate_id=certificate.id,
        admin_id=current_user.id,
        action=action,
        remarks=remarks if remarks else None
    )
    db.session.add(record)

    # Notify candidate
    notification = Notification(
        user_id=certificate.profile.user_id,
        title=f"Certificate {action.capitalize()}",
        message=f"Your certificate '{certificate.title}' has been reviewed and marked as {action.upper()} by an administrator. Remarks: {remarks or 'None'}",
        notification_type="success" if action == 'verified' else "danger"
    )
    db.session.add(notification)

    db.session.commit()

    flash(f"Certificate #{certificate.id} ('{certificate.title}') has been marked as {action.capitalize()}.", "success")
    return redirect(url_for('verification.queue'))


@verification_bp.route('/view/<int:cert_id>')
@login_required
@admin_required
def view_certificate(cert_id):
    """Allows administrators to inspect the uploaded certificate document."""
    certificate = Certificate.query.get_or_404(cert_id)
    upload_folder = current_app.config['CERTIFICATE_UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, certificate.stored_filename)

    if not os.path.exists(file_path):
        flash("Certificate document file was not found on server storage.", "danger")
        return redirect(url_for('verification.queue'))

    return send_from_directory(
        upload_folder,
        certificate.stored_filename,
        as_attachment=False
    )
