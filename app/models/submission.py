from datetime import datetime
from app.extensions import db


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    website_url = db.Column(db.String(500), nullable=False)
    project_description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='submitted')  # 'submitted', 'under_review', 'shortlisted', 'rejected'
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = db.relationship('Team', back_populates='submission')
    history = db.relationship('SubmissionHistory', backref='submission', cascade='all, delete-orphan', order_by='SubmissionHistory.changed_at.desc()')
    evaluation = db.relationship('Evaluation', back_populates='submission', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Submission {self.submission_id} (Team {self.team_id})>"


class SubmissionHistory(db.Model):
    __tablename__ = 'submission_history'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False, index=True)
    website_url = db.Column(db.String(500), nullable=False)
    project_description = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    change_type = db.Column(db.String(50), nullable=False)  # 'initial_submission', 'user_edit', 'admin_edit', 'reopened_submission'
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    editor = db.relationship('User', foreign_keys=[changed_by])

    def __repr__(self):
        return f"<SubmissionHistory {self.id} for Submission {self.submission_id}>"
