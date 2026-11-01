from flask import Blueprint

seeker_bp = Blueprint('seeker', __name__, url_prefix='/seeker')

from app.seeker import routes  # noqa: E402, F401
