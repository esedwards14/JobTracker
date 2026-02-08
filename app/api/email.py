"""API endpoints for email integration with Google OAuth."""

import re
from flask import request, jsonify, redirect, session, url_for
from datetime import datetime

from app.api import api_bp
from app.extensions import db
from app.models import EmailSettings, ParsedEmail, JobApplication
from app.services.email_connector import GmailOAuthConnector
from app.services.email_parser import JobEmailParser
from app.services.google_oauth import get_authorization_url, exchange_code_for_tokens


def normalize_company_name(name: str) -> str:
    """Normalize company name for comparison by removing suffixes and extra spaces."""
    if not name:
        return ""
    # Remove common company suffixes
    name = re.sub(r'\s+', ' ', name.strip())
    name = re.sub(r',\s*inc\.?\s*$|,?\s+inc\.?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r',\s*llc\.?\s*$|,?\s+llc\.?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r',\s*ltd\.?\s*$|,?\s+ltd\.?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r',\s*corp\.?\s*$|,?\s+corp\.?\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+corporation\s*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+company\s*$', '', name, flags=re.IGNORECASE)
    return name.strip()


def extract_companies_from_text(text: str) -> list:
    """Extract potential company names from email text (capitalized phrases)."""
    if not text:
        return []
    
    companies = []
    # Find capitalized phrases (potential company names)
    # Look for "From: CompanyName" or patterns like that
    patterns = [
        r'[Ff]rom:\s*([A-Z][A-Za-z0-9\s&\-\.\']+?)(?:\s+Careers|\s+Team|\s*<|$|\n)',
        r'[Ss]incerely,?\s*\n([A-Z][A-Za-z0-9\s&\-\.\']+)\n',
        r'--\s*\n([A-Z][A-Za-z0-9\s&\-\.\']+)\s*\n',
        r'(\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Careers|Team|Hiring|Recruiting)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            company = match.group(1).strip()
            if len(company) > 3 and len(company) < 80 and company not in companies:
                companies.append(company)
    
    return companies


def find_matching_applications(company: str, position: str, email_from: str, body_preview: str) -> list:
    """Find matching applications using multiple matching strategies."""
    applications = []
    
    # Strategy 1: Direct company name match (with normalization)
    if company:
        normalized_company = normalize_company_name(company)
        apps = JobApplication.query.all()
        for app in apps:
            normalized_app_name = normalize_company_name(app.company_name)
            # Direct match or substring match
            if (normalized_company.lower() in normalized_app_name.lower() or 
                normalized_app_name.lower() in normalized_company.lower()):
                # If we have position, check that too
                if position:
                    if position.lower() in app.position.lower() if app.position else False:
                        applications.append(app)
                else:
                    applications.append(app)
        
        if applications:
            return applications

    # Strategy 2: Match individual words from company name (skip short words)
    if company:
        normalized_company = normalize_company_name(company)
        words = [w for w in normalized_company.split() if len(w) > 3]
        for word in words:
            apps = JobApplication.query.filter(
                JobApplication.company_name.ilike(f'%{word}%')
            ).all()
            if apps:
                applications.extend(apps)
        
        if applications:
            return list(set(applications))  # Remove duplicates

    # Strategy 3: Try extracting company from email body_preview
    if body_preview and not applications:
        potential_companies = extract_companies_from_text(body_preview)
        for potential_company in potential_companies:
            normalized = normalize_company_name(potential_company)
            if normalized:
                apps = JobApplication.query.filter(
                    JobApplication.company_name.ilike(f'%{normalized}%')
                ).all()
                if apps:
                    applications.extend(apps)
        
        if applications:
            return list(set(applications))

    # Strategy 4: Extract company from email domain
    if not applications:
        domain_match = re.search(r'@([^.>]+)', email_from)
        if domain_match:
            domain = domain_match.group(1).lower()
            skip_domains = ['indeed', 'linkedin', 'greenhouse', 'lever', 'gmail',
                           'outlook', 'yahoo', 'hotmail', 'icims', 'workday',
                           'smartrecruiters', 'jobvite', 'taleo', 'ashby', 'workable',
                           'bamboohr', 'breezy', 'jazz', 'zoho', 'noreply', 'mail']
            if domain not in skip_domains and len(domain) > 2:
                apps = JobApplication.query.filter(
                    JobApplication.company_name.ilike(f'%{domain}%')
                ).all()
                if apps:
                    applications.extend(apps)
                    return list(set(applications))

    # Strategy 5: Try sender name
    if not applications:
        sender_match = re.match(r'^"?([^"<]+?)"?\s*<', email_from)
        if sender_match:
            sender_name = sender_match.group(1).strip().strip('"\'')
            if ' @ ' in sender_name:
                sender_name = sender_name.split(' @ ')[0].strip()
            
            skip_names = ['careers', 'jobs', 'recruiting', 'talent', 'hr', 'hiring',
                         'noreply', 'no-reply', 'notifications', 'team']
            platform_keywords = ['indeed', 'linkedin', 'greenhouse', 'lever', 'workday',
                                'icims', 'smartrecruiters', 'workable', 'handshake']
            
            if (sender_name.lower() not in skip_names and len(sender_name) > 2 and
                not any(p in sender_name.lower() for p in platform_keywords)):
                apps = JobApplication.query.filter(
                    JobApplication.company_name.ilike(f'%{sender_name}%')
                ).all()
                if apps:
                    applications.extend(apps)
                
                # Try first word too
                if not apps and ' ' in sender_name:
                    first_word = sender_name.split()[0]
                    if len(first_word) > 3:
                        apps = JobApplication.query.filter(
                            JobApplication.company_name.ilike(f'%{first_word}%')
                        ).all()
                        if apps:
                            applications.extend(apps)
    
    return list(set(applications))  # Remove duplicates


@api_bp.route('/email/settings', methods=['GET'])
def get_email_settings():
    """Get current email settings."""
    settings = EmailSettings.query.first()
    if settings and settings.refresh_token:
        return jsonify(settings.to_dict())
    return jsonify({'configured': False})


@api_bp.route('/email/oauth/start', methods=['GET'])
def start_oauth():
    """Start Google OAuth flow - returns URL to redirect user to."""
    try:
        auth_url, state = get_authorization_url()
        session['oauth_state'] = state
        return jsonify({'authorization_url': auth_url})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/email/settings', methods=['DELETE'])
def delete_email_settings():
    """Delete email settings (disconnect Gmail)."""
    settings = EmailSettings.query.first()
    if settings:
        db.session.delete(settings)
        db.session.commit()
    return jsonify({'message': 'Gmail disconnected'})


@api_bp.route('/email/sync', methods=['POST'])
def sync_emails():
    """Sync emails and parse job applications."""
    settings = EmailSettings.query.first()
    if not settings or not settings.is_active or not settings.refresh_token:
        return jsonify({'error': 'Gmail not connected. Please connect via Google Sign-In first.'}), 400

    days_back = request.json.get('days_back', 30) if request.json else 30

    try:
        # Connect and fetch emails via OAuth
        connector = GmailOAuthConnector(settings.access_token or '', settings.refresh_token)
        with connector:
            raw_emails = connector.fetch_job_emails(days_back=days_back, limit=100)

            # Update tokens if refreshed
            updated_tokens = connector.get_updated_tokens()
            if updated_tokens:
                settings.access_token = updated_tokens['access_token']
                settings.token_expiry = updated_tokens['token_expiry']

        # Parse emails
        parser = JobEmailParser()
        parsed_emails = parser.parse_multiple(raw_emails)

        # Debug info - find Indeed emails (not Indeed Apply) and show their body
        debug_emails = []
        for email in raw_emails:
            subject = email.get('subject', 'No subject')
            from_addr = email.get('from_address', '')
            # Look for Indeed emails but NOT indeedapply@
            if 'indeed' in from_addr.lower() and 'indeedapply@' not in from_addr.lower():
                body = email.get('body_text', '')
                debug_emails.append({
                    'subject': subject[:80],
                    'from': from_addr,
                    'body_length': len(body),
                    'body_sample': body[:2000]
                })
                if len(debug_emails) >= 3:
                    break

        # Save to database (skip duplicates and already-imported applications)
        new_count = 0
        skipped_imported = 0
        for parsed in parsed_emails:
            msg_id = str(parsed['message_id'])
            # Skip if we've already parsed this exact message
            existing = ParsedEmail.query.filter_by(message_id=msg_id).first()
            if existing:
                continue

            # If an application already exists that matches the parsed company/position,
            # skip creating a parsed email to avoid re-importing.
            company = (parsed.get('company_name') or '').strip()
            position = (parsed.get('position') or '').strip()
            app_exists = None
            if company or position:
                app_q = JobApplication.query
                if company:
                    app_q = app_q.filter(JobApplication.company_name.ilike(f'%{company}%'))
                if position:
                    app_q = app_q.filter(JobApplication.position.ilike(f'%{position}%'))
                app_exists = app_q.first()

            if app_exists:
                skipped_imported += 1
                continue

            email_record = ParsedEmail(
                message_id=msg_id,
                email_subject=parsed['email_subject'],
                email_from=parsed['email_from'],
                email_date=parsed['email_date'],
                body_preview=parsed.get('body_preview', ''),
                company_name=parsed['company_name'],
                position=parsed['position'],
                platform=parsed['platform'],
                confidence=parsed['confidence'],
                status='pending'
            )
            db.session.add(email_record)
            new_count += 1

        # Update last sync time
        settings.last_sync = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': f'Sync complete. Found {new_count} new job application emails.',
            'total_scanned': len(raw_emails),
            'job_emails_found': len(parsed_emails),
            'new_emails': new_count,
            'skipped_already_imported': skipped_imported,
            'debug_emails': debug_emails  # Show what emails were fetched
        })

    except Exception as e:
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500


