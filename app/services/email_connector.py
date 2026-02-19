"""Gmail connector using OAuth for fetching job application emails."""

import base64
import email
from datetime import datetime, timedelta
from typing import List, Optional
from email.utils import parsedate_to_datetime

from app.services.google_oauth import get_gmail_service, refresh_access_token


class GmailOAuthConnector:
    """Connect to Gmail via OAuth to fetch job-related emails."""

    def __init__(self, access_token: str, refresh_token: str, token_expiry=None):
        """
        Initialize Gmail connector with OAuth tokens.

        Args:
            access_token: Current access token
            refresh_token: Refresh token for getting new access tokens
            token_expiry: Token expiry datetime (optional, used for proactive refresh)
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = token_expiry
        self.service = None
        self.credentials = None

    def connect(self) -> 'GmailOAuthConnector':
        """Establish connection to Gmail API."""
        self.service, self.credentials = get_gmail_service(
            self.access_token,
            self.refresh_token,
            self.token_expiry
        )
        return self

    def get_updated_tokens(self):
        """Get updated tokens if they were refreshed."""
        if self.credentials:
            return {
                'access_token': self.credentials.token,
                'token_expiry': self.credentials.expiry
            }
        return None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # No cleanup needed for API client

    def fetch_job_emails(self, days_back: int = 30, limit: int = 200) -> List[dict]:
        """
        Fetch emails that look like job application confirmations.

        Args:
            days_back: How many days back to search
            limit: Maximum number of emails to return

        Returns:
            List of email dictionaries with subject, from, date, body
        """
        if not self.service:
            raise ConnectionError("Not connected. Call connect() first.")

        # Calculate date filter
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')

        # Optimized search queries - reduced to prevent server overload
        # Only 6 essential queries that catch most job emails
        search_queries = [
            # Main application keyword - catches most job emails
            f'after:{after_date} subject:application',
            # Interview-related
            f'after:{after_date} subject:interview',
            # Scheduling emails (Calendly, etc.) - catches direct recruiter scheduling
            f'after:{after_date} calendly.com OR goodtime.io OR subject:schedule',
            # Indeed (most common job platform)
            f'after:{after_date} from:indeed.com OR from:indeedemail.com',
            # LinkedIn
            f'after:{after_date} from:linkedin.com',
            # Common ATS platforms
            f'after:{after_date} from:greenhouse.io OR from:lever.co OR from:workday.com',
            # Career emails
            f'after:{after_date} from:careers@ OR from:jobs@',
        ]

        emails = []
        seen_ids = set()

        for query in search_queries:
            # Stop early if we have enough emails
            if len(emails) >= limit:
                break

            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=30  # Reduced from 50 to speed up queries
                ).execute()

                messages = results.get('messages', [])

                for msg_info in messages:
                    if msg_info['id'] in seen_ids:
                        continue

                    seen_ids.add(msg_info['id'])

                    try:
                        msg = self.service.users().messages().get(
                            userId='me',
                            id=msg_info['id'],
                            format='full'
                        ).execute()

                        parsed = self._parse_message(msg)
                        if parsed:
                            emails.append(parsed)

                        if len(emails) >= limit:
                            break

                    except Exception as e:
                        print(f"Error fetching message {msg_info['id']}: {e}")
                        continue

            except Exception as e:
                print(f"Error with query '{query}': {e}")
                continue

            if len(emails) >= limit:
                break

        # Sort by date descending (use a timezone-aware min date as fallback)
        from datetime import timezone
        aware_min = datetime.min.replace(tzinfo=timezone.utc)
        emails.sort(key=lambda x: x['date'] if x['date'] else aware_min, reverse=True)
        return emails[:limit]

    def fetch_recruiter_emails(self, days_back: int = 90, limit: int = 100) -> List[dict]:
        """
        Fetch emails from real people (recruiters, hiring managers) about jobs.
        Uses broader search queries than fetch_job_emails to find personal contacts.

        Args:
            days_back: How many days back to search
            limit: Maximum number of emails to return

        Returns:
            List of email dictionaries
        """
        if not self.service:
            raise ConnectionError("Not connected. Call connect() first.")

        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')

        # Queries specifically designed to find emails from real people (recruiters/HMs)
        # Exclude automated job platform emails to focus on personal contacts
        platform_exclusions = '-from:indeed.com -from:indeedemail.com -from:linkedin.com -from:greenhouse.io -from:lever.co -from:workday.com -from:icims.com -from:smartrecruiters.com -from:workable.com -from:jobvite.com -from:taleo.net -from:ashbyhq.com -from:bamboohr.com -from:noreply'

        search_queries = [
            # Scheduling tool links — strongest signal of personal recruiter contact
            f'after:{after_date} calendly.com',
            f'after:{after_date} goodtime.io',
            # Interview emails from company domains (not platforms)
            f'after:{after_date} subject:interview {platform_exclusions}',
            # Direct recruiter outreach about opportunities
            f'after:{after_date} (subject:opportunity OR subject:"open role" OR subject:"new role") {platform_exclusions}',
            # "I came across your profile" / "reaching out" type emails
            f'after:{after_date} ("reaching out" OR "came across your") {platform_exclusions}',
            # Application update emails from company HR directly
            f'after:{after_date} subject:"your application" {platform_exclusions}',
        ]

        emails = []
        seen_ids = set()

        for query in search_queries:
            if len(emails) >= limit:
                break

            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=25
                ).execute()

                messages = results.get('messages', [])

                for msg_info in messages:
                    if msg_info['id'] in seen_ids:
                        continue
                    seen_ids.add(msg_info['id'])

                    try:
                        msg = self.service.users().messages().get(
                            userId='me',
                            id=msg_info['id'],
                            format='full'
                        ).execute()

                        parsed = self._parse_message(msg)
                        if parsed:
                            emails.append(parsed)

                        if len(emails) >= limit:
                            break

                    except Exception as e:
                        print(f"Error fetching recruiter message {msg_info['id']}: {e}")
                        continue

            except Exception as e:
                print(f"Error with recruiter query '{query}': {e}")
                continue

        from datetime import timezone
        aware_min = datetime.min.replace(tzinfo=timezone.utc)
        emails.sort(key=lambda x: x['date'] if x['date'] else aware_min, reverse=True)
        return emails[:limit]

    def _parse_message(self, msg: dict) -> Optional[dict]:
        """Parse a Gmail API message into a dictionary."""
        try:
            headers = {h['name'].lower(): h['value'] for h in msg['payload']['headers']}

            # Get subject
            subject = headers.get('subject', '')

            # Get from address
            from_header = headers.get('from', '')

            # Get date - handle various formats, always return timezone-aware
            date_str = headers.get('date', '')
            msg_date = None
            if date_str:
                try:
                    msg_date = parsedate_to_datetime(date_str)
                except Exception:
                    # Try alternative parsing for malformed dates
                    try:
                        from dateutil import parser as dateutil_parser
                        msg_date = dateutil_parser.parse(date_str)
                    except Exception:
                        # Last resort: extract just the date portion
                        import re
                        date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', date_str)
                        if date_match:
                            try:
                                from dateutil import parser as dateutil_parser
                                msg_date = dateutil_parser.parse(date_match.group(1))
                            except Exception:
                                msg_date = None

                # Ensure all dates are timezone-aware to prevent comparison errors
                if msg_date and msg_date.tzinfo is None:
                    from datetime import timezone
                    msg_date = msg_date.replace(tzinfo=timezone.utc)

            # Get body text
            body_text = self._get_body_text(msg['payload'])

            return {
                'message_id': msg['id'],
                'subject': subject,
                'from_address': from_header,
                'to_address': headers.get('to', ''),
                'date': msg_date,
                'body_text': body_text,
                'body_preview': body_text[:500] if body_text else '',
            }

        except Exception as e:
            print(f"Error parsing message: {e}")
            return None

    def _get_body_text(self, payload: dict) -> str:
        """Extract text body from message payload (plain text preferred, HTML as fallback)."""
        plain_text = ''
        html_text = ''

        if 'body' in payload and payload['body'].get('data'):
            content = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            mime_type = payload.get('mimeType', '')
            if mime_type == 'text/plain':
                plain_text = content
            elif mime_type == 'text/html':
                html_text = content
            else:
                plain_text = content

        elif 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')

                if mime_type == 'text/plain' and part.get('body', {}).get('data'):
                    plain_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')

                elif mime_type == 'text/html' and part.get('body', {}).get('data'):
                    html_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')

                elif mime_type.startswith('multipart/'):
                    nested = self._get_body_text(part)
                    if nested and not plain_text:
                        plain_text = nested

        # Prefer plain text, but extract from HTML if needed
        if plain_text:
            return plain_text
        elif html_text:
            return self._html_to_text(html_text)
        return ''

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text, preserving important content."""
        import re

        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Replace common block elements with newlines
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?(?:p|div|tr|li|h[1-6])[^>]*>', '\n', text, flags=re.IGNORECASE)

        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")

        # Clean up whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)

        return text.strip()

    def test_connection(self) -> bool:
        """Test if the OAuth connection works."""
        try:
            self.connect()
            # Try to get profile info
            profile = self.service.users().getProfile(userId='me').execute()
            return bool(profile.get('emailAddress'))
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
