"""Contact model."""

from datetime import datetime
from app.extensions import db


class Contact(db.Model):
    """Model for tracking contacts/connections at companies (recruiters, hiring managers, etc.)."""

    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_applications.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=True)  # Company name (for contacts not tied to an application)
    title = db.Column(db.String(255), nullable=True)  # Job title (e.g., "Recruiter", "Hiring Manager")
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    linkedin_url = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), default='manual')  # manual, email_scan
    email_subject = db.Column(db.String(500), nullable=True)  # Subject of email they responded with
    last_contact_date = db.Column(db.Date, nullable=True)  # When they last reached out
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name}>'

    def to_dict(self):
        """Convert model to dictionary."""
        # Get company from application if not set directly
        company_name = self.company
        if not company_name and self.application:
            company_name = self.application.company_name

        return {
            'id': self.id,
            'application_id': self.application_id,
            'name': self.name,
            'company': company_name,
            'title': self.title,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'notes': self.notes,
            'source': self.source,
            'email_subject': self.email_subject,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
