"""
Admin dashboard and management interfaces for SACEL
Provides administrative functions for system administrators and school admins
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, School, Student, Teacher, Application, UserRole, ApplicationStatus
from app.extensions import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta

bp = Blueprint('admin', __name__)

def require_admin():
    """Decorator to require admin access"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    allowed_roles = [UserRole.SYSTEM_ADMIN, UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL]
    if current_user.role not in allowed_roles:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('public.home'))
    
    return None

@bp.route('/dashboard')
@login_required
def dashboard():
    """Main admin dashboard with key metrics and analytics"""
    error = require_admin()
    if error:
        return error
    
    # Get dashboard statistics
    try:
        stats = {
            'total_users': User.query.count(),
            'total_students': User.query.filter_by(role=UserRole.STUDENT).count(),
            'total_teachers': User.query.filter_by(role=UserRole.TEACHER).count(),
            'total_schools': School.query.count(),
            'pending_applications': Application.query.filter_by(status='submitted').count(),
            'recent_registrations': User.query.filter(
                User.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count() if hasattr(User, 'created_at') else 0
        }
        
        # Get recent activity
        recent_users = User.query.order_by(desc(User.id)).limit(5).all()
        recent_applications = Application.query.order_by(desc(Application.created_at)).limit(5).all() if hasattr(Application, 'created_at') else []
        
        return render_template('admin/dashboard.html', 
                             stats=stats, 
                             recent_users=recent_users,
                             recent_applications=recent_applications)
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/dashboard.html', 
                             stats={}, 
                             recent_users=[], 
                             recent_applications=[])


@bp.route('/email')
@login_required
def email_management():
    """Email configuration and management page"""
    error = require_admin()
    if error:
        return error
    
    return render_template('admin/email.html')
    if error:
        return error
    
    # Get dashboard statistics
    stats = {}
    
    # System-wide stats for system admins
    if current_user.role == UserRole.SYSTEM_ADMIN:
        stats.update({
            'total_users': User.query.count(),
            'total_schools': School.query.count(),
            'total_students': User.query.filter_by(role=UserRole.STUDENT).count(),
            'total_teachers': User.query.filter_by(role=UserRole.TEACHER).count(),
            'total_applications': Application.query.count(),
            'pending_applications': Application.query.filter_by(
                status='submitted'
            ).count()
        })
        schools = School.query.all()
    else:
        # School-specific stats for school admins
        school_id = current_user.school_id
        stats.update({
            'school_students': User.query.filter_by(role=UserRole.STUDENT, school_id=school_id).count(),
            'school_teachers': User.query.filter_by(role=UserRole.TEACHER, school_id=school_id).count(),
            'school_applications': Application.query.filter_by(school_id=school_id).count(),
            'pending_school_applications': Application.query.filter_by(
                school_id=school_id, 
                status='submitted'
            ).count()
        })
        schools = [current_user.school] if current_user.school else []
    
    # Recent activity
    recent_applications = Application.query.order_by(desc(Application.created_at)).limit(10).all()
    
    # User growth over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    user_growth = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago).group_by(
        func.date(User.created_at)
    ).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         schools=schools,
                         recent_applications=recent_applications,
                         user_growth=user_growth)

