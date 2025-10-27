from app.extensions import db
from datetime import datetime
from app.models import ApplicationStatus, MatchScore

from app.extensions import db
from datetime import datetime
from app.models import ApplicationStatus, MatchScore

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
        return f'<Application {self.reference_number} - {self.student_first_name} {self.student_last_name}>'

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    assignment_type = db.Column(db.Enum('homework', 'classwork', 'test', 'exam', 'project', name='assignment_type'), nullable=False)
    
    # Content and files
    content = db.Column(db.Text)  # Rich text content
    file_references = db.Column(db.Text)  # JSON string of uploaded files
    
    # Scheduling
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    
    # Grading configuration
    total_marks = db.Column(db.Integer, default=100)
    pass_mark = db.Column(db.Integer, default=50)
    question_config = db.Column(db.Text)  # JSON configuration for questions
    
    # AI generation metadata
    ai_generated = db.Column(db.Boolean, default=False)
    ai_prompt = db.Column(db.Text, nullable=True)
    ai_model_version = db.Column(db.String(50), nullable=True)
    
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School')
    teacher = db.relationship('Teacher', backref='assignments')
    
    def __repr__(self):
        return f'<Assignment {self.title}>'

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Submission content
    answers = db.Column(db.Text)  # JSON string of answers
    file_references = db.Column(db.Text)  # JSON string of uploaded files
    
    # Grading and feedback
    score = db.Column(db.Float, nullable=True)
    percentage = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text)
    ai_feedback = db.Column(db.Text)  # AI-generated feedback
    teacher_feedback = db.Column(db.Text)  # Teacher's additional feedback
    
    # Analytics
    time_spent_minutes = db.Column(db.Integer, default=0)
    attempt_number = db.Column(db.Integer, default=1)
    
    # Status and timestamps
    status = db.Column(db.Enum('draft', 'submitted', 'graded', 'returned', name='submission_status'), default='draft')
    submitted_at = db.Column(db.DateTime, nullable=True)
    graded_at = db.Column(db.DateTime, nullable=True)
    graded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # AI grading metadata
    ai_graded = db.Column(db.Boolean, default=False)
    ai_confidence = db.Column(db.Float, nullable=True)
    requires_manual_review = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = db.relationship('Assignment', backref='submissions')
    student = db.relationship('Student', backref='submissions')
    grader = db.relationship('User')
    
    def __repr__(self):
        return f'<Submission {self.id} - {self.assignment.title}>'