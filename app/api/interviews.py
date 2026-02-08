"""API endpoints for interview stages."""

from flask import request, jsonify
from marshmallow import ValidationError

from app.api import api_bp
from app.extensions import db
from app.models import JobApplication, InterviewStage
from app.schemas.interview import InterviewCreateSchema, InterviewUpdateSchema


@api_bp.route('/applications/<int:app_id>/interviews', methods=['GET'])
def list_interviews(app_id):
    """List all interviews for an application."""
    application = JobApplication.query.get_or_404(app_id)
    interviews = application.interviews.order_by(InterviewStage.stage_number).all()

    return jsonify({
        'interviews': [interview.to_dict() for interview in interviews]
    })


@api_bp.route('/applications/<int:app_id>/interviews', methods=['POST'])
def create_interview(app_id):
    """Add a new interview stage to an application."""
    application = JobApplication.query.get_or_404(app_id)
    schema = InterviewCreateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    interview = InterviewStage(application_id=app_id, **data)
    db.session.add(interview)

    # Update application status to interviewing if not already
    if application.status == 'applied':
        application.status = 'interviewing'
        if not application.response_received:
            application.response_received = True

    db.session.commit()

    return jsonify(interview.to_dict()), 201


@api_bp.route('/interviews/<int:id>', methods=['GET'])
def get_interview(id):
    """Get a single interview by ID."""
    interview = InterviewStage.query.get_or_404(id)
    return jsonify(interview.to_dict())


@api_bp.route('/interviews/<int:id>', methods=['PUT'])
def update_interview(id):
    """Update an interview stage."""
    interview = InterviewStage.query.get_or_404(id)
    schema = InterviewUpdateSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400

    for key, value in data.items():
        setattr(interview, key, value)

    db.session.commit()

    return jsonify(interview.to_dict())


@api_bp.route('/interviews/<int:id>', methods=['DELETE'])
def delete_interview(id):
    """Delete an interview stage."""
    interview = InterviewStage.query.get_or_404(id)
    db.session.delete(interview)
    db.session.commit()

    return jsonify({'message': 'Interview deleted successfully'}), 200