@api_bp.route('/email/parsed', methods=['GET'])
def get_parsed_emails():
    """Get list of parsed emails."""
    status = request.args.get('status', 'pending')

    query = ParsedEmail.query
    if status != 'all':
        query = query.filter_by(status=status)

    emails = query.order_by(ParsedEmail.email_date.desc()).all()

    return jsonify({
        'emails': [e.to_dict() for e in emails]
    })


@api_bp.route('/email/parsed/clear', methods=['DELETE'])
def clear_parsed_emails():
    """Clear all parsed emails to allow re-sync."""
    count = ParsedEmail.query.count()
    ParsedEmail.query.delete()
    db.session.commit()
    return jsonify({'message': f'Cleared {count} parsed emails', 'deleted': count})


@api_bp.route('/email/parsed/<int:id>/import', methods=['POST'])
def import_parsed_email(id):
    """Import a parsed email as a job application."""
    parsed = ParsedEmail.query.get_or_404(id)

    if parsed.status == 'imported':
        return jsonify({'error': 'Email already imported'}), 400

    # Allow overriding extracted data
    data = request.json or {}

    # Create job application
    application = JobApplication(
        company_name=data.get('company_name') or parsed.company_name or 'Unknown Company',
        position=data.get('position') or parsed.position or 'Unknown Position',
        date_applied=parsed.email_date.date() if parsed.email_date else None,
        source='email',
        notes=f"Imported from email: {parsed.email_subject}"
    )
    db.session.add(application)

    # Update parsed email status
    parsed.status = 'imported'
    parsed.application_id = application.id

    db.session.commit()

    return jsonify({
        'message': 'Application imported successfully',
        'application': application.to_dict()
    })


