"""Schemas for Tag validation."""

from marshmallow import Schema, fields, validate


class TagSchema(Schema):
    """Schema for tag data."""

    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    color = fields.String(validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$'), load_default='#6B7280')
