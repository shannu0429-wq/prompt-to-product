from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='team_leader')  # 'team_leader', 'admin', 'super_admin'
    college = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    team = db.relationship('Team', back_populates='leader', uselist=False, cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='actor', lazy='dynamic')
    problem_statements = db.relationship('ProblemStatement', backref='author', lazy='dynamic')
    evaluations = db.relationship('Evaluation', backref='evaluator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    @property
    def is_admin(self):
        return self.role in ['admin', 'super_admin']

    @property
    def is_team_leader(self):
        return self.role == 'team_leader'

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"
