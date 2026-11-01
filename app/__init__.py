import os
from datetime import datetime
import click
from flask import Flask, render_template, Blueprint, jsonify
from flask_login import current_user
from config import config_by_name, Config
from app.extensions import db, login_manager, csrf_protect, generate_csrf_token


# Main Blueprint for public routes
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Platform landing and public home page."""
    from app.models import Certificate, JobSeekerProfile, Skill
    stats = {
        'total_profiles': JobSeekerProfile.query.count(),
        'verified_certificates': Certificate.query.filter_by(status='verified').count(),
        'total_skills': Skill.query.count()
    }
    return render_template('index.html', stats=stats)


@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'app': 'Skill Resume Certificate Verification System',
        'timestamp': datetime.utcnow().isoformat()
    })


@main_bp.route('/candidates')
def candidates_directory():
    """
    Public and verified candidate discovery directory.
    Supports search by name/headline, filtering by skills, qualifications, and verification status.
    """
    from flask import request
    from app.models import JobSeekerProfile, User, Skill, Education, Certificate

    search = request.args.get('search', '').strip()
    skill_filter = request.args.get('skill', '').strip()
    qualification_filter = request.args.get('qualification', '').strip()
    verified_only = request.args.get('verified_only', '').strip().lower() in ('1', 'true', 'yes')

    query = JobSeekerProfile.query.join(User).filter(User.is_active == True)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (JobSeekerProfile.first_name.ilike(search_pattern)) |
            (JobSeekerProfile.last_name.ilike(search_pattern)) |
            (JobSeekerProfile.headline.ilike(search_pattern))
        )

    if skill_filter:
        query = query.join(JobSeekerProfile.skills).filter(Skill.name.ilike(f"%{skill_filter}%"))

    if qualification_filter:
        query = query.join(JobSeekerProfile.education_entries).filter(
            (Education.degree.ilike(f"%{qualification_filter}%")) |
            (Education.field_of_study.ilike(f"%{qualification_filter}%"))
        )

    if verified_only:
        query = query.join(JobSeekerProfile.certificates).filter(Certificate.status == 'verified')

    profiles = query.distinct().order_by(JobSeekerProfile.created_at.desc()).all()

    # Pre-fetch all available skills and degrees for quick filter tags
    available_skills = [s[0] for s in Skill.query.with_entities(Skill.name).distinct().all()]
    available_degrees = [d[0] for d in Education.query.with_entities(Education.degree).distinct().all() if d[0]]

    return render_template(
        'candidates/directory.html',
        profiles=profiles,
        search=search,
        selected_skill=skill_filter,
        selected_qualification=qualification_filter,
        verified_only=verified_only,
        available_skills=available_skills,
        available_degrees=available_degrees
    )


@main_bp.route('/candidates/<int:profile_id>')
def candidate_public_profile(profile_id):
    """
    Displays candidate's public authorized profile showcasing verified credentials,
    education, skills, and experience without exposing raw private documents.
    """
    from flask import abort
    from app.models import JobSeekerProfile

    profile = JobSeekerProfile.query.get_or_404(profile_id)
    if not profile.user.is_active:
        abort(404, description="Candidate profile is currently unavailable.")

    verified_certs = profile.certificates.filter_by(status='verified').all()
    educations = profile.education_entries.all()
    skills = profile.skills.all()
    experiences = profile.work_experiences.all()
    projects = profile.projects.all()
    achievements = profile.achievements.all()

    return render_template(
        'candidates/detail.html',
        profile=profile,
        verified_certs=verified_certs,
        educations=educations,
        skills=skills,
        experiences=experiences,
        projects=projects,
        achievements=achievements
    )


def create_app(config_name: str | None = None) -> Flask:
    """
    Application Factory for Skill Resume Certificate Verification System.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, Config))

    # Ensure required directories exist
    os.makedirs(app.config['RESUME_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CERTIFICATE_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PICTURE_UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register global CSRF protection hook
    app.before_request(csrf_protect)

    # Register context processors
    @app.context_processor
    def inject_global_template_variables():
        unread_notifications = 0
        if current_user.is_authenticated:
            unread_notifications = current_user.notifications.filter_by(is_read=False).count()
        return {
            'csrf_token': generate_csrf_token,
            'current_year': datetime.utcnow().year,
            'app_name': 'Skill & Certificate Verification System',
            'unread_notifications_count': unread_notifications
        }

    # Register error handlers
    @app.errorhandler(400)
    def bad_request(error):
        description = getattr(error, 'description', 'Bad Request')
        return render_template('errors/400.html', description=description), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        max_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
        description = f"The uploaded file is too large. Maximum permitted size is {max_mb} MB."
        return render_template('errors/413.html', description=description), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500

    # Register Blueprints
    from app.auth import auth_bp
    from app.seeker import seeker_bp
    from app.admin import admin_bp
    from app.verification import verification_bp
    from app.reports import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(seeker_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(verification_bp)
    app.register_blueprint(reports_bp)

    # Register CLI Commands
    register_cli_commands(app)

    return app


def register_cli_commands(app: Flask):
    """Registers custom flask CLI commands."""

    @app.cli.command('init-db')
    def init_db_command():
        """Initialize and create all database tables."""
        from app.models import User  # Ensure models are imported
        with app.app_context():
            db.create_all()
            click.echo(click.style("[OK] Successfully created all database tables.", fg="green"))

    @app.cli.command('create-admin')
    @click.option('--username', default=None, help='Admin username')
    @click.option('--email', default=None, help='Admin email address')
    @click.option('--password', default=None, help='Admin password')
    def create_admin_command(username, email, password):
        """Creates an administrator account."""
        from app.models import User
        with app.app_context():
            username = username or os.environ.get('INITIAL_ADMIN_USERNAME') or click.prompt('Admin username')
            email = email or os.environ.get('INITIAL_ADMIN_EMAIL') or click.prompt('Admin email')
            password = password or os.environ.get('INITIAL_ADMIN_PASSWORD') or click.prompt('Admin password', hide_input=True)

            existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
            if existing_user:
                click.echo(click.style(f"Error: User with username '{username}' or email '{email}' already exists.", fg="red"))
                return

            admin = User(
                username=username,
                email=email,
                role='admin',
                is_active=True
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            click.echo(click.style(f"[OK] Admin user '{username}' successfully created!", fg="green"))
