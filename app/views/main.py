"""Main views for the web interface."""

from datetime import date, datetime
from flask import render_template, request, redirect, url_for, flash
from decimal import Decimal
from sqlalchemy import or_, case

from app.views import views_bp
from app.extensions import db
from app.models import JobApplication, InterviewStage, EmailSettings


@views_bp.route('/')
def dashboard():
    """Render the dashboard page."""
    return render_template('pages/dashboard.html')


@views_bp.route('/applications')
def applications():
    """Render the applications list page."""
    return render_template('pages/applications.html')


@views_bp.route('/applications/<int:id>')
def application_detail(id):
    """Render the application detail page."""
    application = JobApplication.query.get_or_404(id)
    return render_template('pages/application_detail.html',
                         application=application,
                         Interview=InterviewStage)


@views_bp.route('/settings/email')
def email_settings():
    """Render the email settings page."""
    settings = EmailSettings.query.first()
    return render_template('pages/email_settings.html', settings=settings)


@views_bp.route('/oauth/callback')
def oauth_callback():
    """Handle Google OAuth callback."""
    from app.services.google_oauth import exchange_code_for_tokens

    error = request.args.get('error')
    if error:
        flash(f'Google sign-in failed: {error}', 'error')
        return redirect(url_for('views.email_settings'))

    code = request.args.get('code')
    if not code:
        flash('No authorization code received', 'error')
        return redirect(url_for('views.email_settings'))

    try:
        # Exchange code for tokens
        tokens = exchange_code_for_tokens(code)

        # Verify we got an email address
        email = tokens.get('email')
        if not email:
            flash('Warning: Could not retrieve email address. Please try connecting again.', 'warning')
            return redirect(url_for('views.email_settings'))

        # Save to database
        settings = EmailSettings.query.first()
        if settings:
            settings.email_address = email
            settings.access_token = tokens['access_token']
            settings.refresh_token = tokens['refresh_token']
            settings.token_expiry = tokens.get('token_expiry')
            settings.is_active = True
        else:
            settings = EmailSettings(
                email_address=email,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                token_expiry=tokens.get('token_expiry'),
                provider='gmail'
            )
            db.session.add(settings)

        db.session.commit()
        flash('Gmail connected successfully!', 'success')

    except Exception as e:
        flash(f'Failed to connect Gmail: {str(e)}', 'error')

    return redirect(url_for('views.email_settings'))


@views_bp.route('/applications/new', methods=['GET', 'POST'])
def new_application():
    """Render the new application form and handle submission."""
    if request.method == 'POST':
        # Parse form data
        data = {
            'company_name': request.form.get('company_name'),
            'position': request.form.get('position'),
            'date_applied': datetime.strptime(request.form.get('date_applied'), '%Y-%m-%d').date()
                           if request.form.get('date_applied') else date.today(),
            'salary_currency': request.form.get('salary_currency', 'USD'),
            'application_url': request.form.get('application_url') or None,
            'job_description': request.form.get('job_description') or None,
            'notes': request.form.get('notes') or None,
            'source': 'manual',
        }

        # Parse salary fields
        if request.form.get('expected_salary_min'):
            data['expected_salary_min'] = Decimal(request.form.get('expected_salary_min'))
        if request.form.get('expected_salary_max'):
            data['expected_salary_max'] = Decimal(request.form.get('expected_salary_max'))

        application = JobApplication(**data)
        db.session.add(application)
        db.session.commit()

        flash('Application added successfully!', 'success')
        return redirect(url_for('views.application_detail', id=application.id))

    return render_template('pages/application_form.html',
                         application=None,
                         today=date.today().isoformat())


@views_bp.route('/applications/<int:id>/edit', methods=['GET', 'POST'])
def edit_application(id):
    """Render the edit application form and handle submission."""
    application = JobApplication.query.get_or_404(id)

    if request.method == 'POST':
        # Update application fields
        application.company_name = request.form.get('company_name')
        application.position = request.form.get('position')
        application.salary_currency = request.form.get('salary_currency', 'USD')
        application.application_url = request.form.get('application_url') or None
        application.job_description = request.form.get('job_description') or None
        application.notes = request.form.get('notes') or None

        # Parse date
        if request.form.get('date_applied'):
            application.date_applied = datetime.strptime(
                request.form.get('date_applied'), '%Y-%m-%d'
            ).date()

        # Parse salary fields
        application.expected_salary_min = (
            Decimal(request.form.get('expected_salary_min'))
            if request.form.get('expected_salary_min') else None
        )
        application.expected_salary_max = (
            Decimal(request.form.get('expected_salary_max'))
            if request.form.get('expected_salary_max') else None
        )

        # Parse status
        if request.form.get('status'):
            application.status = request.form.get('status')

        # Parse response fields
        application.response_received = bool(request.form.get('response_received'))
        if request.form.get('response_date'):
            application.response_date = datetime.strptime(
                request.form.get('response_date'), '%Y-%m-%d'
            ).date()
        else:
            application.response_date = None

        db.session.commit()

        flash('Application updated successfully!', 'success')
        return redirect(url_for('views.application_detail', id=application.id))

    return render_template('pages/application_form.html',
                         application=application,
                         today=date.today().isoformat())


