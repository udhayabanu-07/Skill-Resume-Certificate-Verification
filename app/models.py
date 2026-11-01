from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    User account model supporting job seekers and administrative reviewers.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='job_seeker')  # 'job_seeker', 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    profile = db.relationship('JobSeekerProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')
    verified_certificates = db.relationship('Certificate', foreign_keys='Certificate.verified_by_id', backref='verifier_user', lazy='dynamic')
    verification_actions = db.relationship('VerificationRecord', foreign_keys='VerificationRecord.admin_id', backref='admin_user', lazy='dynamic')

    def set_password(self, password: str) -> None:
        """Hashes and sets the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        """Returns True if the user has an admin role."""
        return self.role == 'admin'

    @property
    def is_job_seeker(self) -> bool:
        """Returns True if the user has a job seeker role."""
        return self.role == 'job_seeker'

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"


class JobSeekerProfile(db.Model):
    """
    Detailed profile information for a job seeker.
    """
    __tablename__ = 'job_seeker_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    headline = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    state = db.Column(db.String(64), nullable=True)
    country = db.Column(db.String(64), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    career_objective = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    education_entries = db.relationship('Education', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='Education.end_date.desc()')
    skills = db.relationship('Skill', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='Skill.name.asc()')
    work_experiences = db.relationship('WorkExperience', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='WorkExperience.start_date.desc()')
    projects = db.relationship('Project', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='Project.created_at.desc()')
    achievements = db.relationship('Achievement', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='Achievement.created_at.desc()')
    resumes = db.relationship('Resume', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='Resume.uploaded_at.desc()')
    certificates = db.relationship('Certificate', backref='profile', lazy='dynamic', cascade='all, delete-orphan', order_by='Certificate.uploaded_at.desc()')

    @property
    def full_name(self) -> str:
        """Returns the full name of the job seeker."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def effective_objective(self) -> str:
        """Returns career objective or bio as fallback."""
        return self.career_objective or self.bio or ""

    @property
    def profile_completion_percentage(self) -> int:
        """Calculates dynamic profile completion percentage (0 - 100%)."""
        score = 0
        if self.first_name and self.last_name:
            score += 10
        if self.phone:
            score += 5
        if self.city or self.country or self.address:
            score += 5
        if self.date_of_birth:
            score += 5
        if self.headline:
            score += 5
        if self.career_objective or self.bio:
            score += 10
        if self.profile_picture:
            score += 10
        if self.linkedin_url or self.github_url or self.portfolio_url:
            score += 10
        if self.education_entries.count() > 0:
            score += 10
        skill_cnt = self.skills.count()
        if skill_cnt >= 2:
            score += 10
        elif skill_cnt == 1:
            score += 5
        if self.work_experiences.count() > 0 or self.projects.count() > 0:
            score += 10
        if self.certificates.count() > 0 or self.resumes.count() > 0:
            score += 10
        return min(100, score)

    def __repr__(self) -> str:
        return f"<JobSeekerProfile id={self.id} user_id={self.user_id} name='{self.full_name}'>"


class Project(db.Model):
    """
    Key projects completed by the job seeker for portfolio and resume showcase.
    """
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    technologies = db.Column(db.String(255), nullable=True)
    project_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Project id={self.id} title='{self.title}'>"


class Achievement(db.Model):
    """
    Honors, awards, or competitive achievements for the job seeker's resume.
    """
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_achieved = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Achievement id={self.id} title='{self.title}'>"


class Education(db.Model):
    """
    Educational background and qualifications of a job seeker.
    """
    __tablename__ = 'educations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    institution = db.Column(db.String(150), nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    field_of_study = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    grade_or_cgpa = db.Column(db.String(30), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Education id={self.id} degree='{self.degree}' institution='{self.institution}'>"


class Skill(db.Model):
    """
    Skills claimed by the job seeker, with proficiency level and verification status.
    """
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), default='technical', nullable=False)  # 'technical', 'soft'
    proficiency_level = db.Column(db.String(20), default='intermediate', nullable=False)  # beginner, intermediate, advanced, expert
    years_of_experience = db.Column(db.Float, default=0.0, nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    certificate = db.relationship('Certificate', backref='linked_skills', foreign_keys=[certificate_id])

    def __repr__(self) -> str:
        return f"<Skill id={self.id} name='{self.name}' verified={self.is_verified}>"


class WorkExperience(db.Model):
    """
    Work experience record for a job seeker.
    """
    __tablename__ = 'work_experiences'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    company = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<WorkExperience id={self.id} title='{self.job_title}' company='{self.company}'>"


class Resume(db.Model):
    """
    Uploaded resume documents and parsed summaries.
    """
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    parsed_text = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Resume id={self.id} file='{self.original_filename}'>"


class Certificate(db.Model):
    """
    Uploaded certificates requiring human-in-the-loop review.
    Does not automatically approve certificates.
    """
    __tablename__ = 'certificates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('job_seeker_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    credential_id = db.Column(db.String(100), nullable=True)
    credential_url = db.Column(db.String(500), nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'verified', 'rejected'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Relationships
    verification_records = db.relationship('VerificationRecord', backref='certificate', lazy='dynamic', cascade='all, delete-orphan', order_by='VerificationRecord.created_at.desc()')

    def __repr__(self) -> str:
        return f"<Certificate id={self.id} title='{self.title}' status='{self.status}'>"


class VerificationRecord(db.Model):
    """
    Audit log of actions performed by administrators when reviewing certificates.
    """
    __tablename__ = 'verification_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id', ondelete='CASCADE'), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(20), nullable=False)  # 'verified', 'rejected', 'in_review'
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<VerificationRecord id={self.id} cert_id={self.certificate_id} action='{self.action}'>"


class Notification(db.Model):
    """
    In-app notifications for users regarding verification updates and system alerts.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(30), default='info', nullable=False)  # 'info', 'success', 'warning', 'danger'
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} title='{self.title}' read={self.is_read}>"
