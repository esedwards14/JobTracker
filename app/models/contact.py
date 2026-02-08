"""Contact model."""

from datetime import datetime
from app.extensions import db


class Contact(db.Model):
    """Model for tracking contacts at companies."""

    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    linkedin_url = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name}>'

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'name': self.name,
            'title': self.title,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
