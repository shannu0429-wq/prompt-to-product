from app.routes.public import public_bp
from app.routes.auth import auth_bp
from app.routes.registration import registration_bp
from app.routes.dashboard import dashboard_bp
from app.routes.submissions import submissions_bp
from app.routes.admin import admin_bp

__all__ = [
    'public_bp',
    'auth_bp',
    'registration_bp',
    'dashboard_bp',
    'submissions_bp',
    'admin_bp',
]