@api_bp.route('/email/parsed/<int:id>/ignore', methods=['POST'])
def ignore_parsed_email(id):
    """Mark a parsed email as ignored."""
    parsed = ParsedEmail.query.get_or_404(id)
    parsed.status = 'ignored'
    db.session.commit()

    return jsonify({'message': 'Email ignored'})


@api_bp.route('/email/parsed/<int:id>', methods=['DELETE'])
def delete_parsed_email(id):
    """Delete a parsed email."""
    parsed = ParsedEmail.query.get_or_404(id)
    db.session.delete(parsed)
    db.session.commit()

    return jsonify({'message': 'Email deleted'})


@api_bp.route('/email/import-all', methods=['POST'])
def import_all_pending():
    """Import all pending parsed emails as job applications."""
    pending = ParsedEmail.query.filter_by(status='pending').all()

    imported = 0
    for parsed in pending:
        if parsed.company_name and parsed.confidence >= 0.5:
            application = JobApplication(
                company_name=parsed.company_name,
                position=parsed.position or 'Unknown Position',
                date_applied=parsed.email_date.date() if parsed.email_date else None,
                source='email',
                notes=f"Imported from email: {parsed.email_subject}"
            )
            db.session.add(application)
            parsed.status = 'imported'
            parsed.application_id = application.id
            imported += 1

    db.session.commit()

    return jsonify({
        'message': f'Imported {imported} applications',
        'imported': imported
    })


