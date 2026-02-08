"""Schemas for Interview Stage validation."""

from marshmallow import Schema, fields, validate


class InterviewCreateSchema(Schema):
    """Schema for creating a new interview stage."""

    stage_number = fields.Integer(required=True, validate=validate.Range(min=1))
    stage_type = fields.String(
        validate=validate.OneOf(['phone_screen', 'technical', 'behavioral', 'onsite', 'final', 'other']),
        allow_none=True
    )
    scheduled_date = fields.DateTime(allow_none=True)
    interviewer_names = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)


class InterviewUpdateSchema(Schema):
    """Schema for updating an interview stage."""

    stage_number = fields.Integer(validate=validate.Range(min=1))
    stage_type = fields.String(
        validate=validate.OneOf(['phone_screen', 'technical', 'behavioral', 'onsite', 'final', 'other']),
        allow_none=True
    )
    scheduled_date = fields.DateTime(allow_none=True)
    completed_date = fields.DateTime(allow_none=True)
    interviewer_names = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    outcome = fields.String(
        validate=validate.OneOf(['passed', 'failed', 'pending', 'cancelled']),
        allow_none=True
    )


class InterviewSchema(Schema):
    """Schema for serializing interview data."""

    id = fields.Integer(dump_only=True)
    application_id = fields.Integer()
    stage_number = fields.Integer()
    stage_type = fields.String()
    scheduled_date = fields.DateTime()
    completed_date = fields.DateTime()
    interviewer_names = fields.String()
    notes = fields.String()
    outcome = fields.String()
    created_at = fields.DateTime(dump_only=True)
