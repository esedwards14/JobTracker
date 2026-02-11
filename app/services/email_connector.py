"""Gmail connector using OAuth for fetching job application emails."""

import base64
import email
from datetime import datetime, timedelta
from typing import List, Optional
from email.utils import parsedate_to_datetime

from app.services.google_oauth import get_gmail_service, refresh_access_token


class GmailOAuthConnector:
    """Connect to Gmail via OAuth to fetch job-related emails."""

    def __init__(self, access_token: str, refresh_token: str):
        """
        Initialize Gmail connector with OAuth tokens.

        Args:
            access_token: Current access token
            refresh_token: Refresh token for getting new access tokens
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.service = None
        self.credentials = None

    def connect(self) -> 'GmailOAuthConnector':
        """Establish connection to Gmail API."""
        self.service, self.credentials = get_gmail_service(
            self.access_token,
            self.refresh_token
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

        # Broader search queries for job-related emails
        search_queries = [
            # Subject-based searches - application keywords
            f'after:{after_date} subject:application',
            f'after:{after_date} subject:"thank you for applying"',
            f'after:{after_date} subject:"thanks for applying"',
            f'after:{after_date} subject:"application received"',
            f'after:{after_date} subject:"application submitted"',
            f'after:{after_date} subject:"we received your application"',
            f'after:{after_date} subject:"your application"',
            f'after:{after_date} subject:"applied for"',
            f'after:{after_date} subject:"applying for"',
            f'after:{after_date} subject:"job application"',
            f'after:{after_date} subject:"application confirmation"',
            f'after:{after_date} subject:"thank you for your interest"',
            f'after:{after_date} subject:"thanks for your interest"',

            # Response/update keywords
            f'after:{after_date} subject:"application update"',
            f'after:{after_date} subject:"application status"',
            f'after:{after_date} subject:"regarding your application"',
            f'after:{after_date} subject:"update on your application"',
            f'after:{after_date} subject:"unfortunately"',
            f'after:{after_date} subject:"not moving forward"',
            f'after:{after_date} subject:"regret to inform"',
            f'after:{after_date} subject:"position has been filled"',

            # Interview keywords
            f'after:{after_date} subject:interview',
            f'after:{after_date} subject:"schedule a call"',
            f'after:{after_date} subject:"next steps"',
            f'after:{after_date} subject:"phone screen"',

            # Offer keywords
            f'after:{after_date} subject:"offer letter"',
            f'after:{after_date} subject:"job offer"',
            f'after:{after_date} subject:"offer of employment"',

            # Candidate/hiring keywords
            f'after:{after_date} subject:candidate',
            f'after:{after_date} subject:"hiring process"',
            f'after:{after_date} subject:"recruitment"',
            f'after:{after_date} subject:"position"',
            f'after:{after_date} subject:"opportunity"',

            # Platform-specific sender searches
            f'after:{after_date} from:indeed.com',
            f'after:{after_date} from:indeedemail.com',
            f'after:{after_date} from:linkedin.com',
            f'after:{after_date} from:jobalerts-noreply@linkedin.com',
            f'after:{after_date} from:messages-noreply@linkedin.com',
            f'after:{after_date} from:handshake.com',
            f'after:{after_date} from:joinhandshake.com',
            f'after:{after_date} from:greenhouse.io',
            f'after:{after_date} from:greenhouse-mail.io',
            f'after:{after_date} from:lever.co',
            f'after:{after_date} from:workday.com',
            f'after:{after_date} from:myworkdayjobs.com',
            f'after:{after_date} from:smartrecruiters.com',
            f'after:{after_date} from:icims.com',
            f'after:{after_date} from:jobvite.com',
            f'after:{after_date} from:applytojob.com',
            f'after:{after_date} from:taleo.net',
            f'after:{after_date} from:successfactors.com',
            f'after:{after_date} from:brassring.com',
            f'after:{after_date} from:ultipro.com',
            f'after:{after_date} from:ashbyhq.com',
            f'after:{after_date} from:paylocity.com',
            f'after:{after_date} from:paycom.com',
            f'after:{after_date} from:adp.com',
            f'after:{after_date} from:bamboohr.com',
            f'after:{after_date} from:ceridian.com',
            f'after:{after_date} from:phenom.com',
            f'after:{after_date} from:avature.net',
            f'after:{after_date} from:beamery.com',
            f'after:{after_date} from:eightfold.ai',
            f'after:{after_date} from:phenom.com',
            f'after:{after_date} from:glassdoor.com',
            f'after:{after_date} from:ziprecruiter.com',
            f'after:{after_date} from:monster.com',
            f'after:{after_date} from:careerbuilder.com',
            f'after:{after_date} from:dice.com',
            f'after:{after_date} from:simplyhired.com',
            f'after:{after_date} from:snagajob.com',
            f'after:{after_date} from:flexjobs.com',
            f'after:{after_date} from:roberthalf.com',
            f'after:{after_date} from:randstad.com',
            f'after:{after_date} from:manpower.com',
            f'after:{after_date} from:kellyservices.com',
            f'after:{after_date} from:adecco.com',

            # Common company career email patterns
            f'after:{after_date} from:careers@',
            f'after:{after_date} from:jobs@',
            f'after:{after_date} from:recruiting@',
            f'after:{after_date} from:talent@',
            f'after:{after_date} from:hr@',
            f'after:{after_date} from:hiring@',
            f'after:{after_date} from:recruitment@',
            f'after:{after_date} from:staffing@',
            f'after:{after_date} from:humanresources@',
            f'after:{after_date} from:noreply@ subject:application',
            f'after:{after_date} from:no-reply@ subject:application',
            f'after:{after_date} from:notifications@ subject:application',

            # Body content searches (catches more emails)
            f'after:{after_date} "thank you for applying"',
            f'after:{after_date} "we received your application"',
            f'after:{after_date} "application has been received"',
            f'after:{after_date} "your candidacy"',
            f'after:{after_date} "hiring team"',
            f'after:{after_date} "recruiting team"',
        ]

        emails = []
        seen_ids = set()

        for query in search_queries:
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=50
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
        try:
            from datetime import timezone
            aware_min = datetime.min.replace(tzinfo=timezone.utc)
            emails.sort(key=lambda x: x['date'] if x['date'] else aware_min, reverse=True)
        except Exception as e:
            print(f"Warning: Could not sort emails by date: {e}")
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
