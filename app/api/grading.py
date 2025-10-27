"""
Advanced Grading API endpoints for SACEL platform
Provides RESTful endpoints for rubric-based grading, peer reviews, and detailed feedback
"""

from flask import Blueprint, request, session, jsonify, render_template, redirect, url_for
from flask_restful import Api, Resource
from functools import wraps
from app.models import User, UserRole, Assignment, Submission
from app.services.grading_service import (
    GradingService,
    GradingRubric,
    RubricCriteria,
    invalidate_grading_cache,
    export_grades_to_csv
)
from app.services.redis_service import redis_service
import json

grading_bp = Blueprint('grading', __name__)
api = Api(grading_bp)


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


class RubricResource(Resource):
    """API resource for managing grading rubrics"""
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def get(self, rubric_id=None):
        """Get rubric(s)"""
        if rubric_id:
            # Get specific rubric
            cache_key = f"rubric:{rubric_id}"
            rubric_data = redis_service.get_cached_data(cache_key)
            
            if not rubric_data:
                # Check if it's a default rubric
                default_rubrics = GradingService.create_default_rubrics()
                if rubric_id in default_rubrics:
                    rubric_data = default_rubrics[rubric_id].to_dict()
                    # Cache for future use
                    redis_service.cache_data(cache_key, rubric_data, timeout=3600)
                else:
                    return {'error': 'Rubric not found'}, 404
            
            return {
                'success': True,
                'data': rubric_data
            }
        else:
            # Get all available rubrics
            default_rubrics = GradingService.create_default_rubrics()
            rubrics_list = []
            
            for rubric_id, rubric in default_rubrics.items():
                rubrics_list.append({
                    'id': rubric_id,
                    'title': rubric.title,
                    'description': rubric.description,
                    'total_points': rubric.total_points,
                    'criteria_count': len(rubric.criteria)
                })
            
            return {
                'success': True,
                'data': rubrics_list
            }
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def post(self):
        """Create a new custom rubric"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['title', 'description', 'criteria']
            if not all(field in data for field in required_fields):
                return {'error': 'Missing required fields'}, 400
            
            # Create criteria objects
            criteria = []
            for criteria_data in data['criteria']:
                criteria.append(RubricCriteria.from_dict(criteria_data))
            
            # Create rubric
            rubric = GradingRubric(
                title=data['title'],
                description=data['description'],
                criteria=criteria
            )
            
            # Generate rubric ID and cache
            rubric_id = f"custom_{session['user_id']}_{len(data['criteria'])}"
            cache_key = f"rubric:{rubric_id}"
            redis_service.cache_data(cache_key, rubric.to_dict(), timeout=86400)
            
            return {
                'success': True,
                'rubric_id': rubric_id,
                'message': 'Rubric created successfully'
            }
            
        except Exception as e:
            return {'error': f'Failed to create rubric: {str(e)}'}, 500


class AutoGradeResource(Resource):
    """API resource for automatic grading"""
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def post(self, submission_id):
        """Auto-grade a submission using rubric"""
        try:
            data = request.get_json() or {}
            rubric_id = data.get('rubric_id', 'essay')  # Default to essay rubric
            
            # Get submission
            submission = Submission.query.get(submission_id)
            if not submission:
                return {'error': 'Submission not found'}, 404
            
            # Permission check - can only grade own students' work
            current_user = User.query.get(session['user_id'])
            if (current_user.role == UserRole.TEACHER and 
                submission.assignment.teacher_id != current_user.id):
                return {'error': 'Cannot grade other teachers\' assignments'}, 403
            
            # Get rubric
            cache_key = f"rubric:{rubric_id}"
            rubric_data = redis_service.get_cached_data(cache_key)
            
            if not rubric_data:
                default_rubrics = GradingService.create_default_rubrics()
                if rubric_id in default_rubrics:
                    rubric = default_rubrics[rubric_id]
                else:
                    return {'error': 'Rubric not found'}, 404
            else:
                rubric = GradingRubric.from_dict(rubric_data)
            
            # Perform auto-grading
            result = GradingService.auto_grade_submission(submission_id, rubric)
            
            if 'error' in result:
                return result, 400
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            return {'error': f'Auto-grading failed: {str(e)}'}, 500


class PeerReviewResource(Resource):
    """API resource for peer review functionality"""
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def post(self, assignment_id):
        """Create peer review assignments"""
        try:
            data = request.get_json() or {}
            
            review_criteria = data.get('criteria', [
                'Content Quality',
                'Organization',
                'Clarity',
                'Originality'
            ])
            reviews_per_student = data.get('reviews_per_student', 2)
            
            # Permission check
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return {'error': 'Assignment not found'}, 404
            
            current_user = User.query.get(session['user_id'])
            if (current_user.role == UserRole.TEACHER and 
                assignment.teacher_id != current_user.id):
                return {'error': 'Cannot create peer reviews for other teachers\' assignments'}, 403
            
            # Create peer review assignments
            result = GradingService.create_peer_review_assignment(
                assignment_id, review_criteria, reviews_per_student
            )
            
            if 'error' in result:
                return result, 400
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            return {'error': f'Failed to create peer reviews: {str(e)}'}, 500
    
    def get(self, assignment_id):
        """Get peer review assignments for a student"""
        current_user = User.query.get(session['user_id'])
        
        if current_user.role == UserRole.STUDENT:
            # Get peer reviews assigned to this student
            cache_key = f"peer_review:{assignment_id}"
            peer_review_data = redis_service.get_cached_data(cache_key)
            
            if not peer_review_data:
                return {'error': 'No peer reviews found'}, 404
            
            # Filter for this student's assignments
            student_pairings = [
                p for p in peer_review_data['pairings']
                if p['reviewer_id'] == current_user.id
            ]
            
            return {
                'success': True,
                'data': {
                    'criteria': peer_review_data['criteria'],
                    'assignments': student_pairings
                }
            }
        
        elif current_user.role in [UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN]:
            # Get all peer review data for assignment
            cache_key = f"peer_review:{assignment_id}"
            peer_review_data = redis_service.get_cached_data(cache_key)
            
            if not peer_review_data:
                return {'error': 'No peer reviews found'}, 404
            
            return {
                'success': True,
                'data': peer_review_data
            }
        
        else:
            return {'error': 'Insufficient permissions'}, 403


class PeerReviewSubmissionResource(Resource):
    """API resource for submitting peer reviews"""
    
    @require_role(UserRole.STUDENT, UserRole.TEACHER)
    def post(self, submission_id):
        """Submit a peer review"""
        try:
            data = request.get_json()
            current_user = User.query.get(session['user_id'])
            
            # Validate review data
            required_fields = ['ratings', 'comments', 'overall_score']
            if not all(field in data for field in required_fields):
                return {'error': 'Missing required review fields'}, 400
            
            # Submit peer review
            result = GradingService.submit_peer_review(
                current_user.id, submission_id, data
            )
            
            if 'error' in result:
                return result, 400
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            return {'error': f'Failed to submit peer review: {str(e)}'}, 500


class GradeReportResource(Resource):
    """API resource for grade reports"""
    
    @require_auth
    def get(self, submission_id):
        """Get comprehensive grade report"""
        current_user = User.query.get(session['user_id'])
        submission = Submission.query.get(submission_id)
        
        if not submission:
            return {'error': 'Submission not found'}, 404
        
        # Permission check
        if (current_user.role == UserRole.STUDENT and 
            submission.student_id != current_user.id):
            return {'error': 'Cannot access other students\' reports'}, 403
        elif (current_user.role == UserRole.TEACHER and 
              submission.assignment.teacher_id != current_user.id):
            return {'error': 'Cannot access other teachers\' assignments'}, 403
        elif current_user.role not in [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN,
                                       UserRole.TEACHER, UserRole.STUDENT]:
            return {'error': 'Insufficient permissions'}, 403
        
        # Generate report
        report = GradingService.generate_grade_report(submission_id)
        
        if 'error' in report:
            return report, 404
        
        return {
            'success': True,
            'data': report
        }


class GradeCacheResource(Resource):
    """API resource for managing grading cache"""
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def delete(self):
        """Clear grading cache"""
        try:
            submission_id = request.args.get('submission_id', type=int)
            assignment_id = request.args.get('assignment_id', type=int)
            
            invalidate_grading_cache(submission_id, assignment_id)
            
            return {
                'success': True,
                'message': 'Grading cache cleared successfully'
            }
            
        except Exception as e:
            return {'error': f'Failed to clear cache: {str(e)}'}, 500


class GradeExportResource(Resource):
    """API resource for exporting grades"""
    
    @require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
    def get(self, assignment_id):
        """Export assignment grades to CSV"""
        try:
            # Permission check
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return {'error': 'Assignment not found'}, 404
            
            current_user = User.query.get(session['user_id'])
            if (current_user.role == UserRole.TEACHER and 
                assignment.teacher_id != current_user.id):
                return {'error': 'Cannot export other teachers\' assignments'}, 403
            
            # Generate CSV
            csv_content = export_grades_to_csv(assignment_id)
            
            return {
                'success': True,
                'data': {
                    'csv_content': csv_content,
                    'filename': f"{assignment.title}_grades.csv"
                }
            }
            
        except Exception as e:
            return {'error': f'Export failed: {str(e)}'}, 500


# Register API resources
api.add_resource(RubricResource, '/rubrics/<string:rubric_id>', '/rubrics')
api.add_resource(AutoGradeResource, '/auto-grade/<int:submission_id>')
api.add_resource(PeerReviewResource, '/peer-review/<int:assignment_id>')
api.add_resource(PeerReviewSubmissionResource, '/peer-review/submit/<int:submission_id>')
api.add_resource(GradeReportResource, '/report/<int:submission_id>')
api.add_resource(GradeCacheResource, '/cache')
api.add_resource(GradeExportResource, '/export/<int:assignment_id>')


# Traditional Flask routes for HTML pages
@grading_bp.route('/dashboard')
@require_auth
def grading_dashboard():
    """Render grading dashboard"""
    user = User.query.get(session['user_id'])
    
    if user.role == UserRole.TEACHER:
        return render_template('grading/teacher_dashboard.html', user=user)
    elif user.role in [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN]:
        return render_template('grading/admin_dashboard.html', user=user)
    else:
        return redirect(url_for('public.home'))


@grading_bp.route('/rubric/<string:rubric_id>')
@require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
def view_rubric(rubric_id):
    """View rubric details"""
    return render_template('grading/rubric_detail.html', rubric_id=rubric_id)


@grading_bp.route('/assignment/<int:assignment_id>/grade')
@require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
def grade_assignment(assignment_id):
    """Grade assignment page"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Permission check
    current_user = User.query.get(session['user_id'])
    if (current_user.role == UserRole.TEACHER and 
        assignment.teacher_id != current_user.id):
        return redirect(url_for('errors.forbidden'))
    
    return render_template('grading/grade_assignment.html', assignment=assignment)


@grading_bp.route('/submission/<int:submission_id>/grade')
@require_role(UserRole.TEACHER, UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN)
def grade_submission(submission_id):
    """Grade individual submission page"""
    submission = Submission.query.get_or_404(submission_id)
    
    # Permission check
    current_user = User.query.get(session['user_id'])
    if (current_user.role == UserRole.TEACHER and 
        submission.assignment.teacher_id != current_user.id):
        return redirect(url_for('errors.forbidden'))
    
    return render_template('grading/grade_submission.html', submission=submission)


@grading_bp.route('/peer-review/<int:assignment_id>')
@require_auth
def peer_review_page(assignment_id):
    """Peer review page"""
    assignment = Assignment.query.get_or_404(assignment_id)
    user = User.query.get(session['user_id'])
    
    return render_template('grading/peer_review.html', 
                         assignment=assignment, user=user)


# Error handlers
@grading_bp.errorhandler(404)
def grading_not_found(error):
    return {'error': 'Grading resource not found'}, 404


@grading_bp.errorhandler(500)
def grading_server_error(error):
    return {'error': 'Internal server error in grading service'}, 500
