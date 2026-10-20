from datetime import datetime
from app.extensions import db


class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    score_functionality = db.Column(db.Float, default=0.0, nullable=False)
    score_innovation = db.Column(db.Float, default=0.0, nullable=False)
    score_prompt_engineering = db.Column(db.Float, default=0.0, nullable=False)
    score_ui_ux = db.Column(db.Float, default=0.0, nullable=False)
    score_real_world_impact = db.Column(db.Float, default=0.0, nullable=False)
    score_code_quality = db.Column(db.Float, default=0.0, nullable=False)
    total_score = db.Column(db.Float, default=0.0, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    is_finalized = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submission = db.relationship('Submission', back_populates='evaluation')

    def calculate_total(self):
        self.total_score = round(
            float(self.score_functionality or 0) +
            float(self.score_innovation or 0) +
            float(self.score_prompt_engineering or 0) +
            float(self.score_ui_ux or 0) +
            float(self.score_real_world_impact or 0) +
            float(self.score_code_quality or 0),
            2
        )
        return self.total_score

    def __repr__(self):
        return f"<Evaluation for Submission {self.submission_id}: {self.total_score}/60>"


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    rank = db.Column(db.Integer, nullable=False)
    is_top_three = db.Column(db.Boolean, default=False, nullable=False)
    special_award = db.Column(db.String(150), nullable=True)  # e.g., "Winner", "1st Runner-Up", "2nd Runner-Up"
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = db.relationship('Team', back_populates='result')

    def __repr__(self):
        return f"<Result Rank {self.rank}: Team {self.team_id} (Published: {self.is_published})>"
