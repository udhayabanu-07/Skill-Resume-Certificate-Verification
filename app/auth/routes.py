import re
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.auth import auth_bp
from app.extensions import db
from app.models import User, JobSeekerProfile, Notification


def get_reset_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_reset_token(email: str) -> str:
    s = get_reset_serializer()
    return s.dumps(email, salt='password-reset-salt')


def verify_reset_token(token: str, max_age: int = 3600):
    s = get_reset_serializer()
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=max_age)
        return email
    except (SignatureExpired, BadSignature):
        return None


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration. Public registration strictly creates Job Seeker accounts."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Public registration is strictly locked to job_seeker role.
        # Admin accounts can only be created via the secure CLI command.
        role = 'job_seeker'

        # Validation
        errors = []
        if not first_name or len(first_name) > 64:
            errors.append("First name is required (maximum 64 characters).")

        if not last_name or len(last_name) > 64:
            errors.append("Last name is required (maximum 64 characters).")

        if not username or len(username) < 3 or len(username) > 64:
            errors.append("Username must be between 3 and 64 characters long.")
        elif not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            errors.append("Username can only contain letters, numbers, dots, hyphens, and underscores.")

        if not email:
            errors.append("Email address is required.")
        else:
            try:
                valid_info = validate_email(email, check_deliverability=False)
                email = valid_info.normalized
            except EmailNotValidError as e:
                errors.append(f"Invalid email address: {str(e)}")

        if not password or len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")

        # Check existing username and email
        if username and User.query.filter_by(username=username).first():
            errors.append("The username is already taken. Please choose another.")
        if email and User.query.filter_by(email=email).first():
            errors.append("The email address is already registered. Please sign in or use another email.")

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'auth/register.html',
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email
            )

        # Create user account strictly as Job Seeker
        user = User(
            username=username,
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Obtain user.id

        # Create associated Job Seeker profile
        profile = JobSeekerProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(profile)

        # Send welcome notification
        welcome_notification = Notification(
            user_id=user.id,
            title="Welcome to Skill & Certificate Verification System",
            message="Your job seeker account has been created. You can now upload your professional certificates and resumes for verification.",
            notification_type="info"
        )
        db.session.add(welcome_notification)

        db.session.commit()

        flash("Registration successful! You can now log in with your credentials.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user authentication."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        login_identifier = request.form.get('login_identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not login_identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('auth/login.html', login_identifier=login_identifier)

        # Find user by username or email
        user = User.query.filter(
            (User.username == login_identifier) | (User.email == login_identifier.lower())
        ).first()

        if not user or not user.check_password(password):
            flash("Invalid credentials. Please verify and try again.", "danger")
            return render_template('auth/login.html', login_identifier=login_identifier)

        if not user.is_active:
            flash("Your account has been deactivated. Please contact an administrator.", "warning")
            return render_template('auth/login.html', login_identifier=login_identifier)

        login_user(user, remember=remember)
        flash(f"Welcome back, {user.username}!", "success")

        # Handle 'next' query param for safe redirection
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        return redirect(url_for('auth.dashboard_redirect'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logs out the current authenticated user."""
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('main.index'))


@auth_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirects the authenticated user to their role-appropriate dashboard."""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('seeker.dashboard'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Allows authenticated users to change their account password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.", "danger")
            return render_template('auth/change_password.html')

        if not current_user.check_password(current_password):
            flash("Your current password does not match our records.", "danger")
            return render_template('auth/change_password.html')

        if len(new_password) < 8:
            flash("New password must be at least 8 characters long.", "danger")
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash("New password and confirmation do not match.", "danger")
            return render_template('auth/change_password.html')

        current_user.set_password(new_password)

        notification = Notification(
            user_id=current_user.id,
            title="Password Changed",
            message="Your account password was successfully updated. If you did not make this change, contact support immediately.",
            notification_type="warning"
        )
        db.session.add(notification)
        db.session.commit()

        flash("Your password has been changed successfully!", "success")
        return redirect(url_for('auth.dashboard_redirect'))

    return render_template('auth/change_password.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Initiates password reset request workflow."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    reset_link = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        if not identifier:
            flash("Please enter your registered username or email address.", "danger")
            return render_template('auth/forgot_password.html')

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user:
            token = generate_reset_token(user.email)
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            flash(f"Password reset instructions have been generated for {user.email}.", "success")
            return render_template('auth/forgot_password.html', reset_link=reset_link, user=user)
        else:
            flash("No active account found with that email address or username.", "danger")
            return render_template('auth/forgot_password.html')

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Resets user password with valid token."""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    email = verify_reset_token(token)
    if not email:
        flash("The password reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User account associated with this token was not found.", "danger")
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password or not confirm_password:
            flash("Please enter and confirm your new password.", "danger")
            return render_template('auth/reset_password.html', token=token)

        if len(new_password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template('auth/reset_password.html', token=token)

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('auth/reset_password.html', token=token)

        user.set_password(new_password)
        db.session.commit()

        notification = Notification(
            user_id=user.id,
            title="Password Reset Successful",
            message="Your account password was reset using a recovery link.",
            notification_type="info"
        )
        db.session.add(notification)
        db.session.commit()

        flash("Your password has been reset successfully! You can now log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token, email=email)
