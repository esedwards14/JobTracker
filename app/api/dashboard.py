"""API endpoints for dashboard statistics."""

from flask import jsonify
from sqlalchemy import func
from datetime import datetime, timedelta

from app.api import api_bp
from app.extensions import db
from app.models import JobApplication, InterviewStage


@api_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get summary statistics for the dashboard."""

    # Total applications
    total = JobApplication.query.count()

    # Applications by status
    status_counts = db.session.query(
        JobApplication.status,
        func.count(JobApplication.id)
    ).group_by(JobApplication.status).all()

    status_dict = {status: count for status, count in status_counts}

    # Response rate
    with_response = JobApplication.query.filter_by(response_received=True).count()
    response_rate = (with_response / total * 100) if total > 0 else 0

    # Applications in last 7 days
    week_ago = datetime.utcnow().date() - timedelta(days=7)
    recent_applications = JobApplication.query.filter(
        JobApplication.date_applied >= week_ago
    ).count()

    # Applications in last 30 days
    month_ago = datetime.utcnow().date() - timedelta(days=30)
    monthly_applications = JobApplication.query.filter(
        JobApplication.date_applied >= month_ago
    ).count()

    # Upcoming interviews (scheduled but not completed)
    upcoming_interviews = InterviewStage.query.filter(
        InterviewStage.scheduled_date >= datetime.utcnow(),
        InterviewStage.completed_date.is_(None)
    ).count()

    # Interview conversion rate (applications that reached interview stage)
    apps_with_interviews = db.session.query(
        func.count(func.distinct(InterviewStage.application_id))
    ).scalar() or 0
    interview_rate = (apps_with_interviews / total * 100) if total > 0 else 0

    return jsonify({
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
            'last_7_days': recent_applications,
            'last_30_days': monthly_applications,
        },
        'upcoming_interviews': upcoming_interviews,
    })


@api_bp.route('/dashboard/timeline', methods=['GET'])
def get_application_timeline():
    """Get applications over time for charting."""

    # Get daily counts for last 30 days
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)

    daily_counts = db.session.query(
        JobApplication.date_applied,
        func.count(JobApplication.id)
    ).filter(
        JobApplication.date_applied >= thirty_days_ago
    ).group_by(
        JobApplication.date_applied
    ).order_by(
        JobApplication.date_applied
    ).all()

    timeline = [
        {'date': date.isoformat(), 'count': count}
        for date, count in daily_counts
    ]

    return jsonify({'timeline': timeline})


@api_bp.route('/dashboard/funnel', methods=['GET'])
def get_application_funnel():
    """Get funnel data showing progression through stages."""

    total = JobApplication.query.count()
    with_response = JobApplication.query.filter_by(response_received=True).count()

    # Count by highest interview stage reached
    apps_with_interviews = db.session.query(
        InterviewStage.application_id,
        func.max(InterviewStage.stage_number).label('max_stage')
    ).group_by(InterviewStage.application_id).subquery()

    first_interview = db.session.query(func.count()).filter(
        apps_with_interviews.c.max_stage >= 1
    ).scalar() or 0

    second_interview = db.session.query(func.count()).filter(
        apps_with_interviews.c.max_stage >= 2
    ).scalar() or 0

    third_plus = db.session.query(func.count()).filter(
        apps_with_interviews.c.max_stage >= 3
    ).scalar() or 0

    offers = JobApplication.query.filter_by(status='offered').count()

    return jsonify({
        'funnel': [
            {'stage': 'Applied', 'count': total},
            {'stage': 'Response', 'count': with_response},
            {'stage': '1st Interview', 'count': first_interview},
            {'stage': '2nd Interview', 'count': second_interview},
            {'stage': '3rd+ Interview', 'count': third_plus},
            {'stage': 'Offer', 'count': offers},
        ]
    })
