"""API endpoints for job applications."""

from flask import request, jsonify
from marshmallow import ValidationError
from sqlalchemy import or_
from datetime import datetime

from app.api import api_bp
from app.extensions import db
from app.models import JobApplication, Tag
from app.schemas import ApplicationSchema, ApplicationCreateSchema, ApplicationUpdateSchema


@api_bp.route('/applications', methods=['GET'])
def list_applications():
    """List all applications with optional filters."""
    from app.services.user_service import get_current_user_id

    # Query parameters
    status = request.args.get('status')
    company = request.args.get('company')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    response_received = request.args.get('response_received')
    sort_by = request.args.get('sort_by', 'date_applied')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Build query - filter by current user
    user_id = get_current_user_id()
    query = JobApplication.query.filter_by(user_id=user_id)

    # Apply filters
    if status:
        statuses = status.split(',')
        query = query.filter(JobApplication.status.in_(statuses))

    if company:
        query = query.filter(JobApplication.company_name.ilike(f'%{company}%'))

    if from_date:
        query = query.filter(JobApplication.date_applied >= from_date)

    if to_date:
        query = query.filter(JobApplication.date_applied <= to_date)

    if response_received is not None:
        query = query.filter(JobApplication.response_received == (response_received.lower() == 'true'))

    # Apply sorting
    sort_column = getattr(JobApplication, sort_by, JobApplication.date_applied)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'applications': [app.to_dict() for app in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
    })


@api_bp.route('/applications/<int:id>', methods=['GET'])
def get_application(id):
    """Get a single application by ID."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()
    return jsonify(application.to_dict())


@api_bp.route('/applications', methods=['POST'])
def create_application():
    """Create a new application."""
    from app.services.user_service import get_current_user_id

    schema = ApplicationCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    # Add current user ID
    data['user_id'] = get_current_user_id()

    application = JobApplication(**data)
    db.session.add(application)
    db.session.commit()

    return jsonify(application.to_dict()), 201


@api_bp.route('/applications/<int:id>', methods=['PUT'])
def update_application(id):
    """Update an existing application."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()
    schema = ApplicationUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    for key, value in data.items():
        setattr(application, key, value)

    db.session.commit()

    return jsonify(application.to_dict())


@api_bp.route('/applications/<int:id>/notes', methods=['PATCH'])
def update_application_notes(id):
    """Update only the notes of an application."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()

    data = request.json
    if data is None:
        data = {}

    application.notes = data.get('notes') or None
    db.session.commit()

    return jsonify(application.to_dict())


@api_bp.route('/applications/<int:id>/status', methods=['PATCH'])
def update_application_status(id):
    """Update only the status of an application."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()

    data = request.json
    if 'status' not in data:
        return jsonify({'error': 'status field is required'}), 400

    valid_statuses = ['applied', 'interviewing', 'offered', 'rejected', 'withdrawn', 'follow_up']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    application.status = data['status']

    # Auto-update related fields based on status
    if data['status'] == 'interviewing' and not application.response_received:
        application.response_received = True
        application.response_date = datetime.utcnow().date()

    db.session.commit()

    return jsonify(application.to_dict())


@api_bp.route('/applications/<int:id>', methods=['DELETE'])
def delete_application(id):
    """Delete an application."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()
    db.session.delete(application)
    db.session.commit()

    # Return empty string for HTMX to remove the row
    if request.headers.get('HX-Request'):
        return '', 200

    return jsonify({'message': 'Application deleted successfully'}), 200


@api_bp.route('/applications/delete-all', methods=['DELETE'])
def delete_all_applications():
    """Delete all applications for current user."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    count = JobApplication.query.filter_by(user_id=user_id).count()
    JobApplication.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    return jsonify({'message': f'Deleted {count} applications', 'deleted': count}), 200


@api_bp.route('/applications/bulk/delete', methods=['POST'])
def bulk_delete_applications():
    """Delete multiple applications by ID."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()

    data = request.json
    if not data or 'ids' not in data or not isinstance(data['ids'], list):
        return jsonify({'error': 'ids field is required and must be a list'}), 400

    ids = data['ids']
    if len(ids) > 500:
        return jsonify({'error': 'Cannot delete more than 500 applications at once'}), 400

    count = JobApplication.query.filter(
        JobApplication.id.in_(ids),
        JobApplication.user_id == user_id
    ).delete(synchronize_session=False)
    db.session.commit()

    return jsonify({'message': f'Deleted {count} applications', 'deleted': count}), 200


@api_bp.route('/applications/bulk/status', methods=['PATCH'])
def bulk_update_status():
    """Update status for multiple applications."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()

    data = request.json
    if not data or 'ids' not in data or 'status' not in data:
        return jsonify({'error': 'ids and status fields are required'}), 400

    valid_statuses = ['applied', 'interviewing', 'offered', 'rejected', 'withdrawn', 'follow_up']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    ids = data['ids']
    if len(ids) > 500:
        return jsonify({'error': 'Cannot update more than 500 applications at once'}), 400

    applications = JobApplication.query.filter(
        JobApplication.id.in_(ids),
        JobApplication.user_id == user_id
    ).all()

    for app in applications:
        app.status = data['status']
        if data['status'] == 'interviewing' and not app.response_received:
            app.response_received = True
            app.response_date = datetime.utcnow().date()

    db.session.commit()

    return jsonify({'message': f'Updated {len(applications)} applications', 'updated': len(applications)}), 200


@api_bp.route('/applications/bulk/tags', methods=['POST'])
def bulk_add_tags():
    """Add tags to multiple applications."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()

    data = request.json
    if not data or 'ids' not in data or 'tag_ids' not in data:
        return jsonify({'error': 'ids and tag_ids fields are required'}), 400

    ids = data['ids']
    tag_ids = data['tag_ids']

    if len(ids) > 500:
        return jsonify({'error': 'Cannot update more than 500 applications at once'}), 400

    applications = JobApplication.query.filter(
        JobApplication.id.in_(ids),
        JobApplication.user_id == user_id
    ).all()

    tags = Tag.query.filter(
        Tag.id.in_(tag_ids),
        Tag.user_id == user_id
    ).all()

    if not tags:
        return jsonify({'error': 'No valid tags found'}), 400

    count = 0
    for app in applications:
        for tag in tags:
            if tag not in app.tags:
                app.tags.append(tag)
                count += 1

    db.session.commit()

    return jsonify({
        'message': f'Added tags to {len(applications)} applications',
        'updated': len(applications),
        'tags_added': count
    }), 200


@api_bp.route('/applications/<int:id>/tags/<int:tag_id>', methods=['POST'])
def add_tag_to_application(id, tag_id):
    """Add a tag to an application."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first_or_404()

    if tag not in application.tags:
        application.tags.append(tag)
        db.session.commit()

    return jsonify(application.to_dict())


@api_bp.route('/applications/<int:id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_application(id, tag_id):
    """Remove a tag from an application."""
    from app.services.user_service import get_current_user_id
    user_id = get_current_user_id()
    application = JobApplication.query.filter_by(id=id, user_id=user_id).first_or_404()
    tag = Tag.query.filter_by(id=tag_id, user_id=user_id).first_or_404()

    if tag in application.tags:
        application.tags.remove(tag)
        db.session.commit()

    return jsonify(application.to_dict())
