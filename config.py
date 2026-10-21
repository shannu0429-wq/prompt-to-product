import os
import urllib.parse
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


def _normalize_database_uri(url: str) -> str:
    """Normalize and sanitize cloud database connection strings (TiDB, Render, Neon, etc.)."""
    if not url:
        return url
    # Ensure pure-Python drivers are used in container environments
    if url.startswith('mysql+mysqldb://'):
        url = url.replace('mysql+mysqldb://', 'mysql+pymysql://', 1)
    elif url.startswith('mysql://'):
        url = url.replace('mysql://', 'mysql+pymysql://', 1)
    elif url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)

    parsed = urllib.parse.urlsplit(url)
    path = parsed.path
    # Automatically map default /sys or empty schema to prompt_to_product
    if path in ('/sys', '/sys/', '', '/'):
        path = '/prompt_to_product'

    if 'pymysql' in parsed.scheme:
        params = urllib.parse.parse_qs(parsed.query) if parsed.query else {}
        # Remove MySQLdb-specific options that break PyMySQL
        params.pop('ssl_mode', None)
        if '<CA_PATH>' in params.get('ssl_ca', [''])[0]:
            params.pop('ssl_ca', None)
        if 'tidbcloud.com' in parsed.netloc:
            # Enforce PyMySQL TLS verification on TiDB Cloud
            params['ssl_verify_cert'] = ['true']
        new_query = urllib.parse.urlencode({k: v[0] for k, v in params.items()})
        parsed = parsed._replace(path=path, query=new_query)
    else:
        parsed = parsed._replace(path=path)

    return urllib.parse.urlunsplit(parsed)


class Config:
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'p2p-dev-insecure-secret-key-change-in-production-2026')
    
    # Database configuration
    # Prefer explicit connection string if provided, otherwise assemble from individual params
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'prompt_to_product')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'admin')

    default_db_uri = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    raw_db_url = os.getenv('DATABASE_URL')
    if raw_db_url:
        SQLALCHEMY_DATABASE_URI = _normalize_database_uri(raw_db_url)
    elif os.getenv('RENDER') and MYSQL_HOST == 'localhost':
        # Render cloud environment fallback before external DATABASE_URL is added to environment
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'render_app.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = default_db_uri

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        **({'connect_args': {'ssl': {'check_hostname': False}}} if ('tidbcloud.com' in SQLALCHEMY_DATABASE_URI or 'ssl' in SQLALCHEMY_DATABASE_URI) else {})
    } if not SQLALCHEMY_DATABASE_URI.startswith('sqlite') else {}

    # Session and Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(days=2)
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200

    # Mail Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@ssrsgc.com')
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

    # App Settings
    PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL', 'http://127.0.0.1:5000')
    REGISTRATION_OPEN = os.getenv('REGISTRATION_OPEN', 'true').lower() == 'true'
    EMAIL_VERIFICATION_REQUIRED = os.getenv('EMAIL_VERIFICATION_REQUIRED', 'false').lower() == 'true'

    # File uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'images', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'webp', 'ico'}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
