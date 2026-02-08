"""Database models."""

from app.models.application import JobApplication
from app.models.interview import InterviewStage
from app.models.contact import Contact
from app.models.tag import Tag, application_tags
from app.models.email_settings import EmailSettings, ParsedEmail

__all__ = [
    'JobApplication',
    'InterviewStage',
    'Contact',
    'Tag',
    'application_tags',
    'EmailSettings',
    'ParsedEmail',
]
