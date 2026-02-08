"""API Blueprint registration."""

from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import applications, interviews, dashboard, tags, email, contacts
