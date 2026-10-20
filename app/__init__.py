import os
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf, mail
from app.models.user import User


def create_app(config_name=None):
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Login loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Context processors for global template availability
    @app.context_processor
    def inject_global_data():
        from app.services.settings_service import SettingsService
        status_text, status_class = SettingsService.get_event_status()
        active_logo = SettingsService.get_active_logo()
        settings = SettingsService.get_all_settings()
        return {
            'site_settings': settings,
            'active_logo': active_logo,
            'event_status_text': status_text,
            'event_status_class': status_class,
            'current_year': datetime.now().year,
        }

    # Template filters for Indian Standard Time (IST: UTC+5:30)
    @app.template_filter('ist_datetime')
    def ist_datetime_filter(dt):
        if not dt:
            return 'N/A'
        if isinstance(dt, str):
            from app.services.settings_service import SettingsService
            parsed = SettingsService.parse_datetime(dt)
            if not parsed:
                return dt
            dt = parsed
        # Convert UTC to IST (+5:30)
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        # Assume dt is naive UTC
        dt_utc = dt.replace(tzinfo=timezone.utc)
        dt_ist = dt_utc.astimezone(ist_tz)
        return dt_ist.strftime('%d %b %Y, %I:%M %p IST')

    # Register Blueprints
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.registration import registration_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.submissions import submissions_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(admin_bp)

    # Custom Error Handlers
    @app.errorhandler(400)
    def bad_request_error(e):
        return render_template('errors/400.html', error=e), 400

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(429)
    def ratelimit_error(e):
        return render_template('errors/429.html', error=e), 429

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html', error=e), 500

    # CLI commands
    @app.cli.command("seed-data")
    def seed_data_cmd():
        from scripts.seed_data import run_seed
        run_seed()

    @app.cli.command("create-admin")
    def create_admin_cmd():
        from scripts.create_admin import run_create_admin
        run_create_admin()

    return app
