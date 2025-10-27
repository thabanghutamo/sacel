"""
Analytics API endpoints for SACEL platform
Provides RESTful endpoints for accessing student and class performance data
"""

from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_restful import Api, Resource
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, UserRole
from app.services.analytics_service import (
    PerformanceAnalytics,
    get_learning_recommendations,
    invalidate_analytics_cache
)

analytics_bp = Blueprint('analytics', __name__)
api = Api(analytics_bp)

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return {'error': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return decorated

def require_role(*roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return {'error': 'Authentication required'}, 401
            
            user = User.query.get(session['user_id'])
            if not user or user.role not in roles:
                return {'error': 'Insufficient permissions'}, 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


class StudentAnalytics(Resource):
    """API resource for student performance analytics"""
    
    @require_auth
    def get(self, student_id=None):
        """Get student analytics data"""
        current_user = User.query.get(session['user_id'])
        
        # If no student_id provided, use current user (if student)
        if not student_id:
            if current_user.role == UserRole.STUDENT:
                student_id = current_user.id
            else:
                return {'error': 'Student ID required'}, 400
        
        # Permission check
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            return {'error': 'Cannot access other student data'}, 403
        elif current_user.role == UserRole.TEACHER:
            # Teachers can view students in their classes
            student = User.query.get(student_id)
            if not student or student.school_id != current_user.school_id:
                return {'error': 'Cannot access student from different school'}, 403
        elif current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN]:
            return {'error': 'Insufficient permissions'}, 403
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        # Get analytics data
        analytics = PerformanceAnalytics.get_student_overview(student_id, days)
        
        if not analytics:
            return {'error': 'Student not found or no data available'}, 404
        
        return {
            'success': True,
            'data': analytics
        }


class StudentRecommendations(Resource):
    """API resource for learning recommendations"""
    
    @require_auth
    def get(self, student_id=None):
        """Get learning recommendations for a student"""
        current_user = User.query.get(session['user_id'])
        
        # If no student_id provided, use current user (if student)
        if not student_id:
            if current_user.role == UserRole.STUDENT:
                student_id = current_user.id
            else:
                return {'error': 'Student ID required'}, 400
        
        # Permission check (same as analytics)
        if current_user.role == UserRole.STUDENT and current_user.id != student_id:
            return {'error': 'Cannot access other student data'}, 403
        elif current_user.role == UserRole.TEACHER:
            student = User.query.get(student_id)
            if not student or student.school_id != current_user.school_id:
                return {'error': 'Cannot access student from different school'}, 403
        elif current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN]:
            return {'error': 'Insufficient permissions'}, 403
        
        # Get recommendations
        recommendations = get_learning_recommendations(student_id)
        
        return {
            'success': True,
            'data': {
                'student_id': student_id,
                'recommendations': recommendations
            }
        }


class ClassAnalytics(Resource):
    """API resource for class performance analytics"""
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def get(self):
        """Get class analytics for a teacher"""
        current_user = User.query.get(session['user_id'])
        
        # Get query parameters
        teacher_id = request.args.get('teacher_id', type=int)
        subject = request.args.get('subject')
        grade_level = request.args.get('grade_level', type=int)
        
        # Permission check
        if current_user.role == UserRole.TEACHER:
            teacher_id = current_user.id  # Teachers can only see their own classes
        elif not teacher_id:
            return {'error': 'Teacher ID required for admin users'}, 400
        
        # Verify teacher exists and has permission
        if current_user.role in [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN]:
            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role != UserRole.TEACHER:
                return {'error': 'Teacher not found'}, 404
            
            if (current_user.role == UserRole.SCHOOL_ADMIN and 
                teacher.school_id != current_user.school_id):
                return {'error': 'Cannot access teacher from different school'}, 403
        
        # Get analytics data
        analytics = PerformanceAnalytics.get_class_analytics(
            teacher_id, subject, grade_level
        )
        
        return {
            'success': True,
            'data': analytics
        }


class SchoolAnalytics(Resource):
    """API resource for school-level analytics"""
    
    @require_role(UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN)
    def get(self, school_id=None):
        """Get school analytics data"""
        current_user = User.query.get(session['user_id'])
        
        # School admins can only see their own school
        if current_user.role == UserRole.SCHOOL_ADMIN:
            school_id = current_user.school_id
        elif not school_id:
            return {'error': 'School ID required for admin users'}, 400
        
        # Get analytics data
        analytics = PerformanceAnalytics.get_school_analytics(school_id)
        
        return {
            'success': True,
            'data': analytics
        }


