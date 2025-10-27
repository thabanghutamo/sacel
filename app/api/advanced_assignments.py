"""
Advanced Assignment API endpoints for SACEL Platform
Provides REST API for multimedia assignments, collaboration, and peer review
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.services.advanced_assignment_service import advanced_assignment_service
from functools import wraps
import json

advanced_assignments_bp = Blueprint('advanced_assignments', __name__,
                                   url_prefix='/api/advanced-assignments')


def require_teacher_or_admin(f):
    """Decorator to ensure user is teacher or admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.value not in ['teacher', 'admin', 'system_admin']:
            return jsonify({'error': 'Teacher privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def require_student_or_authorized(f):
    """Decorator for student access or authorized users"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role.value in ['teacher', 'admin', 'system_admin']:
            return f(*args, **kwargs)
        elif current_user.role.value == 'student':
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'Access denied'}), 403
    return decorated_function


@advanced_assignments_bp.route('/create-multimedia', methods=['POST'])
@login_required
@require_teacher_or_admin
def create_multimedia_assignment():
    """Create assignment with multimedia support"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'subject', 'grade_level', 'due_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        result = advanced_assignment_service.create_multimedia_assignment(
            current_user.id, data
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create assignment'}), 500


@advanced_assignments_bp.route('/submit-collaborative', methods=['POST'])
@login_required
@require_student_or_authorized
def submit_collaborative_assignment():
    """Submit collaborative assignment"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['assignment_id', 'student_ids', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Ensure current user is included in collaborators
        if current_user.role.value == 'student':
            if current_user.id not in data['student_ids']:
                data['student_ids'].append(current_user.id)
        
        result = advanced_assignment_service.submit_collaborative_assignment(data)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to submit collaborative assignment'}), 500


@advanced_assignments_bp.route('/check-plagiarism', methods=['POST'])
@login_required
@require_teacher_or_admin
def check_plagiarism():
    """Check content for plagiarism"""
    try:
        data = request.get_json()
        
        if not data or 'assignment_id' not in data or 'content' not in data:
            return jsonify({'error': 'Assignment ID and content required'}), 400
        
        result = advanced_assignment_service.check_plagiarism(
            data['assignment_id'],
            data['content'],
            data.get('exclude_group_id')
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': 'Plagiarism check failed'}), 500


@advanced_assignments_bp.route('/create-peer-reviews/<int:assignment_id>', 
                               methods=['POST'])
@login_required
@require_teacher_or_admin
def create_peer_review_assignments(assignment_id):
    """Create peer review assignments for an assignment"""
    try:
        result = advanced_assignment_service.create_peer_review_assignments(
            assignment_id
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to create peer review assignments'}), 500


@advanced_assignments_bp.route('/submit-peer-review', methods=['POST'])
@login_required
@require_student_or_authorized
def submit_peer_review():
    """Submit a peer review"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['submission_id', 'scores', 'comments']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Set reviewer ID to current user if student
        if current_user.role.value == 'student':
            data['reviewer_id'] = current_user.id
        elif 'reviewer_id' not in data:
            return jsonify({'error': 'Reviewer ID required'}), 400
        
        result = advanced_assignment_service.submit_peer_review(data)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({'error': 'Failed to submit peer review'}), 500


@advanced_assignments_bp.route('/analytics/<int:assignment_id>')
@login_required
@require_teacher_or_admin
def get_assignment_analytics(assignment_id):
    """Get comprehensive analytics for an assignment"""
    try:
        result = advanced_assignment_service.get_assignment_analytics(
            assignment_id
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get assignment analytics'}), 500


@advanced_assignments_bp.route('/peer-review-assignments/<int:student_id>')
@login_required
@require_student_or_authorized
def get_peer_review_assignments(student_id):
    """Get peer review assignments for a student"""
    try:
        # Allow students to only access their own assignments
        if current_user.role.value == 'student' and current_user.id != student_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # This would query assignments where the student is assigned as reviewer
        # For now, return placeholder data structure
        result = {
            'student_id': student_id,
            'pending_reviews': [],
            'completed_reviews': [],
            'review_deadline': None
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get peer review assignments'}), 500


@advanced_assignments_bp.route('/collaboration-invites/<int:student_id>')
@login_required
@require_student_or_authorized
def get_collaboration_invites(student_id):
    """Get collaboration invites for a student"""
    try:
        # Allow students to only access their own invites
        if current_user.role.value == 'student' and current_user.id != student_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # This would query pending collaboration invites
        # For now, return placeholder data structure
        result = {
            'student_id': student_id,
            'pending_invites': [],
            'active_collaborations': [],
            'invitation_history': []
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get collaboration invites'}), 500


@advanced_assignments_bp.route('/multimedia-upload', methods=['POST'])
@login_required
@require_teacher_or_admin
def upload_multimedia_content():
    """Upload multimedia content for assignments"""
    try:
        # This would handle file uploads for multimedia assignments
        # For now, return success response
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        uploaded_files = []
        for file in files:
            if file.filename:
                # Here you would save the file and return the URL
                uploaded_files.append({
                    'filename': file.filename,
                    'url': f'/uploads/{file.filename}',
                    'size': len(file.read()),
                    'type': file.content_type
                })
        
        return jsonify({
            'uploaded_files': uploaded_files,
            'total_files': len(uploaded_files)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to upload multimedia content'}), 500


@advanced_assignments_bp.route('/assignment-features/<int:assignment_id>')
@login_required
def get_assignment_features(assignment_id):
    """Get enabled features for an assignment"""
    try:
        from app.models import Assignment
        
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Parse assignment features from ai_generated_content
        try:
            assignment_settings = json.loads(assignment.ai_generated_content or '{}')
        except:
            assignment_settings = {}
        
        features = {
            'assignment_id': assignment_id,
            'title': assignment.title,
            'multimedia_support': {
                'enabled': len(assignment_settings.get('attachments', [])) > 0,
                'attachments': assignment_settings.get('attachments', []),
                'embedded_videos': assignment_settings.get('embedded_videos', []),
                'interactive_elements': assignment_settings.get('interactive_elements', [])
            },
            'collaboration': {
                'enabled': assignment_settings.get('collaboration_settings', {}).get('allow_collaboration', False),
                'max_collaborators': assignment_settings.get('collaboration_settings', {}).get('max_collaborators', 3),
                'deadline': assignment_settings.get('collaboration_settings', {}).get('collaboration_deadline')
            },
            'peer_review': {
                'enabled': assignment_settings.get('peer_review_settings', {}).get('enable_peer_review', False),
                'reviews_per_student': assignment_settings.get('peer_review_settings', {}).get('reviews_per_student', 2),
                'anonymous': assignment_settings.get('peer_review_settings', {}).get('anonymous_reviews', True),
                'deadline': assignment_settings.get('peer_review_settings', {}).get('peer_review_deadline')
            },
            'plagiarism_detection': {
                'enabled': assignment_settings.get('plagiarism_detection', {}).get('enabled', True),
                'similarity_threshold': assignment_settings.get('plagiarism_detection', {}).get('similarity_threshold', 80),
                'check_internet': assignment_settings.get('plagiarism_detection', {}).get('check_internet', False),
                'check_internal': assignment_settings.get('plagiarism_detection', {}).get('check_internal', True)
            }
        }
        
        return jsonify(features)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get assignment features'}), 500


@advanced_assignments_bp.route('/submission-status/<int:assignment_id>/<int:student_id>')
@login_required
@require_student_or_authorized
def get_submission_status(assignment_id, student_id):
    """Get detailed submission status including collaboration and peer review"""
    try:
        # Allow students to only access their own status
        if current_user.role.value == 'student' and current_user.id != student_id:
            return jsonify({'error': 'Access denied'}), 403
        
        from app.models import Submission, Assignment
        
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=student_id
        ).first()
        
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Parse assignment settings
        try:
            assignment_settings = json.loads(assignment.ai_generated_content or '{}')
        except:
            assignment_settings = {}
        
        status = {
            'assignment_id': assignment_id,
            'student_id': student_id,
            'submission_exists': submission is not None,
            'submission_status': submission.status if submission else 'not_started',
            'submitted_at': submission.submitted_at.isoformat() if submission and submission.submitted_at else None,
            'grade': submission.grade if submission else None,
            'feedback': submission.feedback if submission else None
        }
        
        # Add collaboration info
        if submission and submission.attachment_url:
            try:
                metadata = json.loads(submission.attachment_url)
                if metadata.get('is_collaborative'):
                    status['collaboration'] = {
                        'is_collaborative': True,
                        'group_id': metadata.get('group_id'),
                        'collaborators': metadata.get('collaborators', [])
                    }
            except:
                pass
        
        # Add peer review info
        if assignment_settings.get('peer_review_settings', {}).get('enable_peer_review'):
            peer_reviews = assignment_settings.get('peer_reviews', [])
            submission_reviews = [
                r for r in peer_reviews
                if r['submission_id'] == submission.id
            ] if submission else []
            
            status['peer_review'] = {
                'enabled': True,
                'reviews_received': len(submission_reviews),
                'reviews_to_complete': 0,  # Would calculate pending reviews
                'average_scores': advanced_assignment_service._calculate_average_scores(submission_reviews)
            }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get submission status'}), 500