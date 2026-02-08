"""Interview Stage model."""

from datetime import datetime
from app.extensions import db


class InterviewStage(db.Model):
    """Model for tracking interview stages."""

    __tablename__ = 'interview_stages'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=False)
    stage_number = db.Column(db.Integer, nullable=False)  # 1 = first interview, 2 = second, etc.
    stage_type = db.Column(db.String(100), nullable=True)  # phone_screen, technical, behavioral, onsite, final
    scheduled_date = db.Column(db.DateTime, nullable=True)
    completed_date = db.Column(db.DateTime, nullable=True)
    interviewer_names = db.Column(db.Text, nullable=True)  # Comma-separated
    notes = db.Column(db.Text, nullable=True)
    outcome = db.Column(db.String(50), nullable=True)  # passed, failed, pending, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<InterviewStage {self.stage_number} for Application {self.application_id}>'

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'stage_number': self.stage_number,
            'stage_type': self.stage_type,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'completed_date': self.completed_date.isoformat() if self.completed_date else None,
            'interviewer_names': self.interviewer_names,
            'notes': self.notes,
            'outcome': self.outcome,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
