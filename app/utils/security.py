import os
import uuid
from functools import wraps
from werkzeug.utils import secure_filename
from flask import abort, flash, redirect, url_for, current_app
from flask_login import current_user


def role_required(*allowed_roles):
    """
    Decorator to restrict route access to users with specified roles.
    If the user is not authenticated, redirects to login.
    If the user lacks the required role, aborts with HTTP 403 Forbidden.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator ensuring only users with the 'admin' role can access the route."""
    return role_required('admin')(f)


def seeker_required(f):
    """Decorator ensuring only users with the 'job_seeker' role can access the route."""
    return role_required('job_seeker')(f)


def get_file_extension(filename: str) -> str:
    """Extracts and lowercases the file extension."""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''


def is_allowed_file(filename: str, allowed_extensions: set) -> bool:
    """
    Checks if a filename possesses an allowed extension.
    """
    ext = get_file_extension(filename)
    return bool(ext and ext in allowed_extensions)


def validate_file_mime_type(file_storage, allowed_mime_types: set) -> bool:
    """
    Validates the MIME type reported by the file storage object.
    """
    if not file_storage:
        return False
    content_type = getattr(file_storage, 'mimetype', '') or getattr(file_storage, 'content_type', '')
    if not content_type:
        return False
    return content_type.lower() in {m.lower() for m in allowed_mime_types}


def generate_secure_stored_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generates a cryptographically random, collision-resistant, and sanitized filename.
    Example output: cert_a4b2c1d3_resume_john_doe.pdf
    """
    sanitized_original = secure_filename(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    ext = get_file_extension(sanitized_original)
    base_name = sanitized_original.rsplit('.', 1)[0] if '.' in sanitized_original else sanitized_original
    # Cap base name length to keep filesystem path length within safe limits
    base_name = base_name[:40]

    prefix_str = f"{prefix}_" if prefix else ""
    return f"{prefix_str}{unique_id}_{base_name}.{ext}" if ext else f"{prefix_str}{unique_id}_{base_name}"
