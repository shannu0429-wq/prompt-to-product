from datetime import datetime
from app.extensions import db


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    team_name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    leader_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    team_size = db.Column(db.Integer, nullable=False, default=1)
    registration_status = db.Column(db.String(50), nullable=False, default='registered')  # 'registered', 'verified', 'under_review', 'suspended'
    allow_edit = db.Column(db.Boolean, default=False)
    allow_resubmit = db.Column(db.Boolean, default=False)
    internal_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    leader = db.relationship('User', back_populates='team')
    members = db.relationship('TeamMember', back_populates='team', cascade='all, delete-orphan', order_by='TeamMember.is_leader.desc(), TeamMember.id.asc()')
    submission = db.relationship('Submission', back_populates='team', uselist=False, cascade='all, delete-orphan')
    result = db.relationship('Result', back_populates='team', uselist=False, cascade='all, delete-orphan')

    @property
    def has_submitted(self):
        return self.submission is not None

    def __repr__(self):
        return f"<Team {self.registration_id}: {self.team_name}>"


class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(191), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    is_leader = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = db.relationship('Team', back_populates='members')

    def __repr__(self):
        return f"<TeamMember {self.full_name} ({self.email})>"
