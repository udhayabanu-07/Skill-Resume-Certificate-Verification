import os
from app import create_app
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
    VerificationRecord,
    Notification
)

# Create application instance using FLASK_ENV or default
app = create_app(os.environ.get('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Populates Flask interactive shell with database models."""
    return {
        'db': db,
        'User': User,
        'JobSeekerProfile': JobSeekerProfile,
        'Education': Education,
        'Skill': Skill,
        'WorkExperience': WorkExperience,
        'Project': Project,
        'Achievement': Achievement,
        'Resume': Resume,
        'Certificate': Certificate,
        'VerificationRecord': VerificationRecord,
        'Notification': Notification
    }


if __name__ == '__main__':
    # Running locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
