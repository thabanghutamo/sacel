"""
Real-time Analytics API endpoints for SACEL Platform
Provides REST API for live dashboard data
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.real_time_analytics_service import real_time_analytics_service
from datetime import datetime
from typing import Dict, Any


analytics_api_bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')


@analytics_api_bp.route('/platform-overview', methods=['GET'])
@login_required
def get_platform_overview():
    """Get high-level platform statistics"""
    # Check if user has permission to view platform overview
    if current_user.role.value not in ['system_admin', 'principal', 'school_admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        data = real_time_analytics_service.get_platform_overview()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch platform overview: {str(e)}'
        }), 500


@analytics_api_bp.route('/student-performance', methods=['GET'])
@login_required
def get_student_performance():
    """Get student performance analytics"""
    school_id = None
    
    # Determine school filter based on user role
    if current_user.role.value == 'system_admin':
        # System admin can view all schools or filter by specific school
        school_id = request.args.get('school_id', type=int)
    elif current_user.role.value in ['principal', 'school_admin']:
        # School-level users can only see their school
        school_id = current_user.school_id
    elif current_user.role.value == 'teacher':
        # Teachers can see their school's data
        school_id = current_user.school_id
    else:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        data = real_time_analytics_service.get_student_performance_analytics(school_id)
        return jsonify({
            'success': True,
            'data': data,
            'school_id': school_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch student performance data: {str(e)}'
        }), 500


@analytics_api_bp.route('/assignment-analytics', methods=['GET'])
@login_required
def get_assignment_analytics():
    """Get assignment completion and performance analytics"""
    teacher_id = None
    school_id = None
    
    # Determine filters based on user role
    if current_user.role.value == 'system_admin':
        # System admin can view all or filter by school
        school_id = request.args.get('school_id', type=int)
        teacher_id = request.args.get('teacher_id', type=int)
    elif current_user.role.value in ['principal', 'school_admin']:
        # School-level users can see their school's assignments
        school_id = current_user.school_id
        teacher_id = request.args.get('teacher_id', type=int)
    elif current_user.role.value == 'teacher':
        # Teachers can only see their own assignments
        teacher_id = current_user.id
    else:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        data = real_time_analytics_service.get_assignment_analytics(teacher_id, school_id)
        return jsonify({
            'success': True,
            'data': data,
            'filters': {
                'teacher_id': teacher_id,
                'school_id': school_id
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch assignment analytics: {str(e)}'
        }), 500


@analytics_api_bp.route('/school-comparison', methods=['GET'])
@login_required
def get_school_comparison():
    """Get comparative analytics across schools"""
    # Only system admins can see school comparison
    if current_user.role.value != 'system_admin':
        return jsonify({'error': 'System admin access required'}), 403
    
    try:
        data = real_time_analytics_service.get_school_performance_comparison()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch school comparison data: {str(e)}'
        }), 500


@analytics_api_bp.route('/real-time-activity', methods=['GET'])
@login_required
def get_real_time_activity():
    """Get real-time platform activity feed"""
    # Check permissions
    if current_user.role.value not in ['system_admin', 'principal', 'school_admin']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        data = real_time_analytics_service.get_real_time_activity()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch real-time activity: {str(e)}'
        }), 500


@analytics_api_bp.route('/dashboard-summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    """Get personalized dashboard summary based on user role"""
    try:
        summary_data = {}
        
        if current_user.role.value == 'system_admin':
            # System admin gets comprehensive overview
            summary_data = {
                'platform_overview': real_time_analytics_service.get_platform_overview(),
                'school_comparison': real_time_analytics_service.get_school_performance_comparison(),
                'real_time_activity': real_time_analytics_service.get_real_time_activity()
            }
        
        elif current_user.role.value in ['principal', 'school_admin']:
            # School admins get school-specific data
            school_id = current_user.school_id
            summary_data = {
                'student_performance': real_time_analytics_service.get_student_performance_analytics(school_id),
                'assignment_analytics': real_time_analytics_service.get_assignment_analytics(None, school_id),
                'school_activity': real_time_analytics_service.get_real_time_activity()
            }
        
        elif current_user.role.value == 'teacher':
            # Teachers get their personal analytics
            teacher_id = current_user.id
            summary_data = {
                'assignment_analytics': real_time_analytics_service.get_assignment_analytics(teacher_id, None),
                'student_performance': real_time_analytics_service.get_student_performance_analytics(current_user.school_id)
            }
        
        elif current_user.role.value == 'student':
            # Students get limited personal analytics
            summary_data = {
                'personal_progress': {
                    'message': 'Student analytics coming soon',
                    'placeholder_data': True
                }
            }
        
        else:
            return jsonify({'error': 'Invalid user role'}), 400
        
        return jsonify({
            'success': True,
            'data': summary_data,
            'user_role': current_user.role.value,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch dashboard summary: {str(e)}'
        }), 500


@analytics_api_bp.route('/chart-data/<chart_type>', methods=['GET'])
@login_required
def get_chart_data(chart_type: str):
    """Get specific chart data for frontend visualization"""
    # Check permissions
    if current_user.role.value not in ['system_admin', 'principal', 'school_admin', 'teacher']:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    try:
        chart_data = {}
        
        if chart_type == 'user_growth':
            # User growth over time
            chart_data = _generate_user_growth_data()
        
        elif chart_type == 'assignment_completion':
            # Assignment completion rates
            chart_data = _generate_assignment_completion_data()
        
        elif chart_type == 'performance_trends':
            # Performance trends
            chart_data = _generate_performance_trends_data()
        
        elif chart_type == 'school_comparison':
            # School comparison data
            if current_user.role.value == 'system_admin':
                chart_data = _generate_school_comparison_data()
            else:
                return jsonify({'error': 'System admin access required'}), 403
        
        elif chart_type == 'subject_distribution':
            # Subject distribution
            chart_data = _generate_subject_distribution_data()
        
        else:
            return jsonify({'error': 'Invalid chart type'}), 400
        
        return jsonify({
            'success': True,
            'chart_type': chart_type,
            'data': chart_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch chart data: {str(e)}'
        }), 500


def _generate_user_growth_data() -> Dict[str, Any]:
    """Generate user growth chart data"""
    return {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'datasets': [
            {
                'label': 'Students',
                'data': [120, 145, 160, 180, 200, 220],
                'backgroundColor': 'rgba(59, 130, 246, 0.5)',
                'borderColor': 'rgba(59, 130, 246, 1)'
            },
            {
                'label': 'Teachers',
                'data': [15, 18, 20, 22, 25, 28],
                'backgroundColor': 'rgba(34, 197, 94, 0.5)',
                'borderColor': 'rgba(34, 197, 94, 1)'
            }
        ]
    }


def _generate_assignment_completion_data() -> Dict[str, Any]:
    """Generate assignment completion chart data"""
    return {
        'labels': ['Completed', 'In Progress', 'Overdue', 'Not Started'],
        'datasets': [
            {
                'data': [65, 20, 10, 5],
                'backgroundColor': [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(156, 163, 175, 0.8)'
                ],
                'borderWidth': 2
            }
        ]
    }


def _generate_performance_trends_data() -> Dict[str, Any]:
    """Generate performance trends chart data"""
    return {
        'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        'datasets': [
            {
                'label': 'Average Score',
                'data': [78, 82, 85, 87],
                'backgroundColor': 'rgba(168, 85, 247, 0.5)',
                'borderColor': 'rgba(168, 85, 247, 1)',
                'fill': True
            }
        ]
    }


def _generate_school_comparison_data() -> Dict[str, Any]:
    """Generate school comparison chart data"""
    return {
        'labels': ['Greenfield High', 'Riverside Academy', 'Mountain View', 'City Central'],
        'datasets': [
            {
                'label': 'Student Count',
                'data': [450, 320, 280, 550],
                'backgroundColor': 'rgba(59, 130, 246, 0.6)'
            },
            {
                'label': 'Teacher Count',
                'data': [25, 18, 15, 32],
                'backgroundColor': 'rgba(34, 197, 94, 0.6)'
            }
        ]
    }


def _generate_subject_distribution_data() -> Dict[str, Any]:
    """Generate subject distribution chart data"""
    return {
        'labels': ['Mathematics', 'English', 'Science', 'History', 'Geography', 'Arts'],
        'datasets': [
            {
                'data': [25, 20, 18, 12, 15, 10],
                'backgroundColor': [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(168, 85, 247, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(236, 72, 153, 0.8)'
                ]
            }
        ]
    }