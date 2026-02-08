"""Email settings and parsed email models."""

from datetime import datetime
from app.extensions import db


class EmailSettings(db.Model):
    """Store email connection settings using OAuth tokens (no passwords stored)."""

    __tablename__ = 'email_settings'

    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(50), default='gmail')
    is_active = db.Column(db.Boolean, default=True)
    last_sync = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # OAuth tokens (encrypted in production)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email_address': self.email_address,
            'provider': self.provider,
            'is_active': self.is_active,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_connected': bool(self.refresh_token),
        }


class ParsedEmail(db.Model):
    """Store parsed job application emails."""

    __tablename__ = 'parsed_emails'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(255), unique=True, nullable=False)
    email_subject = db.Column(db.Text)
    email_from = db.Column(db.String(255))
    email_date = db.Column(db.DateTime)
    body_preview = db.Column(db.Text)

    # Extracted data
    company_name = db.Column(db.String(255))
    position = db.Column(db.String(255))
    platform = db.Column(db.String(50))
    confidence = db.Column(db.Float)

    # Status
    status = db.Column(db.String(50), default='pending')  # pending, imported, ignored
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    application = db.relationship('JobApplication', backref='source_email')

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'email_subject': self.email_subject,
            'email_from': self.email_from,
            'email_date': self.email_date.isoformat() if self.email_date else None,
            'body_preview': self.body_preview,
            'company_name': self.company_name,
            'position': self.position,
            'platform': self.platform,
            'confidence': self.confidence,
            'status': self.status,
            'application_id': self.application_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
