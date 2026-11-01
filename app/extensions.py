import secrets
from functools import wraps
from flask import session, request, abort, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# SQLAlchemy database instance
db = SQLAlchemy()

# Flask-Login instance
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


def generate_csrf_token() -> str:
    """
    Retrieves or generates a secure CSRF token tied to the user's session.
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token: str | None) -> bool:
    """
    Validates the provided CSRF token against the one stored in session.
    """
    if not token:
        return False
    session_token = session.get('_csrf_token')
    if not session_token:
        return False
    return secrets.compare_digest(session_token, token)


def csrf_protect():
    """
    Global before_request hook to validate CSRF tokens on mutating HTTP methods.
    Checks request.form, JSON payload, and custom headers.
    """
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        # Check if the endpoint has explicitly been exempted
        endpoint = request.endpoint
        if endpoint:
            view_func = current_app.view_functions.get(endpoint)
            if getattr(view_func, '_csrf_exempt', False):
                return None

        # Extract token from form, header, or json
        token = (
            request.form.get('csrf_token')
            or request.headers.get('X-CSRFToken')
            or request.headers.get('X-CSRF-Token')
        )
        if not token and request.is_json:
            token = request.json.get('csrf_token') if isinstance(request.json, dict) else None

        if not validate_csrf_token(token):
            abort(400, description="Security Error: CSRF token is missing or invalid. Please refresh the page and try again.")


def csrf_exempt(f):
    """Decorator to mark a route as exempt from CSRF protection."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    decorated_function._csrf_exempt = True
    return decorated_function
