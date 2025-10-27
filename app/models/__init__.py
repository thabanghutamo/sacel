from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

# Import communication models
from app.models.communication import (
    Message, MessageRecipient, ForumCategory, ForumPost, 
    ForumReply, ForumPostLike, ForumReplyLike, Notification,
    Announcement, AnnouncementView, ChatRoom, ChatParticipant, ChatMessage
)

class UserRole(Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    SCHOOL_ADMIN = "school_admin"
    PRINCIPAL = "principal"
    PARENT = "parent"
    SYSTEM_ADMIN = "system_admin"

class ApplicationStatus(Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"

class MatchScore(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    id_number = db.Column(db.String(13), unique=True, index=True)
    role = db.Column(db.Enum(UserRole), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    preferred_language = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    school = db.relationship('School', backref='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.email}>'

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    school_type = db.Column(db.Enum('public', 'private', name='school_type'), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    
    # Geographic coordinates for distance calculations
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # School branding
    logo_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7), default='#1f2937')  # Hex color
    secondary_color = db.Column(db.String(7), default='#3b82f6')
    
    # School metadata
    established_year = db.Column(db.Integer)
    student_capacity = db.Column(db.Integer)
    current_enrollment = db.Column(db.Integer, default=0)
    languages_offered = db.Column(db.Text)  # JSON string of languages
    
    # Admission settings
    admission_open = db.Column(db.Boolean, default=True)
    admission_requirements = db.Column(db.Text)  # JSON string
    
    # Performance metrics for ranking
    pass_rate = db.Column(db.Float, default=0.0)
    average_score = db.Column(db.Float, default=0.0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<School {self.name}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    learner_number = db.Column(db.String(20), unique=True, nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    subjects = db.Column(db.Text)  # JSON string of enrolled subjects
    enrollment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('active', 'inactive', 'graduated', 'transferred', name='student_status'), default='active')
    parent_guardian_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='student_profile')
    parent_guardian = db.relationship('User', foreign_keys=[parent_guardian_id])
    
    def __repr__(self):
        return f'<Student {self.learner_number}>'

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_number = db.Column(db.String(20), unique=True, nullable=False)
    subjects = db.Column(db.Text, nullable=False)  # JSON string of subjects taught
    grades = db.Column(db.Text, nullable=False)  # JSON string of grades taught
    qualifications = db.Column(db.Text)  # JSON string of qualifications
    hire_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('active', 'inactive', 'on_leave', name='teacher_status'), default='active')
    
    # Relationships
    user = db.relationship('User', backref='teacher_profile')
    
    def __repr__(self):
        return f'<Teacher {self.employee_number}>'

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    instructions = db.Column(db.Text)
    attachment_url = db.Column(db.String(500))
    due_date = db.Column(db.DateTime, nullable=False)
    max_score = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    ai_generated_content = db.Column(db.Text)  # JSON string for AI-generated questions/content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('User', backref='assignments_created')
    submissions = db.relationship('Submission', backref='assignment', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text)
    attachment_url = db.Column(db.String(500))
    grade = db.Column(db.Float, nullable=True)
    percentage = db.Column(db.Float, nullable=True)  # Grade as percentage
    feedback = db.Column(db.Text)
    status = db.Column(db.Enum('draft', 'submitted', 'graded', name='submission_status'), default='draft')
    submitted_at = db.Column(db.DateTime, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='submissions')
    grader = db.relationship('User', foreign_keys=[graded_by])
    
    def __repr__(self):
        return f'<Submission {self.id} for Assignment {self.assignment_id}>'

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Student information
    student_first_name = db.Column(db.String(100), nullable=False)
    student_last_name = db.Column(db.String(100), nullable=False)
    student_birth_date = db.Column(db.Date, nullable=False)
    grade_applying_for = db.Column(db.Integer, nullable=False)
    previous_school = db.Column(db.String(200))
    
    # Parent/Guardian information
    parent_first_name = db.Column(db.String(100), nullable=False)
    parent_last_name = db.Column(db.String(100), nullable=False)
    parent_email = db.Column(db.String(120), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    
    # Additional information
    medical_conditions = db.Column(db.Text)
    special_requirements = db.Column(db.Text)
    
    # Application processing
    status = db.Column(db.Enum('submitted', 'under_review', 'approved', 'rejected', 'waitlisted', name='application_status'), default='submitted')
    documents = db.Column(db.Text)  # JSON string of uploaded documents
    notes = db.Column(db.Text)  # Internal review notes
    
    # Timestamps and tracking
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='applications')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<Application {self.reference_number}>'