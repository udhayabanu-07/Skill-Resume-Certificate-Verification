import os
import urllib.parse
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))


def get_database_uri() -> str:
    """
    Constructs the SQLAlchemy database URI based on environment variables.
    Supports:
    1. Direct DATABASE_URL if provided
    2. SQLite fallback if USE_SQLITE is True or MySQL credentials are unset
    3. MySQL via PyMySQL: mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
    """
    # 1. Direct DATABASE_URL override
    direct_url = os.environ.get('DATABASE_URL')
    if direct_url:
        return direct_url

    # 2. SQLite flag check
    use_sqlite = os.environ.get('USE_SQLITE', 'false').lower() in ('1', 'true', 'yes', 'on')
    instance_dir = os.path.join(BASE_DIR, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    sqlite_uri = f"sqlite:///{os.path.join(instance_dir, 'skill_verify.db')}"

    if use_sqlite:
        return sqlite_uri

    # 3. MySQL configuration
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '3306')
    db_name = os.environ.get('DB_NAME', 'skill_verify_db')

    # Safe quoting for passwords with special symbols (#, @, :, etc.)
    encoded_password = urllib.parse.quote_plus(db_password) if db_password else ''

    if encoded_password:
        user_pass = f"{db_user}:{encoded_password}"
    else:
        user_pass = db_user

    return f"mysql+pymysql://{user_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-insecure-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }

    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'uploads')
    RESUME_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
    CERTIFICATE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'certificates')
    PROFILE_PICTURE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # 16 MB

    # Allowed file types for security
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx', 'doc'}
    ALLOWED_CERTIFICATE_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/pjpeg',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }

    # Session and Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day in seconds


class DevelopmentConfig(Config):
    """Development environment specific configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment specific configuration."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production environment specific configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
