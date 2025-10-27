"""
Student Progress API endpoints for SACEL Platform
Provides REST API for comprehensive student progress tracking
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.student_progress_service import student_progress_service
from functools import wraps

student_progress_bp = Blueprint('student_progress', __name__,
                                url_prefix='/api/student-progress')


def require_student_or_authorized(f):
    """Decorator to ensure user is student accessing own data or authorized"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        student_id = kwargs.get('student_id') or request.args.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Student ID required'}), 400
        
        student_id = int(student_id)
        
        # Allow student to access own data
        if current_user.role.value == 'student' and current_user.id == student_id:
            return f(*args, **kwargs)
        
        # Allow teachers and admins to access any student data
        if current_user.role.value in ['teacher', 'admin']:
            return f(*args, **kwargs)
        
        # For parents, add logic to check if they're the parent of the student
        # This would require a parent-student relationship in the database
        
        return jsonify({'error': 'Unauthorized access to student data'}), 403
    
    return decorated_function


@student_progress_bp.route('/overview/<int:student_id>')
@login_required
@require_student_or_authorized
def get_student_overview(student_id):
    """Get comprehensive overview of student's academic progress"""
    try:
        overview = student_progress_service.get_student_overview(student_id)
        return jsonify(overview)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch student overview'}), 500


@student_progress_bp.route('/grade-history/<int:student_id>')
@login_required
@require_student_or_authorized
def get_grade_history(student_id):
    """Get detailed grade history with trends"""
    timeframe = request.args.get('timeframe', '6months')
    
    try:
        history = student_progress_service.get_grade_history(
            student_id, timeframe
        )
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch grade history'}), 500


@student_progress_bp.route('/submissions/<int:student_id>')
@login_required
@require_student_or_authorized
def get_assignment_submissions(student_id):
    """Get detailed assignment submission history"""
    status = request.args.get('status', 'all')
    
    try:
        submissions = student_progress_service.get_assignment_submissions(
            student_id, status
        )
        return jsonify(submissions)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch submissions'}), 500


@student_progress_bp.route('/trends/<int:student_id>')
@login_required
@require_student_or_authorized
def get_performance_trends(student_id):
    """Analyze performance trends and patterns"""
    try:
        trends = student_progress_service.get_performance_trends(student_id)
        return jsonify(trends)
    except Exception as e:
        return jsonify({'error': 'Failed to analyze trends'}), 500


@student_progress_bp.route('/recommendations/<int:student_id>')
@login_required
@require_student_or_authorized
def get_learning_recommendations(student_id):
    """Generate personalized learning recommendations"""
    try:
        recommendations = (
            student_progress_service.get_learning_recommendations(student_id)
        )
        return jsonify(recommendations)
    except Exception as e:
        return jsonify({'error': 'Failed to generate recommendations'}), 500


@student_progress_bp.route('/peer-comparison/<int:student_id>')
@login_required
@require_student_or_authorized
def compare_with_peers(student_id):
    """Compare student performance with peers"""
    scope = request.args.get('scope', 'school')
    
    try:
        comparison = student_progress_service.compare_with_peers(
            student_id, scope
        )
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'error': 'Failed to compare with peers'}), 500


@student_progress_bp.route('/dashboard-summary/<int:student_id>')
@login_required
@require_student_or_authorized
def get_dashboard_summary(student_id):
    """Get summary data for student dashboard"""
    try:
        # Get key data for dashboard
        overview = student_progress_service.get_student_overview(student_id)
        trends = student_progress_service.get_performance_trends(student_id)
        submissions = student_progress_service.get_assignment_submissions(
            student_id, 'all'
        )
        
        if 'error' in overview:
            return jsonify(overview), 400
        
        # Prepare dashboard summary
        summary = {
            'basic_info': overview.get('student_info', {}),
            'academic_summary': overview.get('academic_summary', {}),
            'recent_activity': overview.get('recent_activity', {}),
            'subject_performance': overview.get('subject_performance', {}),
            'submission_stats': {
                'total_submissions': submissions.get('total_submissions', 0),
                'status_breakdown': submissions.get('status_breakdown', {}),
                'on_time_rate': submissions.get('on_time_rate', 0)
            },
            'trends_available': not ('error' in trends or 'message' in trends),
            'timestamp': overview.get('timestamp')
        }
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard summary'}), 500


