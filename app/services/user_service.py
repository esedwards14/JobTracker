"""User service for managing current user session."""

from flask import session


def get_current_user_id():
    """Get the current logged-in user's ID (email address).

    Returns:
        str or None: The user's email/ID if logged in, None otherwise.
    """
    return session.get('user_id')


def set_current_user(email):
    """Set the current user in the session.

    Args:
        email: The user's email address (used as user ID).
    """
    session['user_id'] = email
    session.permanent = True  # Make session persistent


def clear_current_user():
    """Clear the current user from the session (logout)."""
    session.pop('user_id', None)


def is_logged_in():
    """Check if a user is currently logged in.

    Returns:
        bool: True if a user is logged in, False otherwise.
    """
    return 'user_id' in session
