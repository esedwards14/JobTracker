"""API endpoints for tags."""

from flask import request, jsonify
from marshmallow import ValidationError

from app.api import api_bp
from app.extensions import db
from app.models import Tag
from app.schemas import TagSchema


@api_bp.route('/tags', methods=['GET'])
def list_tags():
    """List all tags for current user."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    tags = Tag.query.filter_by(user_id=user_id).order_by(Tag.name).all()
    return jsonify({
        'tags': [tag.to_dict() for tag in tags]
    })


@api_bp.route('/tags', methods=['POST'])
def create_tag():
    """Create a new tag."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    schema = TagSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check if tag with same name exists for this user
    existing = Tag.query.filter_by(name=data['name'], user_id=user_id).first()
    if existing:
        return jsonify({'error': 'Tag with this name already exists'}), 400

    data['user_id'] = user_id
    tag = Tag(**data)
    db.session.add(tag)
    db.session.commit()

    return jsonify(tag.to_dict()), 201


@api_bp.route('/tags/<int:id>', methods=['PUT'])
def update_tag(id):
    """Update a tag."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    tag = Tag.query.filter_by(id=id, user_id=user_id).first_or_404()
    schema = TagSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Check if another tag with same name exists for this user
    existing = Tag.query.filter(Tag.name == data['name'], Tag.id != id, Tag.user_id == user_id).first()
    if existing:
        return jsonify({'error': 'Tag with this name already exists'}), 400

    for key, value in data.items():
        setattr(tag, key, value)

    db.session.commit()

    return jsonify(tag.to_dict())


@api_bp.route('/tags/<int:id>', methods=['DELETE'])
def delete_tag(id):
    """Delete a tag."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    tag = Tag.query.filter_by(id=id, user_id=user_id).first_or_404()
    db.session.delete(tag)
    db.session.commit()

    return jsonify({'message': 'Tag deleted successfully'}), 200
