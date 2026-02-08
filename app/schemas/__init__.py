"""Marshmallow schemas for validation and serialization."""

from app.schemas.application import ApplicationSchema, ApplicationCreateSchema, ApplicationUpdateSchema
from app.schemas.interview import InterviewSchema, InterviewCreateSchema
from app.schemas.tag import TagSchema

__all__ = [
    'ApplicationSchema',
    'ApplicationCreateSchema',
    'ApplicationUpdateSchema',
    'InterviewSchema',
    'InterviewCreateSchema',
    'TagSchema',
]
