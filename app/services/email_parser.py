"""Parse job application confirmation emails to extract application data."""

import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime


class JobEmailParser:
    """Parse job confirmation emails from various platforms."""

    # Universal patterns that work across many email formats
    # These are tried in order - more specific patterns first
    UNIVERSAL_COMPANY_PATTERNS = [
        # Explicit body patterns FIRST (more reliable than ambiguous subject patterns)
        # "application with Company" (very explicit - prioritize this)
        r'application with\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\.|!|,)',

        # Subject line patterns - BE CAREFUL: "application to X" is ambiguous
        # "Thanks for Applying to Company!" (subject line with exclamation)
        r'^[Tt]hanks for [Aa]pplying to\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:!|\.?\s*$)',
        # "Thank You For Your Interest in Company!"
        r'[Ii]nterest in\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:!|\s*$)',
        # "Company Application Update:" or "Company: Application"
        r'^([A-Z][A-Za-z0-9\s&\-\.]+?)\s+Application\s+(?:Update|Status|Confirmation)',
        # "Application to Company" or "Application at Company" - AMBIGUOUS, keep later
        r'[Aa]pplication\s+(?:to|at|for .+? at)\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:!|\.|\s*$)',
        # "application was sent to Company"
        r'application was sent to\s+([A-Z][A-Za-z0-9\s&\-\.\',]+?)(?:\s*$|!)',
        # "application was viewed by Company"
        r'application was viewed by\s+([A-Z][A-Za-z0-9\s&\-\.\',]+?)(?:\s*$|!)',
        # "Position @ Company" or "Position at Company"
        r'@\s*([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\s*$|!)',
        r'\s+at\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\s*$|!|\.)',
        # "from Company" at end
        r'from\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\s*$|!)',

        # Additional body patterns
        # "Thanks for your interest in Company"
        r'(?:thanks|thank you) for (?:your )?interest in\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\.|!|,|\s+We)',
        # "Thank you for applying to Company"
        r'(?:thanks|thank you) for (?:applying|your application) (?:to|at)\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\.|!)',
        # "application to Company has been"
        r'application (?:to|at|with)\s+([A-Z][A-Za-z0-9\s&\-\.]+?)\s+(?:has been|was|is)',
        # "applied to Company"
        r'(?:you )?applied (?:to|at)\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\.|!|\s+on|\s+for)',
        # "Your application to Company"
        r'[Yy]our application to\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\s+has|\.|!)',
        # "received your application...at/to Company"
        r'received your application.*?(?:at|to)\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\.|!)',
        # "Company - City, State" format (common in Indeed)
        r'\n\s*([A-Z][A-Za-z0-9\s&\-\.\',]+?)\s+-\s+[A-Z][a-z]+,?\s+[A-Z]{2}(?:\s+\d{5})?',
        # "at Company for the Position"
        r'at\s+([A-Z][A-Za-z0-9\s&\-\.]+?)\s+for\s+(?:the\s+)?',
        # "Company is hiring" or "Company has received"
        r'([A-Z][A-Za-z0-9\s&\-\.]+?)\s+(?:is hiring|has received|received your)',
        # "joining Company" or "working at Company"
        r'(?:joining|working at|working for)\s+([A-Z][A-Za-z0-9\s&\-\.]+?)(?:\.|!|,)',
    ]

    # Subject-only position patterns (should NOT be used on body)
    SUBJECT_POSITION_PATTERNS = [
        # "Indeed Application: Position"
        r'Indeed Application:\s*(.+?)(?:\s*@|\s*$)',
        # "Application Update: Position"
        r'Application\s+(?:Update|Status|Confirmation):\s*(.+?)(?:\s*$)',
        # "Position @ Company" - get position before @
        r'^(.+?)\s*@\s*[A-Z]',
        # "Position at Company" - get position before "at"
        r'^(.+?)\s+at\s+[A-Z]',
        # "Position - Location at Company"
        r'^(.+?)\s+-\s+[A-Z][a-z]+',
        # "Applying to Position"
        r'[Aa]pplying to\s+(.+?)(?:\s+-\s+|\s+at\s+|\s*$)',
    ]

    # Body position patterns (work on both subject and body)
    BODY_POSITION_PATTERNS = [
        # "for the following role(s): Position" (common in ATS emails) - PRIORITY
        r'(?:following role|following position|following job)(?:\(s\))?:\s*\n?\s*(.+?)(?:\s*\(|\n|$)',
        # "position of Position" (e.g., "applying for the position of Account Coordinator")
        r'position of\s+([A-Z][A-Za-z0-9\s\-/]+?)(?:\.|,|!|\s+at|\s+with|\n)',
        # "interest in the Position position/role"
        r'interest in (?:the\s+)?(?!following)(.+?)\s+(?:position|role|opportunity)',
        # "applying to the Position position/role"
        r'applying to (?:the\s+)?(?!following)(.+?)\s+(?:position|role)',
    ]

    # Platform-specific domains for detection
    PLATFORM_DOMAINS = {
        'indeed': ['indeed.com', 'indeedemail.com', 'indeedapply'],
        'linkedin': ['linkedin.com', 'linkedin.email', 'e.linkedin.com'],
        'handshake': ['handshake.com', 'joinhandshake.com', 'm.joinhandshake.com'],
        'greenhouse': ['greenhouse.io', 'greenhouse-mail.io'],
        'lever': ['lever.co', 'hire.lever.co'],
        'workday': ['workday.com', 'myworkdayjobs.com'],
        'icims': ['icims.com'],
        'smartrecruiters': ['smartrecruiters.com'],
        'workable': ['workablemail.com', 'workable.com'],
        'jobvite': ['jobvite.com'],
        'taleo': ['taleo.net', 'taleo.com'],
        'ashby': ['ashbyhq.com'],
        'bamboohr': ['bamboohr.com'],
        'jazz': ['jazz.co', 'applytojob.com'],
        'breezy': ['breezy.hr'],
        'recruiterbox': ['recruiterbox.com'],
        'zoho': ['zoho.com', 'zohorecruit.com'],
    }

    def __init__(self):
        """Initialize the parser."""
        pass

    def detect_platform(self, from_address: str, subject: str) -> str:
        """Detect which job platform the email is from."""
        from_lower = from_address.lower()

        for platform, domains in self.PLATFORM_DOMAINS.items():
            for domain in domains:
                if domain in from_lower:
                    return platform

        return 'generic'

    def parse_email(self, email_data: dict) -> dict:
        """
        Parse an email and extract job application data.

        Args:
            email_data: Dictionary with subject, from_address, body_text, date

        Returns:
            Dictionary with extracted data and confidence score
        """
        subject = email_data.get('subject', '')
        from_address = email_data.get('from_address', '')
        body = email_data.get('body_text', '')
        date = email_data.get('date')

        # Detect platform
        platform = self.detect_platform(from_address, subject)

        # Try to extract company and position
        company = self._extract_company(subject, body, from_address)
        position = self._extract_position(subject, body)

        # Calculate confidence
        confidence = self._calculate_confidence(company, position, platform)

        # Determine if this looks like a job application email
        is_job_email = self._is_job_application_email(subject, body, from_address)

        return {
            'company_name': company,
            'position': position,
            'platform': platform,
            'confidence': confidence,
            'is_job_email': is_job_email,
            'date_applied': date.date() if date else None,
            'email_subject': subject,
            'email_from': from_address,
            'email_date': date,
        }

    # Explicit body patterns that are more reliable than ambiguous subject patterns
    EXPLICIT_BODY_COMPANY_PATTERNS = [
        r'application with\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\.|!|,)',
        r'(?:thanks|thank you) for (?:your )?interest in\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\.|!|,|\s+We)',
    ]

    def _extract_company(self, subject: str, body: str, from_address: str) -> Optional[str]:
        """Extract company name from email using universal patterns."""

        # FIRST: Check explicit body patterns that are very reliable
        # These patterns like "application with Company" are unambiguous
        for pattern in self.EXPLICIT_BODY_COMPANY_PATTERNS:
            match = re.search(pattern, body[:3000], re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                company = self._clean_company_name(company)
                if company and len(company) > 1 and len(company) < 100:
                    if self._looks_like_company_name(company):
                        return company

        # Try patterns on subject - this gets explicit company mentions
        for pattern in self.UNIVERSAL_COMPANY_PATTERNS:
            match = re.search(pattern, subject, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                company = self._clean_company_name(company)
                if company and len(company) > 1 and len(company) < 100:
                    if self._looks_like_company_name(company):
                        return company

        # Next, try to get company from sender name (e.g., "Company Name <email@domain.com>")
        # Handle quoted sender names like '"Company @ Platform" <email>'
        sender_match = re.match(r'^"?([^"<]+?)"?\s*<', from_address)
        if sender_match:
            sender_name = sender_match.group(1).strip()
            # Remove quotes
            sender_name = sender_name.strip('"\'')

            # If sender name contains @ (like "TEKsystems @ icims"), extract the first part
            if ' @ ' in sender_name:
                sender_name = sender_name.split(' @ ')[0].strip()

            # Exclude generic sender names and job platforms
            skip_names = ['indeed', 'linkedin', 'indeed apply', 'linkedin jobs', 'noreply',
                         'no-reply', 'jobs', 'careers', 'recruiting', 'talent', 'hr',
                         'notifications', 'alerts', 'updates', 'candidates', 'workable',
                         'greenhouse', 'lever', 'icims', 'smartrecruiters', 'handshake',
                         'jobvite', 'taleo', 'ashby', 'bamboohr', 'zoho', 'breezy', 'jazz',
                         'glassdoor', 'ziprecruiter', 'monster', 'careerbuilder']
            # Also check for platform names within the sender name
            platform_keywords = ['indeed', 'linkedin', 'greenhouse', 'lever', 'workday',
                                'icims', 'smartrecruiters', 'workable', 'handshake', 'jobvite',
                                'taleo', 'ashby', 'bamboohr', 'zoho', 'adobe', 'acrobat',
                                'glassdoor', 'ziprecruiter', 'monster', 'careerbuilder']
            sender_lower = sender_name.lower().strip()
            if sender_lower not in skip_names and len(sender_name) > 2:
                if not any(p in sender_lower for p in platform_keywords):
                    cleaned = self._clean_company_name(sender_name)
                    if cleaned and self._looks_like_company_name(cleaned):
                        return cleaned

        # Try patterns on body (subject already checked above)
        for pattern in self.UNIVERSAL_COMPANY_PATTERNS:
            match = re.search(pattern, body[:5000], re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                company = self._clean_company_name(company)
                if company and len(company) > 1 and len(company) < 100:
                    # Verify it looks like a company name
                    if self._looks_like_company_name(company):
                        return company

        # Last resort: extract from email domain
        return self._extract_company_from_domain(from_address)

    def _extract_position(self, subject: str, body: str) -> Optional[str]:
        """Extract position/job title from email using universal patterns."""

        # Try subject-only patterns on subject first
        for pattern in self.SUBJECT_POSITION_PATTERNS:
            match = re.search(pattern, subject, re.IGNORECASE | re.MULTILINE)
            if match:
                position = match.group(1).strip()
                position = self._clean_position_name(position)
                if position and len(position) > 2 and len(position) < 150:
                    if self._looks_like_position(position):
                        return position

        # Try body patterns on both subject and body
        for text in [subject, body[:3000]]:
            for pattern in self.BODY_POSITION_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    position = match.group(1).strip()
                    position = self._clean_position_name(position)
                    if position and len(position) > 2 and len(position) < 150:
                        if self._looks_like_position(position):
                            return position

        return None

    def _looks_like_company_name(self, text: str) -> bool:
        """Check if text looks like a valid company name."""
        if not text:
            return False

        # Reject if too short or too long
        if len(text) < 2 or len(text) > 80:
            return False

        text_lower = text.lower().strip()

        # Reject common generic names and job platform names
        generic_names = [
            'indeed', 'linkedin', 'hr team', 'recruiting', 'talent', 'careers',
            'indeed apply', 'indeed job', 'linkedin jobs', 'glassdoor',
            'ziprecruiter', 'monster', 'careerbuilder', 'handshake',
            'greenhouse', 'lever', 'workday', 'icims', 'smartrecruiters',
            'workable', 'jobvite', 'taleo', 'ashby', 'bamboohr', 'zoho',
            'breezy', 'jazz', 'recruiterbox', 'adobe acrobat sign',
            'noreply', 'no-reply', 'notifications', 'alerts', 'updates',
            'human resources', 'hr', 'adobesign', 'adobe sign',
        ]
        if text_lower in generic_names:
            return False

        # Reject if it looks like a job title (common position keywords)
        position_keywords = [
            'manager', 'director', 'coordinator', 'specialist', 'analyst',
            'engineer', 'developer', 'designer', 'intern', 'associate',
            'executive', 'representative', 'lead', 'senior', 'junior',
            'administrator', 'assistant', 'consultant', 'advisor', 'recruiter',
        ]
        words = text_lower.split()
        # If it contains position keywords AND no typical company suffixes, might be a position
        if any(kw in text_lower for kw in position_keywords):
            company_indicators = ['inc', 'llc', 'ltd', 'corp', 'group', 'solutions',
                                 'services', 'consulting', 'technologies', 'systems']
            if not any(ind in text_lower for ind in company_indicators):
                # Likely a position, not a company
                return False

        # Reject if looks like a person name (First Last format with no company indicators)
        # Person names are typically 2-3 words, each capitalized, no special chars
        if len(words) == 2 or len(words) == 3:
            # Check if all words look like names (capitalized, letters only)
            all_name_like = all(
                len(w) > 1 and w[0].isupper() and w[1:].islower() and w.isalpha()
                for w in words
            )
            company_indicators = ['inc', 'llc', 'ltd', 'corp', 'group', 'solutions',
                                 'services', 'consulting', 'technologies', 'systems',
                                 'company', 'studio', 'media', 'digital', 'agency',
                                 'recruiting', 'staffing', 'partners', 'associates',
                                 'fitness', 'clubs', 'pirates', 'phillies', 'energy',
                                 'college', 'university', 'hospital', 'medical']
            has_company_word = any(ind in text_lower for ind in company_indicators)
            if all_name_like and not has_company_word:
                # Very likely a person name
                return False

        # Reject incomplete sentences or fragments
        fragment_patterns = [
            r'^llc\.',  # Starting with LLC
            r'we have',
            r'we are',
            r'in the meantime',
            r'please',
            r'thank you',
        ]
        for pattern in fragment_patterns:
            if re.search(pattern, text_lower):
                return False

        # Also reject if the name starts with or is primarily a platform name
        platform_prefixes = ['indeed', 'linkedin', 'glassdoor', 'handshake']
        for prefix in platform_prefixes:
            if text_lower.startswith(prefix):
                return False

        # Reject if it looks like a sentence or contains bad patterns
        bad_patterns = [
            r'following job',
            r'has been',
            r'was received',
            r'thank you',
            r'thanks for',
            r'we received',
            r'your application',
            r'the position',
            r'this email',
            r'click here',
            r'log in',
            r'http',
            r'www\.',
            r'was intended',
            r'on \w+,',  # "On Wed," etc - email reply headers
            r'^\d{1,2}:\d{2}',  # Time stamps
            r'hr team',
            r'recruiting team',
            r'talent team',
            r'intended for',
            r'apply now',
            r'view job',
            r'see all jobs',
        ]
        for pattern in bad_patterns:
            if re.search(pattern, text_lower):
                return False

        # Should start with a capital letter or number
        if not re.match(r'^[A-Z0-9]', text):
            return False

        return True

    def _looks_like_position(self, text: str) -> bool:
        """Check if text looks like a valid job position."""
        if not text:
            return False

        # Reject if too short or too long
        if len(text) < 3 or len(text) > 100:
            return False

        # Reject if it looks like a company or contains bad patterns
        bad_patterns = [
            r'^the\s',
            r'http',
            r'www\.',
            r'click here',
            r'@',
            r'\.com',
            r'you signed',
            r'review documents',
            r'thanks for applying',
            r'thank you for',
            r'on \w+,',  # "On Wed," etc
            r'this email',
            r'was intended',
            r'universal energy',  # Company name, not position
            r'to ensure',
            r'continue receiving',
            r'please add',
            r'just want to make sure',
            r'you can check',
            r'status of your',
            r'if you have any questions',
            r'hiring process',
            r'\[image:',  # Image placeholders
            r'^>',  # Email reply markers
            r'^>>',
            r'^\d{3}[\.\-]',  # Phone numbers
            r'email:',
            r'phone:',
            r'^from:',
            r'was sent to',
            r'in the meantime',
            r'^of\s+',  # "of PR Intern" - missing prefix
            r'we\'ll also',
            r'we will',
            r'you\'ve taken',
            r'first step',
            r'here$',  # "Associate here" - missing context
            r'^our\s+',  # "our Customer Marketing" - starts with "our"
            r'your application',
            r'your recent',
            r'be considered',
            r'training program',
            r'one of our',
        ]

        # Position keywords - if text contains these, it's likely a position
        position_keywords = ['intern', 'manager', 'director', 'engineer', 'developer',
                            'analyst', 'specialist', 'coordinator', 'assistant', 'associate',
                            'representative', 'recruiter', 'designer', 'planner', 'lead',
                            'executive', 'administrator', 'consultant', 'advisor', 'officer',
                            'estimator', 'technician', 'operator', 'supervisor', 'trainer']
        text_lower = text.lower()
        has_position_keyword = any(kw in text_lower for kw in position_keywords)

        # If it has a position keyword, it's likely a valid position - accept it
        if has_position_keyword:
            return True

        # Reject if it looks like a company name (not a position)
        company_only_patterns = [
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+$',  # "David Yurman" - two capitalized words only
            r'^WebFX$',
            r'^[A-Z][A-Za-z]+FX$',  # Names ending in FX
            r'^Indeed$',  # Platform name
            r'^Phillies$',  # Team name without position context
            r'^FanDuel$',  # Company name
        ]
        for pattern in company_only_patterns:
            if re.match(pattern, text):
                return False

        # Reject if it's a person's name pattern (First Last or First.Last)
        if re.match(r'^[A-Z][a-z]+\.[A-Z][a-z]+$', text):  # "Breese.McIlvaine"
            return False

        # Single capitalized word without position keyword is likely a company
        words = text.split()
        if len(words) == 1 and text[0].isupper():
            return False
        text_lower = text.lower()
        for pattern in bad_patterns:
            if re.search(pattern, text_lower):
                return False

        return True

    def _clean_company_name(self, company: str) -> str:
        """Clean up extracted company name."""
        if not company:
            return ''

        # Remove URLs and email artifacts
        company = re.sub(r'\s*\[?https?://[^\s\]]*\]?', '', company)
        company = re.sub(r'<[^>]+>', '', company).strip()

        # Remove common suffixes
        company = re.sub(r'\s*(?:Inc\.?|LLC\.?|Ltd\.?|Corp\.?|Corporation|Company|Co\.?)?\s*$', '', company, flags=re.IGNORECASE)
        company = re.sub(r'^\s*(?:the\s+)?', '', company, flags=re.IGNORECASE)
        company = re.sub(r'\s+', ' ', company).strip()

        # Remove trailing punctuation
        company = company.rstrip('.,!?:;-')

        # Remove leading punctuation
        company = company.lstrip('.,!?:;-')

        return company.strip()

    def _clean_position_name(self, position: str) -> str:
        """Clean up extracted position name."""
        if not position:
            return ''

        position = re.sub(r'\s+', ' ', position).strip()
        position = position.rstrip('.,!?:;-')
        position = position.lstrip('.,!?:;-')

        # Remove common noise phrases
        noise_phrases = ['position', 'role', 'opportunity', 'job', 'the']
        for phrase in noise_phrases:
            position = re.sub(rf'^{phrase}\s+', '', position, flags=re.IGNORECASE)
            position = re.sub(rf'\s+{phrase}$', '', position, flags=re.IGNORECASE)

        return position.strip()

    def _extract_company_from_domain(self, from_address: str) -> Optional[str]:
        """Extract company name from email domain as last resort."""
        # Skip known job platform domains
        skip_domains = ['indeed', 'linkedin', 'handshake', 'greenhouse', 'lever',
                       'workday', 'gmail', 'outlook', 'yahoo', 'hotmail', 'icims',
                       'smartrecruiters', 'jobvite', 'taleo', 'noreply', 'no-reply',
                       'notifications', 'mail', 'email', 'e', 'workable', 'bamboohr',
                       'zoho', 'breezy', 'jazz', 'ashby', 'recruiterbox', 'candidates']

        # Try to get domain from email
        match = re.search(r'@([^.>]+)', from_address)
        if match:
            domain = match.group(1).lower()
            if domain not in skip_domains and len(domain) > 2:
                # Capitalize and return
                return domain.replace('-', ' ').replace('_', ' ').title()

        return None

    def _calculate_confidence(self, company: Optional[str], position: Optional[str], platform: str) -> float:
        """Calculate confidence score for the extraction."""
        score = 0.0

        if company:
            score += 0.4
        if position:
            score += 0.4
        if platform != 'generic':
            score += 0.2
        elif company or position:
            score += 0.1

        return min(score, 1.0)

    def _is_job_application_email(self, subject: str, body: str, from_address: str) -> bool:
        """Determine if this email is likely a job application confirmation."""
        text = (subject + ' ' + body[:2000]).lower()
        subject_lower = subject.lower()
        from_lower = from_address.lower()

        # Reject email thread replies (Re:, RE:, Fwd:, etc.)
        if re.match(r'^(re:|fw:|fwd:)\s*', subject_lower):
            return False

        # Reject emails from personal email addresses (gmail, yahoo, outlook, etc.)
        # These are typically follow-up conversations, not automated confirmations
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                          'aol.com', 'icloud.com', 'me.com', 'live.com', 'msn.com']
        for domain in personal_domains:
            if domain in from_lower:
                return False

        # Check if from a known job platform
        is_from_job_platform = any(
            domain in from_lower
            for domains in self.PLATFORM_DOMAINS.values()
            for domain in domains
        )

        # Check if from careers/jobs email
        is_from_careers_email = any(x in from_lower for x in [
            'careers@', 'jobs@', 'recruiting@', 'talent@', 'hr@', 'hiring@',
            'recruitment@', 'staffing@', 'humanresources@', 'people@',
            'talentacquisition@', 'employment@'
        ])

        # Positive indicators - application confirmations and responses
        positive_keywords = [
            'application received',
            'application submitted',
            'application has been submitted',
            'thank you for applying',
            'thanks for applying',
            'application confirmation',
            'we received your application',
            'your application has been',
            'your application was',
            'application for',
            'applied for',
            'applying for',
            'thank you for your interest',
            'thanks for your interest',
            'job application',
            'you applied',
            'we have received your',
            'submitted your application',
            'applying to',
            'application to',
            'successfully submitted',
            'successfully applied',
            # Additional keywords for various job emails
            'your candidacy',
            'candidate',
            'hiring process',
            'recruitment process',
            'hiring team',
            'recruiting team',
            'talent team',
            'hr team',
            'human resources',
            'position you applied',
            'role you applied',
            'career opportunity',
            'job opportunity',
            'employment opportunity',
            'we appreciate your interest',
            'thank you for submitting',
            'your resume',
            'your qualifications',
            'interview',
            'next steps',
            'move forward',
        ]

        # Negative indicators (things that should NOT be imported as new applications)
        # These are responses, not application confirmations
        negative_keywords = [
            'your account',
            'password reset',
            'verify your email',
            'confirm your email',
            'subscription',
            'unsubscribe',
            'newsletter',
            'weekly digest',
            'daily digest',
        ]

        # Job match/recommendation keywords (check in SUBJECT LINE only)
        job_match_keywords = [
            'jobs matching',
            'job match',
            'jobs for you',
            'recommended jobs',
            'jobs you might be interested',
            'jobs you may be interested',
            'new jobs for',
            'jobs based on',
            'similar jobs',
            'jobs like',
            'job alert',
            'job alerts',
            'jobs in your area',
            'new jobs',
            'top job picks',
            'job recommendations',
            'recommended for you',
            'jobs we think',
            'personalized jobs',
            'daily job digest',
            'weekly job digest',
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in text)
        negative_count = sum(1 for kw in negative_keywords if kw in text)

        # Check for job match keywords in subject line only
        job_match_count = sum(1 for kw in job_match_keywords if kw in subject_lower)

        # If subject contains job match keywords, it's a recommendation email - reject
        if job_match_count > 0:
            return False

        # If too many negative keywords, reject
        if negative_count >= 2:
            return False

        # Must have at least one positive keyword indicating application confirmation
        if positive_count == 0:
            return False

        # If from a job platform or careers email, and has positive keywords, accept
        if is_from_job_platform or is_from_careers_email:
            return True

        # For generic emails, require positive keywords
        return positive_count > 0

    def parse_multiple(self, emails: List[dict]) -> List[dict]:
        """Parse multiple emails and return results."""
        results = []
        for email in emails:
            try:
                parsed = self.parse_email(email)
                parsed['message_id'] = email.get('message_id')
                parsed['body_preview'] = email.get('body_preview', '')[:300]
                results.append(parsed)
            except Exception as e:
                print(f"Error parsing email: {e}")
                continue

        # Filter to only job application emails and sort by confidence
        results = [r for r in results if r['is_job_email']]
        results.sort(key=lambda x: (x['confidence'], x['email_date'] or datetime.min), reverse=True)

        return results

    # ==================== RESPONSE EMAIL DETECTION ====================

    # Rejection patterns
    REJECTION_PATTERNS = [
        r'unfortunately',
        r'regret to inform',
        r'not (be )?moving forward',
        r'not selected',
        r'not (been )?chosen',
        r'decided not to proceed',
        r'will not be (proceeding|continuing)',
        r'position has been filled',
        r'role has been filled',
        r'pursuing other candidates',
        r'other candidates more closely',
        r'decided to (pursue|move forward with) other',
        r'not the right fit',
        r'not a (good )?match',
        r'we (have|\'ve) decided to go',
        r'gone with another candidate',
        r'won\'t be advancing',
        r'unable to offer',
        r'not able to offer',
        r'will not be offering',
        r'your application (was|has been) unsuccessful',
        r'thank you for your interest.{0,50}however',
        r'we (appreciate|thank).{0,50}but.{0,50}(not|won\'t|decided)',
        r'after careful (consideration|review).{0,100}(not|decided|unfortunately)',
    ]

    # Interview request patterns
    INTERVIEW_PATTERNS = [
        r'schedule (an? )?(phone |video |virtual |in-person )?interview',
        r'interview (with|at|for)',
        r'like to (invite|schedule)',
        r'invit(e|ing) you (to|for).{0,30}interview',
        r'would you be available.{0,50}(call|chat|interview|meet)',
        r'set up (a |an )?(time|call|meeting|interview)',
        r'book (a |an )?(time|slot|interview)',
        r'next (step|stage|round)',
        r'move(d|ing)? (forward|to the next)',
        r'proceed(ing)? (to|with).{0,20}(interview|next)',
        r'pleased to (invite|inform|let you know)',
        r'excited to (invite|inform|move)',
        r'like to (speak|talk|chat|meet) with you',
        r'calendly\.com',
        r'doodle\.com',
        r'goodtime\.io',
        r'pick a time',
        r'select a time',
        r'choose a time',
        r'availability.{0,30}(interview|call|chat|meeting)',
        r'when.{0,20}available.{0,30}(talk|call|chat|meet|interview)',
    ]

    # Offer patterns
    OFFER_PATTERNS = [
        r'offer (letter|of employment)',
        r'(pleased|happy|excited) to (offer|extend)',
        r'extend (an |a )?(job )?offer',
        r'we.{0,20}(like|want) to offer you',
        r'offer you (the |a )?(position|role|job)',
        r'congratulations.{0,50}(offer|accepted|position)',
        r'accept(ing)? (the |this )?(offer|position|role)',
        r'terms of (employment|your offer)',
        r'compensation (package|details)',
        r'start date',
        r'onboarding',
    ]

    # Recruiter outreach patterns - these indicate someone is reaching out about a NEW position
    # NOT a response to an application you submitted
    RECRUITER_OUTREACH_PATTERNS = [
        # Direct outreach phrases
        r'came across your (profile|resume|background|linkedin)',
        r'found your (profile|resume|background|linkedin)',
        r'saw your (profile|resume|background|linkedin)',
        r'viewed your (profile|resume|linkedin)',
        r'noticed your (profile|resume|background|linkedin)',
        r'i\'m reaching out',
        r'i am reaching out',
        r'reaching out (to you )?(about|regarding|because)',
        r'wanted to reach out',
        r'reaching out to (see|gauge|discuss|explore)',
        r'i wanted to (connect|reach out|touch base|introduce)',
        r'thought (of you|you\'d be|you might be)',
        r'you\'d be (a )?(great|perfect|ideal|excellent) (fit|candidate|match)',
        r'you might be (interested|a good fit|a great fit)',
        r'perfect (fit|candidate|match) for',
        r'great (fit|candidate|match) for',
        r'ideal (candidate|fit) for',
        r'i have (a |an )?(opportunity|role|position)',
        r'i\'ve got (a |an )?(opportunity|role|position)',
        r'we have (a |an )?(opportunity|role|position)',
        r'we\'ve got (a |an )?(opportunity|role|position)',
        r'there\'s (a |an )?(opportunity|role|position)',
        r'exciting opportunity',
        r'new opportunity',
        r'open (role|position|opportunity)',
        r'are you (open to|interested in|looking for)',
        r'would you be (open to|interested in)',
        r'is this something you\'d be interested',
        r'would this be of interest',
        r'are you currently (looking|open|exploring)',
        r'looking for (new opportunities|a new role|your next)',
        r'exploring (new opportunities|new roles)',
        r'on behalf of (my |our )?client',
        r'my client (is |has )',
        r'one of (my |our )clients',
        r'client of (mine|ours)',
        r'confidential (search|opportunity|role|position)',
        r'passive candidates',
        r'your (background|experience|skills) (caught|stood out|impressed|align)',
        r'based on your (experience|background|profile|linkedin)',
        r'your (linkedin|profile) (caught|stood out|impressed)',
        r'quick (call|chat|conversation)',
        r'brief (call|chat|conversation)',
        r'hop on a (call|quick call)',
        r'jump on a (call|quick call)',
        r'15 (minute|min) (call|chat)',
        r'20 (minute|min) (call|chat)',
        r'let me know if.{0,30}interested',
        r'let me know if.{0,30}open to',
        r'if you\'re interested.{0,30}let me know',
        r'if (this|you\'re) interested',
        r'feel free to reach out',
        r'feel free to reply',
        r'looking forward to (hearing|connecting)',
    ]

    # Additional patterns for extracting company from RESPONSE emails
    # These are patterns more common in rejection/interview emails vs confirmation emails
    RESPONSE_COMPANY_PATTERNS = [
        # "Update from Company" or "Update on your application to Company"
        r'[Uu]pdate (?:from|on your.{0,30}(?:at|to|with))\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s*$|!|\.)',
        # "Thank you for your interest in Company"
        r'interest in\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s*$|!|\.)',
        # "Your application to Company" or "regarding your application to Company"
        r'application (?:to|at|with)\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s+has|\s+was|\.|!|,)',
        # "regarding the Position role at Company"
        r'(?:role|position) at\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s*$|!|\.|,)',
        # "from Company Careers" or "from Company Recruiting"
        r'from\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)\s+(?:Careers|Recruiting|Talent|HR|Team)(?:\s|$|<)',
        # "at Company, we" or "At Company,"
        r'(?:^|\. |\n)[Aa]t\s+([A-Z][A-Za-z0-9\s&\-\.\']+?),',
        # "Company has reviewed" or "Company Team"
        r'^([A-Z][A-Za-z0-9\s&\-\.\']+?)\s+(?:has reviewed|Team|Recruiting|Careers)',
        # "on behalf of Company"
        r'on behalf of\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s*$|!|\.|,)',
        # "Update: Company" pattern in subject
        r'[Uu]pdate:\s*([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s*$|!|\.|,|-)',
        # "Company - Application Status"
        r'^([A-Z][A-Za-z0-9\s&\-\.\']+?)\s*[-–:]\s*(?:Application|Your|Status|Update)',
        # "the team at Company"
        r'the (?:team|hiring team|recruiting team) at\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s*$|!|\.|,)',
        # "we at Company"
        r'we at\s+([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s+|\.|,|!)',
    ]

    def parse_response_email(self, email_data: dict) -> dict:
        """
        Parse an email to detect if it's a response to a job application.

        Args:
            email_data: Dictionary with subject, from_address, body_text, date

        Returns:
            Dictionary with response type and extracted data
        """
        subject = email_data.get('subject', '')
        from_address = email_data.get('from_address', '')
        body = email_data.get('body_text', '')
        date = email_data.get('date')

        # Detect platform
        platform = self.detect_platform(from_address, subject)

        # Try to extract company - use response-specific patterns first
        company = self._extract_company_from_response(subject, body, from_address)
        # Fall back to standard extraction if response patterns fail
        if not company:
            company = self._extract_company(subject, body, from_address)
        position = self._extract_position(subject, body)

        # Detect response type
        response_type = self._detect_response_type(subject, body, from_address)

        # Check if this is a job-related response email
        is_response_email = response_type is not None

        return {
            'company_name': company,
            'position': position,
            'platform': platform,
            'response_type': response_type,  # 'rejected', 'interviewing', 'offered', or None
            'is_response_email': is_response_email,
            'email_date': date,
            'email_subject': subject,
            'email_from': from_address,
            'message_id': email_data.get('message_id'),
            'body_preview': body[:300] if body else '',
        }

    def _extract_company_from_response(self, subject: str, body: str, from_address: str) -> Optional[str]:
        """Extract company name from response emails using response-specific patterns."""

        # Try response-specific patterns on subject first
        for pattern in self.RESPONSE_COMPANY_PATTERNS:
            match = re.search(pattern, subject, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                company = self._clean_company_name(company)
                if company and len(company) > 1 and len(company) < 100:
                    if self._looks_like_company_name(company):
                        return company

        # Try response-specific patterns on body
        for pattern in self.RESPONSE_COMPANY_PATTERNS:
            match = re.search(pattern, body[:5000], re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                company = self._clean_company_name(company)
                if company and len(company) > 1 and len(company) < 100:
                    if self._looks_like_company_name(company):
                        return company

        # Try to get company from sender name (e.g., "Company Name <email@domain.com>")
        sender_match = re.match(r'^"?([^"<]+?)"?\s*<', from_address)
        if sender_match:
            sender_name = sender_match.group(1).strip().strip('"\'')

            # If sender name contains @ (like "TEKsystems @ icims"), extract the first part
            if ' @ ' in sender_name:
                sender_name = sender_name.split(' @ ')[0].strip()

            # Skip generic sender names and job platforms
            skip_names = ['indeed', 'linkedin', 'indeed apply', 'linkedin jobs', 'noreply',
                         'no-reply', 'jobs', 'careers', 'recruiting', 'talent', 'hr',
                         'notifications', 'alerts', 'updates', 'candidates', 'workable',
                         'greenhouse', 'lever', 'icims', 'smartrecruiters', 'handshake',
                         'jobvite', 'taleo', 'ashby', 'bamboohr', 'zoho', 'breezy', 'jazz',
                         'glassdoor', 'ziprecruiter', 'monster', 'careerbuilder', 'team',
                         'hiring', 'applicant', 'candidate']
            sender_lower = sender_name.lower().strip()
            if sender_lower not in skip_names and len(sender_name) > 2:
                # Check for platform keywords within sender name
                platform_keywords = ['indeed', 'linkedin', 'greenhouse', 'lever', 'workday',
                                    'icims', 'smartrecruiters', 'workable', 'handshake', 'jobvite',
                                    'taleo', 'ashby', 'bamboohr', 'zoho', 'glassdoor', 'ziprecruiter']
                if not any(p in sender_lower for p in platform_keywords):
                    cleaned = self._clean_company_name(sender_name)
                    if cleaned and self._looks_like_company_name(cleaned):
                        return cleaned

        return None

    def _is_recruiter_outreach(self, subject: str, body: str, from_address: str) -> bool:
        """
        Detect if this email is a recruiter reaching out about a NEW position,
        NOT a response to an application you submitted.
        """
        text = (subject + ' ' + body[:3000]).lower()

        # Count how many outreach patterns match
        outreach_count = sum(1 for pattern in self.RECRUITER_OUTREACH_PATTERNS
                            if re.search(pattern, text, re.IGNORECASE))

        # If 2+ outreach patterns match, this is likely recruiter outreach
        if outreach_count >= 2:
            return True

        # Also check for common recruiter outreach subject lines
        subject_lower = subject.lower()
        outreach_subject_patterns = [
            r'opportunity',
            r'interested\?',
            r'perfect fit',
            r'great fit',
            r'quick question',
            r'reaching out',
            r'your (profile|background|experience)',
            r'new role',
            r'open (role|position)',
            r'job opportunity',
            r'career opportunity',
        ]
        subject_outreach_count = sum(1 for pattern in outreach_subject_patterns
                                     if re.search(pattern, subject_lower, re.IGNORECASE))

        # If subject has outreach language AND body has at least 1 outreach pattern
        if subject_outreach_count >= 1 and outreach_count >= 1:
            return True

        return False

    def _detect_response_type(self, subject: str, body: str, from_address: str) -> Optional[str]:
        """
        Detect what type of response this email is.

        Returns:
            'rejected', 'interviewing', 'offered', or None
        """
        text = (subject + ' ' + body[:3000]).lower()
        subject_lower = subject.lower()
        from_lower = from_address.lower()

        # FIRST: Check if this is recruiter outreach about a NEW position
        # If so, it should NOT be treated as a response to your application
        if self._is_recruiter_outreach(subject, body, from_address):
            return None

        # Skip email thread replies for rejection/offer detection
        # (but interview scheduling can be in reply threads)
        is_reply = re.match(r'^(re:|fw:|fwd:)\s*', subject_lower)

        # Skip personal email addresses
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                          'aol.com', 'icloud.com', 'me.com', 'live.com', 'msn.com']
        is_personal = any(domain in from_lower for domain in personal_domains)

        # Check for offer first (highest priority)
        offer_count = sum(1 for pattern in self.OFFER_PATTERNS
                         if re.search(pattern, text, re.IGNORECASE))
        if offer_count >= 2:
            return 'offered'

        # Check for interview request - but require stronger evidence
        # to avoid false positives from recruiter outreach
        interview_count = sum(1 for pattern in self.INTERVIEW_PATTERNS
                             if re.search(pattern, text, re.IGNORECASE))

        # Also check for phrases that indicate this is about YOUR application
        application_reference_patterns = [
            r'your application',
            r'you applied',
            r'application (?:to|at|for|with)',
            r'role you applied',
            r'position you applied',
            r'regarding your.{0,20}application',
            r'thank you for applying',
            r'thanks for applying',
            r'after reviewing your application',
            r'reviewed your application',
            r'your recent application',
        ]
        has_application_reference = any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in application_reference_patterns
        )

        # For interview status, require either:
        # - 3+ interview patterns (strong signal)
        # - OR 2+ interview patterns AND reference to your application
        if interview_count >= 3:
            return 'interviewing'
        if interview_count >= 2 and has_application_reference:
            return 'interviewing'

        # Check for rejection (skip if from personal email - likely a personal reply)
        if not is_personal:
            rejection_count = sum(1 for pattern in self.REJECTION_PATTERNS
                                 if re.search(pattern, text, re.IGNORECASE))
            if rejection_count >= 1:
                return 'rejected'

        return None

    def _is_job_response_email(self, subject: str, body: str, from_address: str) -> bool:
        """Determine if this email is likely a response to a job application."""
        text = (subject + ' ' + body[:2000]).lower()
        from_lower = from_address.lower()

        # Skip job alert/recommendation emails
        job_match_keywords = [
            'jobs matching', 'job match', 'jobs for you', 'recommended jobs',
            'job alert', 'job alerts', 'new jobs', 'daily job digest',
        ]
        if any(kw in subject.lower() for kw in job_match_keywords):
            return False

        # Check if from a known job platform or careers email
        is_from_job_platform = any(
            domain in from_lower
            for domains in self.PLATFORM_DOMAINS.values()
            for domain in domains
        )
        is_from_careers_email = any(x in from_lower for x in
                                    ['careers@', 'jobs@', 'recruiting@', 'talent@', 'hr@', 'hiring@'])

        # Keywords that indicate this is about a job application
        application_keywords = [
            'your application', 'your candidacy', 'your resume',
            'position', 'role', 'opportunity', 'interview',
            'next steps', 'hiring process', 'recruitment',
            'application status', 'application update',
        ]

        has_app_keyword = any(kw in text for kw in application_keywords)

        return (is_from_job_platform or is_from_careers_email) and has_app_keyword

    def parse_response_emails(self, emails: List[dict]) -> List[dict]:
        """Parse multiple emails looking for job application responses."""
        results = []
        for email in emails:
            try:
                parsed = self.parse_response_email(email)
                if parsed['is_response_email']:
                    results.append(parsed)
            except Exception as e:
                print(f"Error parsing response email: {e}")
                continue

        # Sort by date (newest first)
        results.sort(key=lambda x: x['email_date'] or datetime.min, reverse=True)

        return results
