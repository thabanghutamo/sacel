from app.extensions import db
from datetime import datetime

class LibraryItem(db.Model):
    __tablename__ = 'library_items'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(100))
    grade_level = db.Column(db.String(50))  # Can be multiple grades like "8-10"
    content_type = db.Column(db.Enum('textbook', 'workbook', 'reference', 'multimedia', 'document', name='content_type'), nullable=False)
    
    # File information
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)  # Size in bytes
    file_type = db.Column(db.String(50))  # pdf, doc, video, etc.
    
    # Searchable content
    indexed_content = db.Column(db.Text)  # Extracted text for AI search
    page_count = db.Column(db.Integer)
    
    # Metadata
    author = db.Column(db.String(200))
    publisher = db.Column(db.String(200))
    isbn = db.Column(db.String(20))
    publication_year = db.Column(db.Integer)
    language = db.Column(db.String(10), default='en')
    
    # Access control
    is_public = db.Column(db.Boolean, default=True)
    allowed_grades = db.Column(db.Text)  # JSON array of allowed grades
    
    # Usage tracking
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School')
    uploader = db.relationship('User')
    
    def __repr__(self):
        return f'<LibraryItem {self.title}>'

class StudentAnalytics(db.Model):
    __tablename__ = 'student_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    
    # Performance metrics
    total_assignments = db.Column(db.Integer, default=0)
    completed_assignments = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    improvement_trend = db.Column(db.Float, default=0.0)  # Positive = improving
    
    # Time analytics
    total_study_time_minutes = db.Column(db.Integer, default=0)
    average_time_per_assignment = db.Column(db.Float, default=0.0)
    
    # Engagement metrics
    login_frequency = db.Column(db.Integer, default=0)  # Per week
    resource_downloads = db.Column(db.Integer, default=0)
    ai_interactions = db.Column(db.Integer, default=0)
    
    # Weakness areas (JSON array of topics)
    weakness_areas = db.Column(db.Text)
    strength_areas = db.Column(db.Text)
    
    # Language preferences and usage
    preferred_language = db.Column(db.String(10), default='en')
    translation_usage = db.Column(db.Integer, default=0)
    
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student')
    
    def __repr__(self):
        return f'<StudentAnalytics {self.student_id} - {self.subject}>'

class TeacherAnalytics(db.Model):
    __tablename__ = 'teacher_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    
    # Assignment metrics
    assignments_created = db.Column(db.Integer, default=0)
    ai_generated_assignments = db.Column(db.Integer, default=0)
    average_grading_time = db.Column(db.Float, default=0.0)  # Minutes
    
    # Student performance metrics
    class_average_score = db.Column(db.Float, default=0.0)
    pass_rate = db.Column(db.Float, default=0.0)
    improvement_rate = db.Column(db.Float, default=0.0)
    
    # Coverage tracking
    topics_covered = db.Column(db.Text)  # JSON array of topics
    curriculum_completion = db.Column(db.Float, default=0.0)  # Percentage
    
    # Engagement metrics
    student_feedback_score = db.Column(db.Float, default=0.0)
    resource_uploads = db.Column(db.Integer, default=0)
    
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    teacher = db.relationship('Teacher')
    
    def __repr__(self):
        return f'<TeacherAnalytics {self.teacher_id} - {self.subject}>'

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # login, grade_assignment, etc.
    target_type = db.Column(db.String(50))  # user, assignment, application, etc.
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string with additional details
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class SchoolGallery(db.Model):
    __tablename__ = 'school_gallery'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(300))
    display_order = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)  # For homepage display
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='gallery_images')
    uploader = db.relationship('User')
    
    def __repr__(self):
        return f'<SchoolGallery {self.school.name} - {self.caption}>'