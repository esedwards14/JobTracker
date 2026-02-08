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

    # Build query
    query = JobApplication.query

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
    application = JobApplication.query.get_or_404(id)
    return jsonify(application.to_dict())


@api_bp.route('/applications', methods=['POST'])
def create_application():
    """Create a new application."""
    schema = ApplicationCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    application = JobApplication(**data)
    db.session.add(application)
    db.session.commit()

    return jsonify(application.to_dict()), 201


@api_bp.route('/applications/<int:id>', methods=['PUT'])
def update_application(id):
    """Update an existing application."""
    application = JobApplication.query.get_or_404(id)
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
    application = JobApplication.query.get_or_404(id)

    data = request.json
    if data is None:
        data = {}

    application.notes = data.get('notes') or None
    db.session.commit()

    return jsonify(application.to_dict())


@api_bp.route('/applications/<int:id>/status', methods=['PATCH'])
def update_application_status(id):
    """Update only the status of an application."""
    application = JobApplication.query.get_or_404(id)

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
    application = JobApplication.query.get_or_404(id)
    db.session.delete(application)
    db.session.commit()

    # Return empty string for HTMX to remove the row
    if request.headers.get('HX-Request'):
        return '', 200

    return jsonify({'message': 'Application deleted successfully'}), 200


@api_bp.route('/applications/delete-all', methods=['DELETE'])
def delete_all_applications():
    """Delete all applications."""
    count = JobApplication.query.count()
    JobApplication.query.delete()
    db.session.commit()

    return jsonify({'message': f'Deleted {count} applications', 'deleted': count}), 200


@api_bp.route('/applications/<int:id>/tags/<int:tag_id>', methods=['POST'])
def add_tag_to_application(id, tag_id):
    """Add a tag to an application."""
    application = JobApplication.query.get_or_404(id)
    tag = Tag.query.get_or_404(tag_id)

    if tag not in application.tags:
        application.tags.append(tag)
        db.session.commit()

    return jsonify(application.to_dict())


@api_bp.route('/applications/<int:id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_application(id, tag_id):
    """Remove a tag from an application."""
    application = JobApplication.query.get_or_404(id)
    tag = Tag.query.get_or_404(tag_id)

    if tag in application.tags:
        application.tags.remove(tag)
        db.session.commit()

    return jsonify(application.to_dict())
