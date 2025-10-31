from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Assignment, Submission, User, School
from app.extensions import db
from app.services.file_service import file_service
from datetime import datetime
import json

bp = Blueprint('students', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard"""
    # Get recent assignments for dashboard preview
    recent_assignments = Assignment.query.join(School)\
        .filter(Assignment.school_id == current_user.school_id)\
        .filter(Assignment.is_published == True)\
        .order_by(Assignment.due_date.asc())\
        .limit(5).all()
    
    # Get pending submissions count
    pending_count = Assignment.query.join(School)\
        .outerjoin(Submission, (Submission.assignment_id == Assignment.id) & 
                  (Submission.student_id == current_user.id))\
        .filter(Assignment.school_id == current_user.school_id)\
        .filter(Assignment.is_published == True)\
        .filter(Submission.id == None)\
        .filter(Assignment.due_date > datetime.utcnow())\
        .count()
    
    return render_template('students/dashboard.html', 
                          recent_assignments=recent_assignments,
                          pending_count=pending_count)

@bp.route('/assignments')
@login_required  
def assignments():
    """View all assignments for student"""
    # Get all assignments for the student's school
    assignments = Assignment.query.join(School)\
        .filter(Assignment.school_id == current_user.school_id)\
        .filter(Assignment.is_published == True)\
        .order_by(Assignment.due_date.desc()).all()
    
    # Get submissions for these assignments
    submission_dict = {}
    if assignments:
        assignment_ids = [a.id for a in assignments]
        submissions = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids),
            Submission.student_id == current_user.id
        ).all()
        submission_dict = {s.assignment_id: s for s in submissions}
    
    return render_template('students/assignments.html', 
                          assignments=assignments,
                          submissions=submission_dict)

@bp.route('/assignments/<int:assignment_id>')
@login_required
def view_assignment(assignment_id):
    """View specific assignment details"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if student belongs to same school as assignment
    if assignment.school_id != current_user.school_id:
        flash('Assignment not found.', 'error')
        return redirect(url_for('students.assignments'))
    
    if not assignment.is_published:
        flash('Assignment is not yet available.', 'warning')
        return redirect(url_for('students.assignments'))
    
    # Get existing submission if any
    submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=current_user.id
    ).first()
    
    # Parse questions from assignment
    questions = []
    if assignment.question_config:
        try:
            question_data = json.loads(assignment.question_config)
            questions = question_data.get('questions', [])
        except (json.JSONDecodeError, AttributeError):
            questions = []
    
    return render_template('students/assignment_detail.html',
                          assignment=assignment,
                          submission=submission,
                          questions=questions)

@bp.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    """Submit assignment answers"""
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Security checks
    if assignment.school_id != current_user.school_id:
        return jsonify({'error': 'Assignment not found'}), 404
    
    if not assignment.is_published:
        return jsonify({'error': 'Assignment not available'}), 403
    
    # Check if past due date
    if assignment.due_date < datetime.utcnow():
        return jsonify({'error': 'Assignment deadline has passed'}), 403
    
    if request.method == 'GET':
        # Return submission form
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
        
        return render_template('students/submit_assignment.html',
                              assignment=assignment,
                              submission=submission)
    
    # Handle POST submission
    try:
        data = request.get_json() if request.is_json else request.form
        
        # Get or create submission
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=current_user.id
        ).first()
        
        if not submission:
            submission = Submission(
                assignment_id=assignment_id,
                student_id=current_user.id
            )
            db.session.add(submission)
        
        # Update submission data
        answers = data.get('answers', '{}')
        if isinstance(answers, dict):
            answers = json.dumps(answers)
        
        submission.answers = answers
        submission.status = 'submitted'
        submission.submitted_at = datetime.utcnow()
        
        # Handle file uploads if any
        if 'files' in request.files:
            uploaded_files = []
            for file in request.files.getlist('files'):
                if file.filename:
                    file_path = file_service.save_file(file, 'submissions')
                    uploaded_files.append({
                        'filename': file.filename,
                        'path': file_path,
                        'uploaded_at': datetime.utcnow().isoformat()
                    })
            submission.file_references = json.dumps(uploaded_files)
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'submission_id': submission.id})
        else:
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('students.view_assignment', assignment_id=assignment_id))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error submitting assignment: {str(e)}', 'error')
            return redirect(url_for('students.view_assignment', assignment_id=assignment_id))

@bp.route('/progress')
@login_required
def progress_dashboard():
    """Student progress tracking dashboard"""
    return render_template('students/progress_dashboard.html', 
                          student_id=current_user.id)