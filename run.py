#!/usr/bin/env python3
"""Entry point for the Job Tracker application."""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=3000)
