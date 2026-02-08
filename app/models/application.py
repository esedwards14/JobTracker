"""Job Application model."""

from datetime import datetime, date
from app.extensions import db


class JobApplication(db.Model):
    """Model for tracking job applications."""

    __tablename__ = 'job_applications'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    expected_salary_min = db.Column(db.Numeric(12, 2), nullable=True)
    expected_salary_max = db.Column(db.Numeric(12, 2), nullable=True)
    salary_currency = db.Column(db.String(3), default='USD')
    date_applied = db.Column(db.Date, nullable=False, default=date.today)
    application_url = db.Column(db.Text, nullable=True)
    job_description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), default='manual')  # manual, extension, email
    status = db.Column(db.String(50), default='applied')  # applied, interviewing, offered, rejected, withdrawn
    response_received = db.Column(db.Boolean, default=False)
    response_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    interviews = db.relationship(
        'InterviewStage',
        backref='application',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    contacts = db.relationship(
        'Contact',
        backref='application',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    tags = db.relationship(
        'Tag',
        secondary='application_tags',
        backref=db.backref('applications', lazy='dynamic')
    )

    def __repr__(self):
        return f'<JobApplication {self.company_name} - {self.position}>'

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'position': self.position,
            'expected_salary_min': float(self.expected_salary_min) if self.expected_salary_min else None,
            'expected_salary_max': float(self.expected_salary_max) if self.expected_salary_max else None,
            'salary_currency': self.salary_currency,
            'date_applied': self.date_applied.isoformat() if self.date_applied else None,
            'application_url': self.application_url,
            'job_description': self.job_description,
            'notes': self.notes,
            'source': self.source,
            'status': self.status,
            'response_received': self.response_received,
            'response_date': self.response_date.isoformat() if self.response_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'interviews': [i.to_dict() for i in self.interviews],
            'tags': [t.to_dict() for t in self.tags],
        }