@student_progress_bp.route('/chart-data/<int:student_id>')
@login_required
@require_student_or_authorized
def get_chart_data(student_id):
    """Get formatted data for charts and visualizations"""
    chart_type = request.args.get('type', 'grade_timeline')
    timeframe = request.args.get('timeframe', '6months')
    
    try:
        if chart_type == 'grade_timeline':
            history = student_progress_service.get_grade_history(
                student_id, timeframe
            )
            
            if 'error' in history:
                return jsonify(history), 400
            
            # Format for Chart.js
            timeline_data = history.get('grade_timeline', [])
            chart_data = {
                'labels': [entry['date'] for entry in timeline_data],
                'datasets': [{
                    'label': 'Grade Timeline',
                    'data': [entry['grade'] for entry in timeline_data],
                    'borderColor': 'rgb(59, 130, 246)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'fill': True
                }]
            }
            
        elif chart_type == 'subject_performance':
            overview = student_progress_service.get_student_overview(student_id)
            
            if 'error' in overview:
                return jsonify(overview), 400
            
            subject_data = overview.get('subject_performance', {})
            chart_data = {
                'labels': list(subject_data.keys()),
                'datasets': [{
                    'label': 'Average Grade by Subject',
                    'data': [data['average_grade'] 
                           for data in subject_data.values()],
                    'backgroundColor': [
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)'
                    ]
                }]
            }
            
        elif chart_type == 'weekly_averages':
            history = student_progress_service.get_grade_history(
                student_id, timeframe
            )
            
            if 'error' in history:
                return jsonify(history), 400
            
            weekly_data = history.get('weekly_averages', [])
            chart_data = {
                'labels': [week['week'] for week in weekly_data],
                'datasets': [{
                    'label': 'Weekly Average Grades',
                    'data': [week['average_grade'] for week in weekly_data],
                    'borderColor': 'rgb(16, 185, 129)',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'fill': True
                }]
            }
            
        else:
            return jsonify({'error': 'Invalid chart type'}), 400
        
        return jsonify({
            'chart_type': chart_type,
            'data': chart_data,
            'timeframe': timeframe,
            'timestamp': overview.get('timestamp')
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate chart data'}), 500


@student_progress_bp.route('/recent-activities/<int:student_id>')
@login_required
@require_student_or_authorized
def get_recent_activities(student_id):
    """Get recent academic activities for activity feed"""
    limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 items
    
    try:
        submissions = student_progress_service.get_assignment_submissions(
            student_id, 'all'
        )
        
        if 'error' in submissions:
            return jsonify(submissions), 400
        
        # Get recent submissions and format as activity feed
        recent_submissions = submissions.get('submissions', [])[:limit]
        
        activities = []
        for submission in recent_submissions:
            activity = {
                'id': submission['id'],
                'type': 'submission',
                'title': f"Submitted: {submission['assignment_title']}",
                'description': f"Grade: {submission['grade']}/{submission['max_score']}" if submission['grade'] else "Pending grading",
                'date': submission['submitted_at'],
                'status': submission['status'],
                'subject': submission['subject'],
                'is_late': submission.get('is_late', False)
            }
            activities.append(activity)
        
        return jsonify({
            'activities': activities,
            'total_count': len(recent_submissions),
            'timestamp': submissions.get('timestamp')
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch recent activities'}), 500


@student_progress_bp.route('/export/<int:student_id>')
@login_required
@require_student_or_authorized
def export_progress_report(student_id):
    """Export comprehensive progress report"""
    format_type = request.args.get('format', 'json')
    
    try:
        # Gather comprehensive data
        overview = student_progress_service.get_student_overview(student_id)
        history = student_progress_service.get_grade_history(student_id)
        trends = student_progress_service.get_performance_trends(student_id)
        recommendations = (
            student_progress_service.get_learning_recommendations(student_id)
        )
        submissions = student_progress_service.get_assignment_submissions(
            student_id
        )
        peer_comparison = student_progress_service.compare_with_peers(
            student_id
        )
        
        report = {
            'report_type': 'comprehensive_progress_report',
            'generated_at': overview.get('timestamp'),
            'student_overview': overview,
            'grade_history': history,
            'performance_trends': trends,
            'learning_recommendations': recommendations,
            'assignment_submissions': submissions,
            'peer_comparison': peer_comparison
        }
        
        if format_type == 'json':
            return jsonify(report)
        else:
            return jsonify({'error': 'Only JSON format supported'}), 400
            
    except Exception as e:
        return jsonify({'error': 'Failed to generate report'}), 500