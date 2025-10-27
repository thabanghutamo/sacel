"""
Email Service for SACEL Platform
Handles all email notifications including assignments, grades, and system alerts
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Optional, Dict, Any
from flask import current_app, render_template_string
from jinja2 import Template


class EmailService:
    """Comprehensive email service for educational platform notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@sacel.org.za')
        self.from_name = os.getenv('FROM_NAME', 'SACEL Platform')
        
    def _create_connection(self):
        """Create SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            return server
        except Exception as e:
            current_app.logger.error(f"Failed to connect to SMTP server: {e}")
            return None
    
    def _send_email(self, to_emails: List[str], subject: str, 
                   html_content: str, text_content: str = None,
                   attachments: List[Dict] = None) -> bool:
        """Send email with optional attachments"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text version if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    with open(attachment['path'], 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)
            
            # Send email
            server = self._create_connection()
            if server:
                server.send_message(msg)
                server.quit()
                return True
            return False
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {e}")
            return False
    
    def send_assignment_notification(self, student_email: str, student_name: str,
                                   assignment_title: str, assignment_id: int,
                                   due_date: datetime, teacher_name: str,
                                   subject: str) -> bool:
        """Send new assignment notification to student"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .assignment-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎓 SACEL - New Assignment</h1>
            </div>
            <div class="content">
                <h2>Hello {{ student_name }}!</h2>
                <p>You have a new assignment that requires your attention.</p>
                
                <div class="assignment-details">
                    <h3>📚 {{ assignment_title }}</h3>
                    <p><strong>Subject:</strong> {{ subject }}</p>
                    <p><strong>Teacher:</strong> {{ teacher_name }}</p>
                    <p><strong>Due Date:</strong> {{ due_date.strftime('%B %d, %Y at %I:%M %p') }}</p>
                    
                    <a href="http://localhost:5000/students/assignments/{{ assignment_id }}" class="btn">
                        View Assignment
                    </a>
                </div>
                
                <p>Please log in to your student portal to view the complete assignment details and submit your work.</p>
                <p>If you have any questions, please contact your teacher or school administration.</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            student_name=student_name,
            assignment_title=assignment_title,
            assignment_id=assignment_id,
            due_date=due_date,
            teacher_name=teacher_name,
            subject=subject
        )
        
        subject_line = f"📚 New Assignment: {assignment_title}"
        return self._send_email([student_email], subject_line, html_content)
    
    def send_grade_notification(self, student_email: str, student_name: str,
                               assignment_title: str, grade: str, 
                               feedback: str, teacher_name: str,
                               subject: str) -> bool:
        """Send grade notification to student"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: #059669; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .grade-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669; }
                .grade { font-size: 2em; font-weight: bold; color: #059669; text-align: center; margin: 10px 0; }
                .feedback { background: #f0f9ff; padding: 15px; border-radius: 6px; margin: 15px 0; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 SACEL - Assignment Graded</h1>
            </div>
            <div class="content">
                <h2>Hello {{ student_name }}!</h2>
                <p>Your assignment has been graded and feedback is available.</p>
                
                <div class="grade-card">
                    <h3>📝 {{ assignment_title }}</h3>
                    <p><strong>Subject:</strong> {{ subject }}</p>
                    <p><strong>Teacher:</strong> {{ teacher_name }}</p>
                    
                    <div class="grade">{{ grade }}</div>
                    
                    {% if feedback %}
                    <div class="feedback">
                        <h4>📋 Teacher Feedback:</h4>
                        <p>{{ feedback }}</p>
                    </div>
                    {% endif %}
                    
                    <a href="http://localhost:5000/students/assignments" class="btn">
                        View All Grades
                    </a>
                </div>
                
                <p>Keep up the great work! Continue to engage with your assignments and strive for excellence.</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            student_name=student_name,
            assignment_title=assignment_title,
            grade=grade,
            feedback=feedback,
            teacher_name=teacher_name,
            subject=subject
        )
        
        subject_line = f"🎯 Grade Available: {assignment_title} - {grade}"
        return self._send_email([student_email], subject_line, html_content)
    
    def send_admission_status_notification(self, applicant_email: str, 
                                         applicant_name: str, school_name: str,
                                         status: str, application_id: str,
                                         additional_info: str = None) -> bool:
        """Send admission status update to applicant"""
        
        status_colors = {
            'accepted': '#059669',
            'rejected': '#dc2626',
            'pending': '#d97706',
            'waitlisted': '#7c3aed'
        }
        
        status_icons = {
            'accepted': '🎉',
            'rejected': '😔',
            'pending': '⏳',
            'waitlisted': '📝'
        }
        
        color = status_colors.get(status, '#6b7280')
        icon = status_icons.get(status, '📧')
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: {{ color }}; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .status-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {{ color }}; }
                .status { font-size: 1.5em; font-weight: bold; color: {{ color }}; text-align: center; margin: 15px 0; text-transform: uppercase; }
                .info { background: #f0f9ff; padding: 15px; border-radius: 6px; margin: 15px 0; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: {{ color }}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ icon }} SACEL - Admission Update</h1>
            </div>
            <div class="content">
                <h2>Dear {{ applicant_name }},</h2>
                <p>We have an update regarding your application to {{ school_name }}.</p>
                
                <div class="status-card">
                    <h3>📋 Application #{{ application_id }}</h3>
                    <p><strong>School:</strong> {{ school_name }}</p>
                    
                    <div class="status">{{ status }}</div>
                    
                    {% if additional_info %}
                    <div class="info">
                        <h4>📌 Additional Information:</h4>
                        <p>{{ additional_info }}</p>
                    </div>
                    {% endif %}
                    
                    <a href="http://localhost:5000/admissions/status?id={{ application_id }}" class="btn">
                        View Application Status
                    </a>
                </div>
                
                <p>For any questions about your application, please contact the school administration or visit our platform.</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            applicant_name=applicant_name,
            school_name=school_name,
            status=status.title(),
            application_id=application_id,
            additional_info=additional_info,
            color=color,
            icon=icon
        )
        
        subject_line = f"{icon} Admission Update: {school_name} - {status.title()}"
        return self._send_email([applicant_email], subject_line, html_content)
    
    def send_system_announcement(self, recipient_emails: List[str], 
                               announcement_title: str, content: str,
                               priority: str = 'normal', 
                               author: str = 'SACEL Admin') -> bool:
        """Send system-wide announcements"""
        
        priority_colors = {
            'low': '#6b7280',
            'normal': '#2563eb', 
            'high': '#d97706',
            'urgent': '#dc2626'
        }
        
        priority_icons = {
            'low': '📢',
            'normal': '📢',
            'high': '⚠️',
            'urgent': '🚨'
        }
        
        color = priority_colors.get(priority, '#2563eb')
        icon = priority_icons.get(priority, '📢')
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: {{ color }}; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .announcement { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {{ color }}; }
                .priority { background: {{ color }}; color: white; padding: 5px 15px; border-radius: 20px; font-size: 12px; text-transform: uppercase; display: inline-block; margin: 10px 0; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: {{ color }}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ icon }} SACEL - System Announcement</h1>
            </div>
            <div class="content">
                <div class="announcement">
                    <div class="priority">{{ priority }} Priority</div>
                    <h2>{{ announcement_title }}</h2>
                    <p><strong>From:</strong> {{ author }}</p>
                    <p><strong>Date:</strong> {{ current_date }}</p>
                    
                    <div style="margin: 20px 0; padding: 15px; background: #f8fafc; border-radius: 6px;">
                        {{ content | safe }}
                    </div>
                    
                    <a href="http://localhost:5000/" class="btn">
                        Access Platform
                    </a>
                </div>
                
                <p>Please log in to your account for more details and to stay updated with the latest announcements.</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            announcement_title=announcement_title,
            content=content,
            priority=priority.title(),
            author=author,
            current_date=datetime.now().strftime('%B %d, %Y at %I:%M %p'),
            color=color,
            icon=icon
        )
        
        subject_line = f"{icon} {priority.title()} Announcement: {announcement_title}"
        return self._send_email(recipient_emails, subject_line, html_content)
    
    def send_teacher_notification(self, teacher_email: str, teacher_name: str,
                                notification_type: str, details: Dict[str, Any]) -> bool:
        """Send notifications to teachers for various events"""
        
        if notification_type == 'new_submission':
            return self._send_submission_notification(teacher_email, teacher_name, details)
        elif notification_type == 'grade_reminder':
            return self._send_grading_reminder(teacher_email, teacher_name, details)
        elif notification_type == 'schedule_update':
            return self._send_schedule_update(teacher_email, teacher_name, details)
        
        return False
    
    def _send_submission_notification(self, teacher_email: str, teacher_name: str,
                                    details: Dict[str, Any]) -> bool:
        """Notify teacher of new assignment submission"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: #7c3aed; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .submission-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #7c3aed; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #7c3aed; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📄 SACEL - New Submission</h1>
            </div>
            <div class="content">
                <h2>Hello {{ teacher_name }}!</h2>
                <p>A student has submitted their assignment and is ready for your review.</p>
                
                <div class="submission-card">
                    <h3>📝 {{ assignment_title }}</h3>
                    <p><strong>Student:</strong> {{ student_name }}</p>
                    <p><strong>Submitted:</strong> {{ submission_date }}</p>
                    <p><strong>Status:</strong> Ready for Grading</p>
                    
                    <a href="http://localhost:5000/teachers/grading/{{ assignment_id }}" class="btn">
                        Review Submission
                    </a>
                </div>
                
                <p>Please review the submission and provide feedback to help the student learn and improve.</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            teacher_name=teacher_name,
            assignment_title=details.get('assignment_title'),
            student_name=details.get('student_name'),
            submission_date=details.get('submission_date'),
            assignment_id=details.get('assignment_id')
        )
        
        subject_line = f"📄 New Submission: {details.get('assignment_title')}"
        return self._send_email([teacher_email], subject_line, html_content)
    
    def _send_grading_reminder(self, teacher_email: str, teacher_name: str,
                             details: Dict[str, Any]) -> bool:
        """Send grading reminder to teacher"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: #d97706; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .reminder-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #d97706; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #d97706; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
                .pending-count { font-size: 2em; font-weight: bold; color: #d97706; text-align: center; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⏰ SACEL - Grading Reminder</h1>
            </div>
            <div class="content">
                <h2>Hello {{ teacher_name }}!</h2>
                <p>You have assignments waiting to be graded. Students are eager to receive their feedback!</p>
                
                <div class="reminder-card">
                    <h3>📚 Pending Assignments</h3>
                    <div class="pending-count">{{ pending_count }}</div>
                    <p>assignments ready for grading</p>
                    
                    <a href="http://localhost:5000/teachers/grading" class="btn">
                        Grade Assignments
                    </a>
                </div>
                
                <p>Timely feedback helps students learn more effectively. Thank you for your dedication to education!</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            teacher_name=teacher_name,
            pending_count=details.get('pending_count', 0)
        )
        
        subject_line = f"⏰ Grading Reminder: {details.get('pending_count', 0)} assignments pending"
        return self._send_email([teacher_email], subject_line, html_content)
    
    def send_welcome_email(self, user_email: str, user_name: str, 
                          user_role: str, temporary_password: str = None) -> bool:
        """Send welcome email to new users"""
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background: #059669; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .welcome-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669; }
                .credentials { background: #fef3c7; padding: 15px; border-radius: 6px; margin: 15px 0; border: 1px solid #f59e0b; }
                .footer { background: #374151; color: white; padding: 15px; text-align: center; font-size: 12px; }
                .btn { background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎓 Welcome to SACEL!</h1>
            </div>
            <div class="content">
                <h2>Hello {{ user_name }}!</h2>
                <p>Welcome to the South African Comprehensive Education & Learning platform.</p>
                
                <div class="welcome-card">
                    <h3>🚀 Your Account is Ready</h3>
                    <p><strong>Role:</strong> {{ user_role.replace('_', ' ').title() }}</p>
                    <p><strong>Email:</strong> {{ user_email }}</p>
                    
                    {% if temporary_password %}
                    <div class="credentials">
                        <h4>🔐 Login Credentials</h4>
                        <p><strong>Temporary Password:</strong> {{ temporary_password }}</p>
                        <p><em>Please change your password after your first login for security.</em></p>
                    </div>
                    {% endif %}
                    
                    <a href="http://localhost:5000/auth/login" class="btn">
                        Login to Platform
                    </a>
                </div>
                
                <h3>🌟 Platform Features:</h3>
                <ul>
                    {% if user_role == 'student' %}
                    <li>📚 Access assignments and coursework</li>
                    <li>📊 View grades and progress reports</li>
                    <li>📁 Upload and manage files</li>
                    <li>🌍 Multi-language support</li>
                    {% elif user_role == 'teacher' %}
                    <li>📝 Create and manage assignments</li>
                    <li>🎯 AI-powered grading tools</li>
                    <li>📊 Student analytics and insights</li>
                    <li>📁 File management system</li>
                    {% elif user_role in ['school_admin', 'principal'] %}
                    <li>👥 User management</li>
                    <li>📊 School analytics dashboard</li>
                    <li>📋 Admission management</li>
                    <li>🔧 System administration</li>
                    {% endif %}
                </ul>
                
                <p>If you have any questions, please contact our support team or your school administrator.</p>
            </div>
            <div class="footer">
                <p>© 2025 SACEL Platform - South African Comprehensive Education & Learning</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            user_name=user_name,
            user_email=user_email,
            user_role=user_role,
            temporary_password=temporary_password
        )
        
        subject_line = "🎓 Welcome to SACEL Platform!"
        return self._send_email([user_email], subject_line, html_content)


# Global email service instance
email_service = EmailService()