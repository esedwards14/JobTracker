"""API endpoints for contacts/connections."""

from flask import request, jsonify
from app.api import api_bp
from app.extensions import db
from app.models import Contact, JobApplication


@api_bp.route('/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts/connections."""
    # Optional filtering
    source = request.args.get('source')  # 'manual', 'email_scan'
    company = request.args.get('company')

    query = Contact.query

    if source:
        query = query.filter(Contact.source == source)
    if company:
        query = query.filter(Contact.company.ilike(f'%{company}%'))

    # Order by most recent first
    contacts = query.order_by(Contact.created_at.desc()).all()

    return jsonify({
        'contacts': [c.to_dict() for c in contacts],
        'total': len(contacts)
    })


@api_bp.route('/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get a single contact."""
    contact = Contact.query.get_or_404(contact_id)
    return jsonify(contact.to_dict())


@api_bp.route('/contacts', methods=['POST'])
def create_contact():
    """Create a new contact."""
    data = request.get_json() or {}

    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400

    contact = Contact(
        name=data.get('name'),
        company=data.get('company'),
        title=data.get('title'),
        email=data.get('email'),
        phone=data.get('phone'),
        linkedin_url=data.get('linkedin_url'),
        notes=data.get('notes'),
        source=data.get('source', 'manual'),
        application_id=data.get('application_id')
    )

    db.session.add(contact)
    db.session.commit()

    return jsonify(contact.to_dict()), 201


@api_bp.route('/contacts/<int:contact_id>', methods=['PATCH'])
def update_contact(contact_id):
    """Update a contact."""
    contact = Contact.query.get_or_404(contact_id)
    data = request.get_json() or {}

    # Update fields
    if 'name' in data:
        contact.name = data['name']
    if 'company' in data:
        contact.company = data['company']
    if 'title' in data:
        contact.title = data['title']
    if 'email' in data:
        contact.email = data['email']
    if 'phone' in data:
        contact.phone = data['phone']
    if 'linkedin_url' in data:
        contact.linkedin_url = data['linkedin_url']
    if 'notes' in data:
        contact.notes = data['notes']
    if 'application_id' in data:
        contact.application_id = data['application_id']

    db.session.commit()

    return jsonify(contact.to_dict())


@api_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete a contact."""
    contact = Contact.query.get_or_404(contact_id)

    db.session.delete(contact)
    db.session.commit()

    return jsonify({'message': 'Contact deleted successfully'})


@api_bp.route('/applications/<int:app_id>/contacts', methods=['GET'])
def get_application_contacts(app_id):
    """Get all contacts for a specific application."""
    application = JobApplication.query.get_or_404(app_id)
    contacts = Contact.query.filter_by(application_id=app_id).all()

    return jsonify({
        'contacts': [c.to_dict() for c in contacts],
        'total': len(contacts)
    })