@api_bp.route('/email/scan-responses', methods=['POST'])
def scan_response_emails():
    """Scan emails for responses (rejections, interview requests, offers) and update application statuses."""
    settings = EmailSettings.query.first()
    if not settings or not settings.is_active or not settings.refresh_token:
        return jsonify({'error': 'Gmail not connected. Please connect via Google Sign-In first.'}), 400

    days_back = request.json.get('days_back', 30) if request.json else 30

    try:
        # Connect and fetch emails via OAuth
        connector = GmailOAuthConnector(settings.access_token or '', settings.refresh_token)
        with connector:
            # Fetch emails that might be responses (broader search)
            raw_emails = connector.fetch_job_emails(days_back=days_back, limit=200)

            # Update tokens if refreshed
            updated_tokens = connector.get_updated_tokens()
            if updated_tokens:
                settings.access_token = updated_tokens['access_token']
                settings.token_expiry = updated_tokens['token_expiry']

        # Parse emails for responses
        parser = JobEmailParser()
        response_emails = parser.parse_response_emails(raw_emails)

        # Try to match responses to existing applications and update status
        updates = []
        processed_emails = set()  # Track processed message IDs to avoid duplicates
        created_app_keys = set()  # Track newly created apps to avoid duplicates
        
        for response in response_emails:
            message_id = response.get('message_id')
            
            # Skip if we've already processed this email
            if message_id and message_id in processed_emails:
                continue
            
            if message_id:
                processed_emails.add(message_id)
            
            company = response.get('company_name') or 'Unknown Company'
            position = response.get('position') or 'Unknown Position'
            response_type = response.get('response_type')
            email_date = response.get('email_date')
            from_addr = response.get('email_from', '')
            body_preview = response.get('body_preview', '')

            if not response_type:
                continue

            # Find matching application(s) using improved matching logic
            applications = find_matching_applications(company, position, from_addr, body_preview)
            
            # Check if any matched app already has this response (already scanned)
            already_scanned = False
            for app in applications:
                if (app.response_date and email_date and 
                    app.response_date == email_date.date() and 
                    app.status == response_type):
                    already_scanned = True
                    break
            
            # Skip emails that have already been scanned and processed
            if already_scanned:
                continue
            
            # Track if we created a new app to avoid re-updating it
            newly_created = False

            # If no matching application found, create a new one (but avoid duplicates)
            if not applications:
                # Create a key to check for duplicates
                app_key = f"{normalize_company_name(company).lower()}|{position.lower()}"
                
                # Only create if we haven't created one with this company+position combo
                if app_key not in created_app_keys:
                    # Also check if it already exists in the database
                    existing = JobApplication.query.filter(
                        JobApplication.company_name.ilike(f'%{normalize_company_name(company)}%'),
                        JobApplication.position.ilike(f'%{position}%')
                    ).first()
                    
                    if not existing:
                        new_app = JobApplication(
                            company_name=company,
                            position=position,
                            date_applied=email_date.date() if email_date else datetime.utcnow().date(),
                            source='email',
                            status=response_type,
                            response_received=True,
                            response_date=email_date.date() if email_date else None,
                            notes=f"Created from response email: {response.get('email_subject', '')[:100]}"
                        )
                        db.session.add(new_app)
                        applications = [new_app]
                        newly_created = True
                        created_app_keys.add(app_key)

            for app in applications:
                # Skip if we just created this app (already has the right status)
                if newly_created:
                    updates.append({
                        'application_id': app.id,
                        'company': app.company_name,
                        'position': app.position,
                        'old_status': 'applied',
                        'new_status': response_type,
                        'email_subject': response.get('email_subject', '')[:80],
                        'new_application': True
                    })
                    continue
                
                # Only update if the response is newer than the application
                if email_date and app.date_applied and email_date.date() < app.date_applied:
                    continue

                # Don't downgrade status (e.g., don't mark offered as rejected)
                status_priority = {'applied': 0, 'follow_up': 1, 'interviewing': 2, 'offered': 3, 'rejected': 4, 'withdrawn': 5}
                current_priority = status_priority.get(app.status, 0)
                new_priority = status_priority.get(response_type, 0)

                # Allow status update if it's a progression or rejection
                should_update = False
                if response_type == 'rejected':
                    # Only reject if not already offered or withdrawn
                    should_update = app.status not in ['offered', 'withdrawn']
                elif response_type == 'interviewing':
                    # Only update to interviewing if currently applied or follow_up
                    should_update = app.status in ['applied', 'follow_up']
                elif response_type == 'offered':
                    # Always update to offered (unless withdrawn)
                    should_update = app.status != 'withdrawn'

                if should_update:
                    old_status = app.status
                    app.status = response_type
                    app.response_received = True
                    if email_date:
                        app.response_date = email_date.date()

                    updates.append({
                        'application_id': app.id,
                        'company': app.company_name,
                        'position': app.position,
                        'old_status': old_status,
                        'new_status': response_type,
                        'email_subject': response.get('email_subject', '')[:80]
                    })

        db.session.commit()

        return jsonify({
            'message': f'Scan complete. Updated {len(updates)} applications.',
            'total_response_emails': len(response_emails),
            'updates': updates
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500


@api_bp.route('/email/response-preview', methods=['POST'])
def preview_response_emails():
    """Preview what response emails were found without updating anything."""
    settings = EmailSettings.query.first()
    if not settings or not settings.is_active or not settings.refresh_token:
        return jsonify({'error': 'Gmail not connected. Please connect via Google Sign-In first.'}), 400

    days_back = request.json.get('days_back', 30) if request.json else 30

    try:
        # Connect and fetch emails via OAuth
        connector = GmailOAuthConnector(settings.access_token or '', settings.refresh_token)
        with connector:
            raw_emails = connector.fetch_job_emails(days_back=days_back, limit=200)

            # Update tokens if refreshed
            updated_tokens = connector.get_updated_tokens()
            if updated_tokens:
                settings.access_token = updated_tokens['access_token']
                settings.token_expiry = updated_tokens['token_expiry']
                db.session.commit()

        # Parse emails for responses
        parser = JobEmailParser()
        response_emails = parser.parse_response_emails(raw_emails)

        # Format for preview
        preview = []
        created_app_keys = set()  # Track what we'd create to avoid duplicate warnings
        
        for response in response_emails:
            company = response.get('company_name') or 'Unknown Company'
            position = response.get('position') or 'Unknown Position'
            response_type = response.get('response_type')
            email_date = response.get('email_date')
            from_addr = response.get('email_from', '')
            body_preview = response.get('body_preview', '')

            # Find potential matching applications using improved logic
            apps = find_matching_applications(company, position, from_addr, body_preview)

            # Check if any matched app already has this response (already scanned)
            already_scanned = False
            for app in apps:
                if (app.response_date and email_date and 
                    app.response_date == email_date.date() and 
                    app.status == response_type):
                    already_scanned = True
                    break
            
            # Skip emails that have already been scanned and processed
            if already_scanned:
                continue

            matching_apps = [{'id': a.id, 'company': a.company_name, 'position': a.position, 'status': a.status} for a in apps]
            
            # Check if we would create a duplicate
            app_key = f"{normalize_company_name(company).lower()}|{position.lower()}"
            would_be_duplicate = app_key in created_app_keys
            
            # If no matches, will create a new application (unless it would be a duplicate)
            will_create_new = len(matching_apps) == 0 and not would_be_duplicate
            
            if will_create_new:
                created_app_keys.add(app_key)

            preview.append({
                'email_subject': response.get('email_subject', '')[:100],
                'email_from': response.get('email_from', ''),
                'email_date': response.get('email_date').isoformat() if response.get('email_date') else None,
                'company': company,
                'position': position,
                'response_type': response_type,
                'matching_applications': matching_apps,
                'will_create_new': will_create_new,
                'would_be_duplicate': would_be_duplicate
            })

        return jsonify({
            'total_found': len(preview),
            'responses': preview
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500
    