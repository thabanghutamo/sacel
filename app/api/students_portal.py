"""
Student dashboard and portal for SACEL
Provides student-specific functionality including assignments, grades, and learning resources
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, School, Application, UserRole, Assignment
from app.extensions import db
from datetime import datetime

bp = Blueprint('student_portal', __name__)

def require_student():
    """Decorator to require student access"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if current_user.role != UserRole.STUDENT:
        flash('Access denied. Student privileges required.', 'error')
        return redirect(url_for('public.home'))
    
    return None

@bp.route('/dashboard')
@login_required
def dashboard():
    """Main student dashboard"""
    error = require_student()
    if error:
        return error
    
    # Get student's school info
    school = current_user.school
    
    # Get real stats from database
    from app.models import Submission
    
    # Get all assignments for student's school
    student_assignments = Assignment.query.filter_by(
        school_id=current_user.school_id,
        is_published=True,
        is_active=True
    ).all()
    
    # Get student's submissions
    student_submissions = Submission.query.filter_by(
        student_id=current_user.id
    ).all()
    
    # Calculate real stats
    total_assignments = len(student_assignments)
    completed_assignments = len([s for s in student_submissions if s.submitted_at])
    pending_assignments = total_assignments - completed_assignments
    
    # Calculate average grade from graded submissions
    graded_submissions = [s for s in student_submissions if s.percentage is not None]
    average_grade = round(sum(s.percentage for s in graded_submissions) / len(graded_submissions)) if graded_submissions else 0
    
    stats = {
        'total_assignments': total_assignments,
        'completed_assignments': completed_assignments,
        'pending_assignments': pending_assignments,
        'average_grade': average_grade,
        'attendance_percentage': 0,  # TODO: Implement attendance tracking
        'upcoming_events': 0  # TODO: Implement events/calendar
    }
    
    # Get recent assignments (last 5)
    recent_assignments = []
    for assignment in student_assignments[:5]:
        submission = next((s for s in student_submissions if s.assignment_id == assignment.id), None)
        status = 'completed' if submission and submission.submitted_at else 'pending'
        recent_assignments.append({
            'id': assignment.id,
            'title': assignment.title,
            'subject': assignment.subject,
            'status': status,
            'due_date': assignment.due_date
        })
    
    # Get upcoming deadlines (assignments due in next 30 days)
    from datetime import timedelta
    upcoming_deadline_assignments = [
        a for a in student_assignments 
        if a.due_date > datetime.now() and a.due_date <= datetime.now() + timedelta(days=30)
    ]
    upcoming_deadlines = [
        {
            'title': assignment.title,
            'due_date': assignment.due_date
        }
        for assignment in sorted(upcoming_deadline_assignments, key=lambda x: x.due_date)[:5]
    ]
    
    # Get recent grades (last 5 graded submissions)
    recent_graded = sorted(
        [s for s in student_submissions if s.percentage is not None],
        key=lambda x: x.graded_at or x.submitted_at,
        reverse=True
    )[:5]
    
    recent_grades = []
    for submission in recent_graded:
        assignment = next((a for a in student_assignments if a.id == submission.assignment_id), None)
        if assignment:
            recent_grades.append({
                'assignment_title': assignment.title,
                'subject': assignment.subject,
                'score': submission.percentage
            })
    
    # Get recent activities (submissions and grades)
    recent_activities = []
    
    # Add recent submissions
    recent_submissions = sorted(
        [s for s in student_submissions if s.submitted_at],
        key=lambda x: x.submitted_at,
        reverse=True
    )[:3]
    
    for submission in recent_submissions:
        assignment = next((a for a in student_assignments if a.id == submission.assignment_id), None)
        if assignment:
            time_diff = datetime.now() - submission.submitted_at
            if time_diff.days == 0:
                timestamp = f"{time_diff.seconds // 3600} hours ago" if time_diff.seconds >= 3600 else f"{time_diff.seconds // 60} minutes ago"
            else:
                timestamp = f"{time_diff.days} days ago"
            
            recent_activities.append({
                'title': 'Assignment Submitted',
                'description': f"{assignment.title} submitted successfully",
                'timestamp': timestamp
            })
    
    # Add recent grades
    for submission in recent_graded[:2]:
        assignment = next((a for a in student_assignments if a.id == submission.assignment_id), None)
        if assignment and submission.graded_at:
            time_diff = datetime.now() - submission.graded_at
            if time_diff.days == 0:
                timestamp = f"{time_diff.seconds // 3600} hours ago" if time_diff.seconds >= 3600 else f"{time_diff.seconds // 60} minutes ago"
            else:
                timestamp = f"{time_diff.days} days ago"
            
            recent_activities.append({
                'title': 'Grade Received',
                'description': f"{assignment.title} graded: {submission.percentage}%",
                'timestamp': timestamp
            })
    
    # Sort activities by most recent
    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'])[:5]
    
    return render_template('students/dashboard.html',
                         school=school,
                         stats=stats,
                         recent_activities=recent_activities,
                         recent_assignments=recent_assignments,
                         upcoming_deadlines=upcoming_deadlines,
                         recent_grades=recent_grades,
                         now=datetime.now())

