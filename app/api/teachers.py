from flask import Blueprint, render_template, jsonify, request, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Assignment, Submission, UserRole
from app.extensions import db
from app.services.redis_service import redis_service
from app.services.ai_service import ai_service
from sqlalchemy import func
from datetime import datetime
import json

bp = Blueprint('teachers', __name__)


@bp.route('/communication')
@login_required
def communication_center():
    """Communication center for teachers"""
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
        return redirect(url_for('auth.login'))
    
    return render_template('communication/dashboard.html')


@bp.route('/calendar')
@login_required
def calendar():
    """Calendar and scheduling for teachers"""
    if current_user.role not in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN]:
        return redirect(url_for('auth.login'))
    
    return render_template('calendar/dashboard.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    """Teacher dashboard with stats and recent activity"""
    # Verify teacher role
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    # Try to get cached stats first
    stats = redis_service.get_teacher_stats(current_user.id)
    if not stats:
        # Generate and cache stats
        stats = get_teacher_stats(current_user.id)
        redis_service.cache_teacher_stats(current_user.id, stats, expire=300)
    
    # Try to get cached student performance
    student_performance = redis_service.get_student_performance(current_user.id)
    if not student_performance:
        # Generate and cache student performance
        student_performance = get_student_performance_summary(current_user.id)
        redis_service.cache_student_performance(current_user.id, student_performance, expire=600)
    
    # Get recent assignments (last 5)
    recent_assignments = Assignment.query.filter_by(
        teacher_id=current_user.id
    ).order_by(Assignment.created_at.desc()).limit(5).all()
    
    return render_template('teachers/dashboard.html',
                          stats=stats,
                          recent_assignments=recent_assignments,
                          student_performance=student_performance)


@bp.route('/assignments')
@login_required
def assignments():
    """List all assignments created by the teacher"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    page = request.args.get('page', 1, type=int)
    assignments = Assignment.query.filter_by(
        teacher_id=current_user.id
    ).order_by(Assignment.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('teachers/assignments.html',
                          assignments=assignments)


@bp.route('/assignments/create')
@login_required
def create_assignment():
    """Show assignment creation form"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    return render_template('teachers/create_assignment.html')


@bp.route('/assignments/create-advanced')
@login_required
def create_advanced_assignment():
    """Show advanced assignment creation form with multimedia features"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    return render_template('teachers/advanced_assignment_creator.html')


@bp.route('/assignments', methods=['POST'])
@login_required
def store_assignment():
    """Create a new assignment with AI integration support"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['title', 'subject', 'grade_level', 'due_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Parse due date
        try:
            due_date = datetime.fromisoformat(data['due_date'].replace('T', ' '))
        except ValueError:
            return jsonify({'error': 'Invalid due date format'}), 400
        
        # Validate due date is in the future
        if due_date <= datetime.utcnow():
            return jsonify({'error': 'Due date must be in the future'}), 400
        
        # Handle AI-generated questions
        ai_questions = None
        if 'ai_generated_questions' in data:
            try:
                import json
                ai_questions = json.loads(data['ai_generated_questions'])
                current_app.logger.info(f"AI questions added to assignment: {len(ai_questions) if ai_questions else 0} questions")
            except json.JSONDecodeError:
                current_app.logger.warning("Invalid AI questions JSON format")
        
        # Create assignment
        assignment = Assignment(
            title=data['title'],
            description=data.get('description', ''),
            subject=data['subject'],
            grade_level=int(data['grade_level']),
            due_date=due_date,
            max_score=int(data.get('max_score', 100)),
            teacher_id=current_user.id,
            instructions=data.get('instructions', ''),
            attachment_url=data.get('attachment_url'),
            is_active=not data.get('is_draft', False)  # Drafts are inactive
        )
        
        # Store AI-generated content if available
        if ai_questions:
            assignment.ai_generated_content = json.dumps({
                'questions': ai_questions,
                'generated_at': datetime.utcnow().isoformat(),
                'ai_version': 'gpt-4'
            })
        
        db.session.add(assignment)
        db.session.commit()
        
        # Invalidate teacher cache after creating assignment
        redis_service.invalidate_teacher_cache(current_user.id)
        
        # Log AI usage for analytics
        if ai_questions:
            current_app.logger.info(f"AI-enhanced assignment '{assignment.title}' created by teacher {current_user.id} with {len(ai_questions)} generated questions")
        else:
            current_app.logger.info(f"Assignment '{assignment.title}' created by teacher {current_user.id}")
        
        response_data = {
            'message': 'Assignment created successfully',
            'assignment_id': assignment.id,
            'is_draft': data.get('is_draft', False)
        }
        
        # Add AI enhancement info to response
        if ai_questions:
            response_data['ai_enhanced'] = True
            response_data['ai_questions_count'] = len(ai_questions)
        
        return jsonify(response_data), 201
        
    except ValueError as e:
        current_app.logger.error(f"Validation error creating assignment: {str(e)}")
        return jsonify({'error': 'Invalid input data'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating assignment: {str(e)}")
        return jsonify({'error': 'Failed to create assignment'}), 500


@bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    """Delete an assignment"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        assignment = Assignment.query.filter_by(
            id=assignment_id, 
            teacher_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Check if there are submissions
        if assignment.submissions:
            return jsonify({
                'error': 'Cannot delete assignment with submissions'
            }), 400
        
        db.session.delete(assignment)
        db.session.commit()
        
        # Invalidate caches
        redis_service.invalidate_teacher_cache(current_user.id)
        redis_service.invalidate_assignment_cache(assignment_id)
        
        current_app.logger.info(f"Assignment {assignment_id} deleted by teacher {current_user.id}")
        
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting assignment {assignment_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete assignment'}), 500


@bp.route('/grading')
@login_required
def grading():
    """Show submissions pending grading"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    # Get ungraded submissions for teacher's assignments
    ungraded_submissions = db.session.query(Submission).join(
        Assignment
    ).filter(
        Assignment.teacher_id == current_user.id,
        Submission.grade.is_(None)
    ).order_by(Submission.submitted_at.desc()).all()
    
    return render_template('teachers/grading.html',
                          submissions=ungraded_submissions)


@bp.route('/students')
@login_required
def students():
    """List students in teacher's classes"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    # Get all students who have submitted assignments to this teacher
    students = db.session.query(User).join(Submission).join(
        Assignment
    ).filter(
        Assignment.teacher_id == current_user.id,
        User.role == 'student'
    ).distinct().all()
    
    return render_template('teachers/students.html', students=students)


@bp.route('/health/redis')
@login_required
def redis_health():
    """Check Redis connection health - for debugging/monitoring"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    health_status = redis_service.health_check()
    status_code = 200 if health_status['connected'] else 503
    
    return jsonify(health_status), status_code


def get_teacher_stats(teacher_id):
    """Get statistics for teacher dashboard"""
    try:
        # Total students (unique students who submitted to this teacher)
        total_students = db.session.query(User.id).join(
            Submission
        ).join(Assignment).filter(
            Assignment.teacher_id == teacher_id,
            User.role == 'student'
        ).distinct().count()
        
        # Active assignments (assignments with due dates in the future)
        active_assignments = Assignment.query.filter(
            Assignment.teacher_id == teacher_id,
            Assignment.due_date > datetime.utcnow()
        ).count()
        
        # Pending grading (submissions without grades)
        pending_grading = db.session.query(Submission).join(
            Assignment
        ).filter(
            Assignment.teacher_id == teacher_id,
            Submission.grade.is_(None)
        ).count()
        
        # Class average (average of all graded submissions)
        avg_result = db.session.query(func.avg(Submission.grade)).join(
            Assignment
        ).filter(
            Assignment.teacher_id == teacher_id,
            Submission.grade.isnot(None)
        ).scalar()
        
        class_average = round(avg_result, 1) if avg_result else None
        
        return {
            'total_students': total_students,
            'active_assignments': active_assignments,
            'pending_grading': pending_grading,
            'class_average': class_average
        }
    except Exception as e:
        current_app.logger.error(f"Error getting teacher stats: {str(e)}")
        return {
            'total_students': 0,
            'active_assignments': 0,
            'pending_grading': 0,
            'class_average': None
        }


def get_student_performance_summary(teacher_id, limit=10):
    """Get top performing students for teacher dashboard"""
    try:
        # Get students with their average grades and assignment completion
        student_stats = db.session.query(
            User.id,
            User.full_name.label('name'),
            User.grade,
            func.avg(Submission.grade).label('average_grade'),
            func.count(Submission.id).label('assignments_completed')
        ).join(Submission).join(Assignment).filter(
            Assignment.teacher_id == teacher_id,
            User.role == 'student',
            Submission.grade.isnot(None)
        ).group_by(User.id, User.full_name, User.grade).order_by(
            func.avg(Submission.grade).desc()
        ).limit(limit).all()
        
        return [{
            'name': stat.name,
            'grade': stat.grade,
            'average_grade': round(stat.average_grade, 1) if stat.average_grade else 0,
            'assignments_completed': stat.assignments_completed
        } for stat in student_stats]
        
    except Exception as e:
        current_app.logger.error(f"Error getting student performance: {str(e)}")
        return []


# ============================================================================
# ASSIGNMENT GRADING ENDPOINTS
# ============================================================================

@bp.route('/grading')
@login_required
def grading_dashboard():
    """Teacher grading dashboard showing assignments with submissions to grade"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    return render_template('teachers/grading_dashboard.html')


@bp.route('/api/assignments/pending-grading')
@login_required
def get_assignments_pending_grading():
    """Get assignments with ungraded submissions"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get assignments with ungraded submissions
        assignments = db.session.query(Assignment).join(Submission).filter(
            Assignment.teacher_id == current_user.id,
            Assignment.is_active == True,
            Submission.status == 'submitted',
            Submission.grade.is_(None)
        ).distinct().all()
        
        assignments_data = []
        for assignment in assignments:
            # Count ungraded submissions for this assignment
            ungraded_count = Submission.query.filter_by(
                assignment_id=assignment.id,
                grade=None
            ).filter(Submission.status == 'submitted').count()
            
            # Count total submissions
            total_submissions = Submission.query.filter_by(
                assignment_id=assignment.id
            ).filter(Submission.status == 'submitted').count()
            
            assignments_data.append({
                'id': assignment.id,
                'title': assignment.title,
                'subject': assignment.subject,
                'grade_level': assignment.grade_level,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'max_score': assignment.max_score,
                'ungraded_count': ungraded_count,
                'total_submissions': total_submissions,
                'created_at': assignment.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'assignments': assignments_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting assignments pending grading: {str(e)}")
        return jsonify({'error': 'Failed to fetch assignments'}), 500


@bp.route('/api/assignments/<int:assignment_id>/submissions')
@login_required
def get_assignment_submissions(assignment_id):
    """Get all submissions for an assignment"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Verify assignment belongs to teacher
        assignment = Assignment.query.filter_by(
            id=assignment_id,
            teacher_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Get submissions with student information
        submissions = db.session.query(Submission, User).join(
            User, Submission.student_id == User.id
        ).filter(
            Submission.assignment_id == assignment_id,
            Submission.status == 'submitted'
        ).order_by(Submission.submitted_at.desc()).all()
        
        submissions_data = []
        for submission, student in submissions:
            submissions_data.append({
                'id': submission.id,
                'student_name': student.full_name,
                'student_email': student.email,
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                'grade': submission.grade,
                'feedback': submission.feedback,
                'status': submission.status,
                'answers': json.loads(submission.content) if submission.content else {},
                'attachment_url': submission.attachment_url,
                'graded_at': submission.graded_at.isoformat() if submission.graded_at else None
            })
        
        return jsonify({
            'success': True,
            'assignment': {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'max_score': assignment.max_score,
                'questions': json.loads(assignment.ai_generated_content) if assignment.ai_generated_content else []
            },
            'submissions': submissions_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting assignment submissions: {str(e)}")
        return jsonify({'error': 'Failed to fetch submissions'}), 500


@bp.route('/api/submissions/<int:submission_id>/grade', methods=['POST'])
@login_required
def grade_submission(submission_id):
    """Grade a specific submission"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get submission and verify teacher owns the assignment
        submission = db.session.query(Submission).join(Assignment).filter(
            Submission.id == submission_id,
            Assignment.teacher_id == current_user.id
        ).first()
        
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        data = request.get_json()
        grade = data.get('grade')
        feedback = data.get('feedback', '')
        
        # Validate grade
        if grade is None or not isinstance(grade, (int, float)):
            return jsonify({'error': 'Valid grade is required'}), 400
        
        if grade < 0 or grade > submission.assignment.max_score:
            return jsonify({'error': f'Grade must be between 0 and {submission.assignment.max_score}'}), 400
        
        # Update submission
        submission.grade = grade
        submission.feedback = feedback
        submission.status = 'graded'
        submission.graded_at = datetime.utcnow()
        submission.graded_by = current_user.id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Submission graded successfully',
            'submission': {
                'id': submission.id,
                'grade': submission.grade,
                'feedback': submission.feedback,
                'graded_at': submission.graded_at.isoformat()
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error grading submission: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to grade submission'}), 500


@bp.route('/api/submissions/<int:submission_id>/ai-grade', methods=['POST'])
@login_required
def ai_grade_submission(submission_id):
    """Get AI-assisted grading for a submission"""
    if current_user.role != UserRole.TEACHER:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Get submission and verify teacher owns the assignment
        submission = db.session.query(Submission).join(Assignment).filter(
            Submission.id == submission_id,
            Assignment.teacher_id == current_user.id
        ).first()
        
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        # Get assignment questions
        assignment = submission.assignment
        questions = json.loads(assignment.ai_generated_content) if assignment.ai_generated_content else []
        
        # Get student answers
        answers = json.loads(submission.content) if submission.content else {}
        
        # Use AI service to grade the submission
        grading_result = ai_service.grade_assignment(
            questions=questions,
            answers=answers,
            max_score=assignment.max_score
        )
        
        if grading_result.get('success'):
            return jsonify({
                'success': True,
                'ai_grading': {
                    'suggested_grade': grading_result.get('suggested_grade'),
                    'breakdown': grading_result.get('breakdown', []),
                    'feedback': grading_result.get('feedback', ''),
                    'confidence': grading_result.get('confidence', 0.8)
                }
            })
        else:
            return jsonify({
                'error': 'AI grading failed',
                'message': grading_result.get('error', 'Unknown error')
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Error with AI grading: {str(e)}")
        return jsonify({'error': 'AI grading service unavailable'}), 500


@bp.route('/grading/assignment/<int:assignment_id>')
@login_required
def grade_assignment_submissions(assignment_id):
    """Teacher interface for grading assignment submissions"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    # Verify assignment belongs to teacher
    assignment = Assignment.query.filter_by(
        id=assignment_id,
        teacher_id=current_user.id
    ).first()
    
    if not assignment:
        flash('Assignment not found', 'error')
        return redirect(url_for('teachers.grading_dashboard'))
    
    return render_template('teachers/grade_submissions.html', assignment=assignment)


@bp.route('/grading/submission/<int:submission_id>')
@login_required
def grade_single_submission(submission_id):
    """Teacher interface for grading a single submission"""
    if current_user.role != UserRole.TEACHER:
        return render_template('errors/403.html'), 403
    
    # Get submission and verify teacher owns the assignment
    submission = db.session.query(Submission).join(Assignment).filter(
        Submission.id == submission_id,
        Assignment.teacher_id == current_user.id
    ).first()
    
    if not submission:
        flash('Submission not found', 'error')
        return redirect(url_for('teachers.grading_dashboard'))
    
    # Get student information
    student = User.query.get(submission.student_id)
    
    return render_template('teachers/grade_single_submission.html', 
                         submission=submission, student=student)