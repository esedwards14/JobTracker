"""Google OAuth service for Gmail access."""

import os
import json
from datetime import datetime, timedelta
from flask import url_for, current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Gmail API scope for reading emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_client_config():
    """Get OAuth client configuration from environment or file."""
    # Check for environment variables first
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

    if client_id and client_secret:
        return {
            'web': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': ['http://127.0.0.1:3000/oauth/callback'],
            }
        }

    # Fall back to credentials file
    creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    if os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            return json.load(f)

    return None


def create_oauth_flow(redirect_uri=None):
    """Create OAuth flow for Google sign-in."""
    client_config = get_client_config()
    if not client_config:
        raise ValueError(
            "Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
            "environment variables, or provide a credentials.json file."
        )

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri or 'http://127.0.0.1:3000/oauth/callback'
    )

    return flow


def get_authorization_url():
    """Get the Google OAuth authorization URL."""
    flow = create_oauth_flow()

    # Do not include previously granted scopes here; that can cause
    # Google to request extra scopes (redirect_uri_mismatch / scope changes).
    # Keep access_type and prompt so we still receive a refresh token.
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Get refresh token
        include_granted_scopes=False,
        prompt='consent'  # Force consent to get refresh token
    )

    return authorization_url, state


def exchange_code_for_tokens(authorization_code):
    """Exchange authorization code for access and refresh tokens."""
    flow = create_oauth_flow()
    flow.fetch_token(code=authorization_code)

    credentials = flow.credentials

    return {
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_expiry': credentials.expiry,
        'email': get_user_email(credentials)
    }


def get_user_email(credentials):
    """Get the user's email address from their Google profile."""
    # First try: Gmail profile (works with only gmail.readonly)
    try:
        gmail_service = build('gmail', 'v1', credentials=credentials)
        profile = gmail_service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        if email:
            return email
    except Exception as e:
        current_app.logger.debug(f"Gmail profile lookup failed: {e}")

    # Second try: oauth2 userinfo (requires email/openid scope)
    try:
        oauth2_service = build('oauth2', 'v2', credentials=credentials)
        user_info = oauth2_service.userinfo().get().execute()
        email = user_info.get('email')
        if email:
            return email
    except Exception as e:
        current_app.logger.debug(f"OAuth2 userinfo lookup failed: {e}")

    # Final fallback: try to extract from ID token payload if present
    try:
        if hasattr(credentials, 'id_token') and credentials.id_token:
            import json
            import base64
            parts = credentials.id_token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                padding = 4 - (len(payload) % 4)
                if padding != 4:
                    payload += '=' * padding
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                if 'email' in token_data:
                    return token_data['email']
    except Exception as e:
        current_app.logger.debug(f"ID token extraction failed: {e}")

    return None


def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    client_config = get_client_config()
    if not client_config:
        raise ValueError("Google OAuth not configured")

    web_config = client_config.get('web', client_config.get('installed', {}))

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=web_config['client_id'],
        client_secret=web_config['client_secret']
    )

    credentials.refresh(Request())

    return {
        'access_token': credentials.token,
        'token_expiry': credentials.expiry
    }


def get_gmail_service(access_token, refresh_token):
    """Get an authenticated Gmail API service."""
    client_config = get_client_config()
    web_config = client_config.get('web', client_config.get('installed', {}))

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=web_config['client_id'],
        client_secret=web_config['client_secret'],
        scopes=SCOPES
    )

    # Refresh if expired
    if credentials.expired:
        credentials.refresh(Request())

    service = build('gmail', 'v1', credentials=credentials)
    return service, credentials
