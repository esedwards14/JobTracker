"""Application factory for Job Tracker."""

import os
from flask import Flask
from config import config


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    from app.extensions import db, migrate, cors
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from app.api import api_bp
    from app.views import views_bp

    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(views_bp)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

        # One-time cleanup: strip email subjects from imported application notes
        try:
            from app.models import JobApplication
            updated = JobApplication.query.filter(
                JobApplication.notes.like('Imported from email:%'),
                JobApplication.notes != 'Imported from email'
            ).update(
                {JobApplication.notes: 'Imported from email'},
                synchronize_session=False
            )
            updated += JobApplication.query.filter(
                JobApplication.notes.like('Created from response email:%')
            ).update(
                {JobApplication.notes: 'Imported from email'},
                synchronize_session=False
            )
            if updated:
                db.session.commit()
        except Exception:
            db.session.rollback()

    return app
