"""Schemas for Job Application validation."""

from marshmallow import Schema, fields, validate, post_load
from datetime import date


class ApplicationCreateSchema(Schema):
    """Schema for creating a new application."""

    company_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    position = fields.String(required=True, validate=validate.Length(min=1, max=255))
    expected_salary_min = fields.Decimal(places=2, allow_none=True)
    expected_salary_max = fields.Decimal(places=2, allow_none=True)
    salary_currency = fields.String(validate=validate.Length(max=3), load_default='USD')
    date_applied = fields.Date(load_default=None)
    application_url = fields.URL(allow_none=True)
    job_description = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    source = fields.String(
        validate=validate.OneOf(['manual', 'extension', 'email']),
        load_default='manual'
    )

    @post_load
    def set_defaults(self, data, **kwargs):
        """Set default values after loading."""
        if data.get('date_applied') is None:
            data['date_applied'] = date.today()
        return data


class ApplicationUpdateSchema(Schema):
    """Schema for updating an existing application."""

    company_name = fields.String(validate=validate.Length(min=1, max=255))
    position = fields.String(validate=validate.Length(min=1, max=255))
    expected_salary_min = fields.Decimal(places=2, allow_none=True)
    expected_salary_max = fields.Decimal(places=2, allow_none=True)
    salary_currency = fields.String(validate=validate.Length(max=3))
    date_applied = fields.Date()
    application_url = fields.URL(allow_none=True)
    job_description = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    source = fields.String(validate=validate.OneOf(['manual', 'extension', 'email']))
    status = fields.String(
        validate=validate.OneOf(['applied', 'interviewing', 'offered', 'rejected', 'withdrawn', 'follow_up'])
    )
    response_received = fields.Boolean()
    response_date = fields.Date(allow_none=True)


class ApplicationSchema(Schema):
    """Schema for serializing application data."""

    id = fields.Integer(dump_only=True)
    company_name = fields.String()
    position = fields.String()
    expected_salary_min = fields.Decimal(places=2, as_string=True)
    expected_salary_max = fields.Decimal(places=2, as_string=True)
    salary_currency = fields.String()
    date_applied = fields.Date()
    application_url = fields.String()
    job_description = fields.String()
    notes = fields.String()
    source = fields.String()
    status = fields.String()
    response_received = fields.Boolean()
    response_date = fields.Date()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