class AnalyticsCache(Resource):
    """API resource for managing analytics cache"""
    
    @require_role(UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def delete(self):
        """Clear analytics cache"""
        current_user = User.query.get(session['user_id'])
        
        # Get query parameters
        student_id = request.args.get('student_id', type=int)
        teacher_id = request.args.get('teacher_id', type=int)
        school_id = request.args.get('school_id', type=int)
        
        # Permission checks
        if current_user.role == UserRole.SCHOOL_ADMIN:
            if school_id and school_id != current_user.school_id:
                return {'error': 'Cannot clear cache for different school'}, 403
            
            # Set school_id to current user's school if not provided
            if not school_id:
                school_id = current_user.school_id
        
        # Clear cache
        try:
            invalidate_analytics_cache(
                student_id=student_id,
                teacher_id=teacher_id,
                school_id=school_id
            )
            
            return {
                'success': True,
                'message': 'Analytics cache cleared successfully'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clear cache: {str(e)}'
            }, 500


class AnalyticsOverview(Resource):
    """API resource for analytics dashboard overview"""
    
    @require_auth
    def get(self):
        """Get analytics overview based on user role"""
        current_user = User.query.get(session['user_id'])
        
        if current_user.role == UserRole.STUDENT:
            # Student dashboard - own analytics
            analytics = PerformanceAnalytics.get_student_overview(current_user.id)
            recommendations = get_learning_recommendations(current_user.id)
            
            return {
                'success': True,
                'data': {
                    'type': 'student',
                    'analytics': analytics,
                    'recommendations': recommendations
                }
            }
        
        elif current_user.role == UserRole.TEACHER:
            # Teacher dashboard - class analytics
            analytics = PerformanceAnalytics.get_class_analytics(current_user.id)
            
            return {
                'success': True,
                'data': {
                    'type': 'teacher',
                    'analytics': analytics
                }
            }
        
        elif current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
            # Admin dashboard - school analytics
            school_id = (current_user.school_id if current_user.role == UserRole.SCHOOL_ADMIN 
                        else request.args.get('school_id', type=int))
            
            if not school_id:
                return {'error': 'School ID required'}, 400
            
            analytics = PerformanceAnalytics.get_school_analytics(school_id)
            
            return {
                'success': True,
                'data': {
                    'type': 'school',
                    'analytics': analytics
                }
            }
        
        else:
            return {'error': 'Invalid user role'}, 400


# Register API resources
api.add_resource(StudentAnalytics, 
                '/student/<int:student_id>', 
                '/student')

api.add_resource(StudentRecommendations, 
                '/student/<int:student_id>/recommendations',
                '/student/recommendations')

api.add_resource(ClassAnalytics, '/class')

api.add_resource(SchoolAnalytics, 
                '/school/<int:school_id>',
                '/school')

api.add_resource(AnalyticsCache, '/cache')

api.add_resource(AnalyticsOverview, '/overview')


# Traditional Flask routes for HTML pages
@analytics_bp.route('/dashboard')
def analytics_dashboard():
    """Render analytics dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    
    if user.role == UserRole.STUDENT:
        return render_template('analytics/student_dashboard.html', user=user)
    elif user.role == UserRole.TEACHER:
        return render_template('analytics/teacher_dashboard.html', user=user)
    elif user.role in [UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
        return render_template('analytics/admin_dashboard.html', user=user)
    else:
        return redirect(url_for('public.home'))


@analytics_bp.route('/real-time')
@login_required
def real_time_dashboard():
    """Render real-time analytics dashboard"""
    # Check if user has permission to view analytics
    if current_user.role.value not in ['system_admin', 'principal', 'school_admin', 'teacher']:
        return redirect(url_for('public.home'))
    
    return render_template('analytics/real_time_dashboard.html')


@analytics_bp.route('/student/<int:student_id>')
def student_analytics_page(student_id):
    """Render student analytics page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    current_user = User.query.get(session['user_id'])
    student = User.query.get(student_id)
    
    # Permission check
    if (current_user.role == UserRole.STUDENT and current_user.id != student_id):
        return redirect(url_for('errors.forbidden'))
    elif (current_user.role == UserRole.TEACHER and 
          student.school_id != current_user.school_id):
        return redirect(url_for('errors.forbidden'))
    elif current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN,
                                   UserRole.TEACHER, UserRole.STUDENT]:
        return redirect(url_for('errors.forbidden'))
    
    return render_template('analytics/student_detail.html', 
                         student=student, current_user=current_user)


# Error handlers
@analytics_bp.errorhandler(404)
def analytics_not_found(error):
    return {'error': 'Analytics resource not found'}, 404


@analytics_bp.errorhandler(500)
def analytics_server_error(error):
    return {'error': 'Internal server error in analytics service'}, 500
