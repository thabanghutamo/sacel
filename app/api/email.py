"""
Email API endpoints for SACEL Platform
Provides REST API for sending various types of email notifications
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.email_service import email_service
from app.models import User, Assignment, Application, School
from app.extensions import db
from datetime import datetime
from typing import List, Dict, Any

email_bp = Blueprint('email', __name__)


@email_bp.route('/send-assignment-notification', methods=['POST'])
@login_required
def send_assignment_notification():
    """Send assignment notification to student(s)"""
    try:
        # Only teachers and admins can send assignment notifications
        if current_user.role.value not in ['teacher', 'school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        required_fields = ['student_emails', 'assignment_title', 'assignment_id', 'due_date', 'subject']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        student_emails = data['student_emails']
        if not isinstance(student_emails, list):
            student_emails = [student_emails]
        
        # Send emails to all students
        success_count = 0
        errors = []
        
        for email in student_emails:
            user = User.query.filter_by(email=email).first()
            if user:
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                success = email_service.send_assignment_notification(
                    student_email=email,
                    student_name=f"{user.first_name} {user.last_name}",
                    assignment_title=data['assignment_title'],
                    assignment_id=data['assignment_id'],
                    due_date=due_date,
                    teacher_name=f"{current_user.first_name} {current_user.last_name}",
                    subject=data['subject']
                )
                if success:
                    success_count += 1
                else:
                    errors.append(f"Failed to send to {email}")
            else:
                errors.append(f"User not found: {email}")
        
        return jsonify({
            'success': True,
            'sent': success_count,
            'total': len(student_emails),
            'errors': errors
        })
        
    except Exception as e:
        current_app.logger.error(f"Assignment notification error: {e}")
        return jsonify({'error': 'Failed to send notifications'}), 500


@email_bp.route('/send-grade-notification', methods=['POST'])
@login_required
def send_grade_notification():
    """Send grade notification to student"""
    try:
        # Only teachers and admins can send grade notifications
        if current_user.role.value not in ['teacher', 'school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        required_fields = ['student_email', 'assignment_title', 'grade', 'subject']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        user = User.query.filter_by(email=data['student_email']).first()
        if not user:
            return jsonify({'error': 'Student not found'}), 404
        
        success = email_service.send_grade_notification(
            student_email=data['student_email'],
            student_name=f"{user.first_name} {user.last_name}",
            assignment_title=data['assignment_title'],
            grade=data['grade'],
            feedback=data.get('feedback', ''),
            teacher_name=f"{current_user.first_name} {current_user.last_name}",
            subject=data['subject']
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Grade notification sent'})
        else:
            return jsonify({'error': 'Failed to send notification'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Grade notification error: {e}")
        return jsonify({'error': 'Failed to send notification'}), 500


@email_bp.route('/send-admission-notification', methods=['POST'])
@login_required  
def send_admission_notification():
    """Send admission status notification"""
    try:
        # Only admins can send admission notifications
        if current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        required_fields = ['applicant_email', 'school_name', 'status', 'application_id']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate status
        valid_statuses = ['accepted', 'rejected', 'pending', 'waitlisted']
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        success = email_service.send_admission_status_notification(
            applicant_email=data['applicant_email'],
            applicant_name=data.get('applicant_name', 'Applicant'),
            school_name=data['school_name'],
            status=data['status'],
            application_id=str(data['application_id']),
            additional_info=data.get('additional_info')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Admission notification sent'})
        else:
            return jsonify({'error': 'Failed to send notification'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Admission notification error: {e}")
        return jsonify({'error': 'Failed to send notification'}), 500


@email_bp.route('/send-system-announcement', methods=['POST'])
@login_required
def send_system_announcement():
    """Send system-wide announcement"""
    try:
        # Only system admins can send system announcements
        if current_user.role.value != 'system_admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        required_fields = ['title', 'content', 'recipient_type']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get recipients based on type
        recipient_emails = []
        recipient_type = data['recipient_type']
        
        if recipient_type == 'all':
            users = User.query.all()
            recipient_emails = [user.email for user in users if user.email]
        elif recipient_type == 'students':
            users = User.query.filter_by(role='student').all()
            recipient_emails = [user.email for user in users if user.email]
        elif recipient_type == 'teachers':
            users = User.query.filter_by(role='teacher').all()
            recipient_emails = [user.email for user in users if user.email]
        elif recipient_type == 'admins':
            users = User.query.filter(User.role.in_(['school_admin', 'principal', 'system_admin'])).all()
            recipient_emails = [user.email for user in users if user.email]
        elif recipient_type == 'custom':
            recipient_emails = data.get('custom_emails', [])
        else:
            return jsonify({'error': 'Invalid recipient type'}), 400
        
        if not recipient_emails:
            return jsonify({'error': 'No recipients found'}), 400
        
        # Send announcement in batches to avoid email limits
        batch_size = 50
        success_count = 0
        
        for i in range(0, len(recipient_emails), batch_size):
            batch = recipient_emails[i:i+batch_size]
            success = email_service.send_system_announcement(
                recipient_emails=batch,
                announcement_title=data['title'],
                content=data['content'],
                priority=data.get('priority', 'normal'),
                author=f"{current_user.first_name} {current_user.last_name}"
            )
            if success:
                success_count += len(batch)
        
        return jsonify({
            'success': True,
            'message': f'Announcement sent to {success_count} recipients',
            'total_sent': success_count,
            'total_recipients': len(recipient_emails)
        })
        
    except Exception as e:
        current_app.logger.error(f"System announcement error: {e}")
        return jsonify({'error': 'Failed to send announcement'}), 500


@email_bp.route('/send-teacher-notification', methods=['POST'])
@login_required
def send_teacher_notification():
    """Send notification to teacher"""
    try:
        # Only admins and the system can send teacher notifications
        if current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        required_fields = ['teacher_email', 'notification_type', 'details']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        teacher = User.query.filter_by(email=data['teacher_email'], role='teacher').first()
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404
        
        success = email_service.send_teacher_notification(
            teacher_email=data['teacher_email'],
            teacher_name=f"{teacher.first_name} {teacher.last_name}",
            notification_type=data['notification_type'],
            details=data['details']
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Teacher notification sent'})
        else:
            return jsonify({'error': 'Failed to send notification'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Teacher notification error: {e}")
        return jsonify({'error': 'Failed to send notification'}), 500


@email_bp.route('/send-welcome-email', methods=['POST'])
@login_required
def send_welcome_email():
    """Send welcome email to new user"""
    try:
        # Only admins can send welcome emails
        if current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        required_fields = ['user_email', 'user_name', 'user_role']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        success = email_service.send_welcome_email(
            user_email=data['user_email'],
            user_name=data['user_name'],
            user_role=data['user_role'],
            temporary_password=data.get('temporary_password')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Welcome email sent'})
        else:
            return jsonify({'error': 'Failed to send welcome email'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Welcome email error: {e}")
        return jsonify({'error': 'Failed to send welcome email'}), 500


@email_bp.route('/test-email', methods=['POST'])
@login_required
def test_email():
    """Test email configuration"""
    try:
        # Only system admins can test email
        if current_user.role.value != 'system_admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        test_email = data.get('test_email', current_user.email)
        
        success = email_service.send_system_announcement(
            recipient_emails=[test_email],
            announcement_title="SACEL Email Test",
            content="This is a test email to verify that the email system is working correctly.",
            priority='normal',
            author='System Test'
        )
        
        if success:
            return jsonify({'success': True, 'message': f'Test email sent to {test_email}'})
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Test email error: {e}")
        return jsonify({'error': 'Failed to send test email'}), 500


@email_bp.route('/email-stats', methods=['GET'])
@login_required
def get_email_stats():
    """Get email system statistics"""
    try:
        # Only admins can view email stats
        if current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get user counts for different roles
        total_users = User.query.count()
        students = User.query.filter_by(role='student').count()
        teachers = User.query.filter_by(role='teacher').count()
        admins = User.query.filter(User.role.in_(['school_admin', 'principal', 'system_admin'])).count()
        
        stats = {
            'total_users': total_users,
            'students': students,
            'teachers': teachers,
            'admins': admins,
            'email_configured': bool(email_service.smtp_username and email_service.smtp_password),
            'smtp_server': email_service.smtp_server,
            'smtp_port': email_service.smtp_port
        }
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f"Email stats error: {e}")
        return jsonify({'error': 'Failed to get email stats'}), 500