# --- HTMX Partial Views ---

@views_bp.route('/partials/stats')
def stats_partial():
    """Return dashboard stats as HTML partial."""
    from sqlalchemy import func
    from datetime import timedelta

    total = JobApplication.query.count()

    # Status counts
    status_counts = db.session.query(
        JobApplication.status,
        func.count(JobApplication.id)
    ).group_by(JobApplication.status).all()
    status_dict = {status: count for status, count in status_counts}

    # Response rate
    with_response = JobApplication.query.filter_by(response_received=True).count()
    response_rate = (with_response / total * 100) if total > 0 else 0

    # Interview rate
    apps_with_interviews = db.session.query(
        func.count(func.distinct(InterviewStage.application_id))
    ).scalar() or 0
    interview_rate = (apps_with_interviews / total * 100) if total > 0 else 0

    # Recent applications
    week_ago = date.today() - timedelta(days=7)
    recent_week = JobApplication.query.filter(
        JobApplication.date_applied >= week_ago
    ).count()

    month_ago = date.today() - timedelta(days=30)
    recent_month = JobApplication.query.filter(
        JobApplication.date_applied >= month_ago
    ).count()

    stats = {
        'total_applications': total,
        'status_breakdown': {
            'applied': status_dict.get('applied', 0),
            'interviewing': status_dict.get('interviewing', 0),
            'offered': status_dict.get('offered', 0),
            'rejected': status_dict.get('rejected', 0),
            'withdrawn': status_dict.get('withdrawn', 0),
        },
        'response_rate': round(response_rate, 1),
        'interview_rate': round(interview_rate, 1),
        'recent_applications': {
            'last_7_days': recent_week,
            'last_30_days': recent_month,
        },
    }

    return render_template('partials/stats_cards.html', stats=stats)


@views_bp.route('/partials/status-breakdown')
def status_breakdown_partial():
    """Return status breakdown as HTML partial."""
    from sqlalchemy import func

    total = JobApplication.query.count()

    status_counts = db.session.query(
        JobApplication.status,
        func.count(JobApplication.id)
    ).group_by(JobApplication.status).all()
    status_dict = {status: count for status, count in status_counts}

    stats = {
        'total_applications': total,
        'status_breakdown': {
            'applied': status_dict.get('applied', 0),
            'interviewing': status_dict.get('interviewing', 0),
            'offered': status_dict.get('offered', 0),
            'rejected': status_dict.get('rejected', 0),
            'withdrawn': status_dict.get('withdrawn', 0),
        },
    }

    return render_template('partials/status_breakdown.html', stats=stats)


@views_bp.route('/partials/recent-applications')
def recent_applications_partial():
    """Return recent applications as HTML partial."""
    applications = JobApplication.query.order_by(
        JobApplication.date_applied.desc()
    ).limit(5).all()

    return render_template('partials/recent_applications.html',
                         applications=applications)


@views_bp.route('/partials/applications-list')
def applications_list_partial():
    """Return filtered applications list as HTML partial."""
    # Get filter parameters
    status = request.args.get('status')
    search = request.args.get('search')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    sort = request.args.get('sort', 'response_date_desc')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Build query
    query = JobApplication.query

    if status:
        query = query.filter(JobApplication.status == status)

    # Search across company name, position, notes, and job description
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                JobApplication.company_name.ilike(search_term),
                JobApplication.position.ilike(search_term),
                JobApplication.notes.ilike(search_term),
                JobApplication.job_description.ilike(search_term)
            )
        )

    if from_date:
        query = query.filter(JobApplication.date_applied >= from_date)

    if to_date:
        query = query.filter(JobApplication.date_applied <= to_date)

    # Apply sorting
    if sort == 'alphabetical':
        query = query.order_by(JobApplication.company_name.asc())
    elif sort == 'date_applied_desc':
        query = query.order_by(JobApplication.date_applied.desc())
    elif sort == 'status':
        # Sort by status in custom order: follow_up, interviewing, rejected, applied, offered, withdrawn
        status_order = case(
            (JobApplication.status == 'follow_up', 0),
            (JobApplication.status == 'interviewing', 1),
            (JobApplication.status == 'rejected', 2),
            (JobApplication.status == 'applied', 3),
            (JobApplication.status == 'offered', 4),
            (JobApplication.status == 'withdrawn', 5),
            else_=6
        )
        query = query.order_by(status_order, JobApplication.date_applied.desc())
    else:  # response_date_desc (default) - sort by email received date
        # Sort by response_date (most recent first), nulls last
        query = query.order_by(JobApplication.response_date.desc().nullslast(), JobApplication.date_applied.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('partials/applications_list.html',
                         applications=pagination.items,
                         total=pagination.total,
                         pages=pagination.pages,
                         current_page=page,
                         per_page=per_page)