@bp.route('/assignments')
@login_required
def assignments():
    """View assignments and submissions"""
    error = require_student()
    if error:
        return error
    
    # Get all assignments for the student's school that are published
    try:
        assignments = Assignment.query.filter_by(
            school_id=current_user.school_id,
            is_published=True,
            is_active=True
        ).order_by(Assignment.due_date.desc()).all()
    except Exception as e:
        # Fallback if there are issues with the query
        assignments = []
    
    # Get submissions for these assignments
    submission_dict = {}
    if assignments:
        from app.models import Submission
        assignment_ids = [a.id for a in assignments]
        submissions = Submission.query.filter(
            Submission.assignment_id.in_(assignment_ids),
            Submission.student_id == current_user.id
        ).all()
        submission_dict = {s.assignment_id: s for s in submissions}
    
    return render_template('students/assignments.html', 
                          assignments=assignments,
                          submissions=submission_dict)


@bp.route('/calendar')
@login_required
def calendar():
    """Calendar and scheduling for students"""
    error = require_student()
    if error:
        return error
    
    return render_template('calendar/dashboard.html')


@bp.route('/grades')
@login_required
def grades():
    """View grades and progress reports"""
    error = require_student()
    if error:
        return error
    
    # Get real grades from database
    from app.models import Submission
    
    # Get all submissions for this student
    submissions = Submission.query.filter_by(student_id=current_user.id).all()
    
    # Get assignments for this student's school
    assignments = Assignment.query.filter_by(
        school_id=current_user.school_id,
        is_published=True
    ).all()
    
    # Build grades data
    grades = []
    subjects = set()
    
    for submission in submissions:
        assignment = next((a for a in assignments if a.id == submission.assignment_id), None)
        if assignment and submission.percentage is not None:
            subjects.add(assignment.subject)
            grades.append({
                'assignment_id': assignment.id,
                'assignment_title': assignment.title,
                'subject': assignment.subject,
                'score': submission.percentage,
                'max_score': assignment.max_score or 100,
                'submitted_at': submission.submitted_at,
                'graded_at': submission.graded_at,
                'feedback': submission.feedback
            })
    
    # Sort grades by graded_at (most recent first)
    grades = sorted(grades, key=lambda x: x['graded_at'] or x['submitted_at'], reverse=True)
    subjects = sorted(list(subjects))
    
    return render_template('students/grades.html', grades=grades, subjects=subjects)

@bp.route('/library')
@login_required
def library():
    """Access digital library and learning resources"""
    error = require_student()
    if error:
        return error
    
    # Get library resources from database
    from app.models.library import LibraryResource
    
    try:
        # Get resources available to student's school
        resources = LibraryResource.query.filter_by(
            school_id=current_user.school_id,
            is_active=True
        ).order_by(LibraryResource.title).all()
    except Exception:
        # Fallback if library model doesn't exist yet
        resources = []
    
    return render_template('students/library.html', resources=resources)

@bp.route('/progress')
@login_required
def progress():
    """View student progress and analytics"""
    error = require_student()
    if error:
        return error
    
    return render_template('students/progress_dashboard.html',
                           student_id=current_user.id)


@bp.route('/profile')
@login_required
def profile():
    """View and edit student profile"""
    error = require_student()
    if error:
        return error
    
    return render_template('students/profile.html', user=current_user)