@bp.route('/users')
@login_required
def users():
    """User management interface"""
    error = require_admin()
    if error:
        return error
    
    # Get filter parameters
    role_filter = request.args.get('role', '')
    school_filter = request.args.get('school', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = User.query
    
    # Apply filters
    if role_filter:
        query = query.filter(User.role == UserRole(role_filter))
    
    if school_filter:
        query = query.filter(User.school_id == int(school_filter))
    
    if search:
        query = query.filter(
            (User.first_name.ilike(f'%{search}%')) |
            (User.last_name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    # School admins can only see users in their school
    if current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL]:
        query = query.filter(User.school_id == current_user.school_id)
    
    # Paginate results
    users = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get schools for filter dropdown
    if current_user.role == UserRole.SYSTEM_ADMIN:
        schools = School.query.all()
    else:
        schools = [current_user.school] if current_user.school else []
    
    return render_template('admin/users.html',
                         users=users,
                         schools=schools,
                         UserRole=UserRole,
                         current_filters={
                             'role': role_filter,
                             'school': school_filter,
                             'search': search
                         })

@bp.route('/schools')
@login_required
def schools():
    """School management interface (system admin only)"""
    if current_user.role != UserRole.SYSTEM_ADMIN:
        flash('Access denied. System admin privileges required.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = School.query
    if search:
        query = query.filter(
            (School.name.ilike(f'%{search}%')) |
            (School.city.ilike(f'%{search}%')) |
            (School.province.ilike(f'%{search}%'))
        )
    
    schools = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/schools.html',
                         schools=schools,
                         search=search)

@bp.route('/applications')
@login_required
def applications():
    """Application management interface"""
    error = require_admin()
    if error:
        return error
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    school_filter = request.args.get('school', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = Application.query
    
    # Apply filters
    if status_filter:
        query = query.filter(Application.status == status_filter)
    
    if school_filter:
        query = query.filter(Application.school_id == int(school_filter))
    
    # School admins can only see applications for their school
    if current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL]:
        query = query.filter(Application.school_id == current_user.school_id)
    
    # Order by most recent first
    query = query.order_by(desc(Application.created_at))
    
    # Paginate results
    applications = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get schools for filter dropdown
    if current_user.role == UserRole.SYSTEM_ADMIN:
        schools = School.query.all()
    else:
        schools = [current_user.school] if current_user.school else []
    
    return render_template('admin/applications.html',
                         applications=applications,
                         schools=schools,
                         ApplicationStatus=ApplicationStatus,
                         current_filters={
                             'status': status_filter,
                             'school': school_filter
                         })

@bp.route('/application/<int:application_id>')
@login_required
def application_detail(application_id):
    """View and manage individual application"""
    error = require_admin()
    if error:
        return error
    
    application = Application.query.get_or_404(application_id)
    
    # School admins can only see applications for their school
    if current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL]:
        if application.school_id != current_user.school_id:
            flash('Access denied.', 'error')
            return redirect(url_for('admin.applications'))
    
    return render_template('admin/application_detail.html', application=application)

@bp.route('/application/<int:application_id>/update', methods=['POST'])
@login_required
def update_application(application_id):
    """Update application status"""
    error = require_admin()
    if error:
        return error
    
    application = Application.query.get_or_404(application_id)
    
    # School admins can only update applications for their school
    if current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL]:
        if application.school_id != current_user.school_id:
            return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    notes = data.get('notes', '')
    
    if new_status not in [status.value for status in ApplicationStatus]:
        return jsonify({'error': 'Invalid status'}), 400
    
    application.status = new_status
    application.admin_notes = notes
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Application status updated to {new_status}', 'success')
    return jsonify({'success': True})

@bp.route('/analytics')
@login_required
def analytics():
    """Analytics and reporting dashboard"""
    error = require_admin()
    if error:
        return error
    
    # Time-based analytics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Application trends
    application_trends = db.session.query(
        func.date(Application.created_at).label('date'),
        func.count(Application.id).label('count')
    ).filter(Application.created_at >= thirty_days_ago).group_by(
        func.date(Application.created_at)
    ).all()
    
    # Application status distribution
    status_distribution = db.session.query(
        Application.status,
        func.count(Application.id).label('count')
    ).group_by(Application.status).all()
    
    # School popularity (for system admin)
    school_popularity = []
    if current_user.role == UserRole.SYSTEM_ADMIN:
        school_popularity = db.session.query(
            School.name,
            func.count(Application.id).label('application_count')
        ).join(Application, School.id == Application.school_id).group_by(
            School.id, School.name
        ).order_by(desc(func.count(Application.id))).limit(10).all()
    
    # Calculate summary statistics for analytics_data
    from app.models import User
    total_users = User.query.count()
    total_schools = School.query.count()
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(
        status='submitted'
    ).count()
    
    # Recent registrations (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_registrations = User.query.filter(
        User.created_at >= seven_days_ago
    ).count()
    
    analytics_data = {
        'total_users': total_users,
        'total_schools': total_schools,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'recent_registrations': recent_registrations
    }
    
    return render_template('admin/analytics.html',
                           analytics_data=analytics_data,
                           application_trends=application_trends,
                           status_distribution=status_distribution,
                           school_popularity=school_popularity)


@bp.route('/settings')
@login_required
def settings():
    """System settings and configuration"""
    if current_user.role != UserRole.SYSTEM_ADMIN:
        flash('Access denied. System admin privileges required.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/settings.html')