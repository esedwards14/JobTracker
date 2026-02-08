"""Views Blueprint registration."""

from flask import Blueprint

views_bp = Blueprint('views', __name__)

from app.views import main
