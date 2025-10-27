"""
API Documentation for SACEL Platform
Comprehensive Swagger/OpenAPI documentation for all platform endpoints
"""

from flask import Blueprint, render_template
from flask_restx import Api, Resource, fields

# Create documentation blueprint
docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/docs-home')
def api_docs_home():
    """API documentation homepage"""
    return render_template('docs/api_docs.html')

# Initialize Flask-RESTX API with comprehensive documentation
api = Api(
    docs_bp,
    version='1.0.0',
    title='SACEL Platform API',
    description='''
    ## South African Comprehensive Education & Learning Platform
    
    A comprehensive educational management system providing:
    
    ### 🎓 Core Features
    - **Student Management**: Enrollment, progress tracking, and academic records
    - **Assignment System**: AI-powered creation, submission, and grading
    - **Multi-language Support**: All 11 South African official languages
    - **Analytics Dashboard**: Comprehensive insights for students, teachers, and administrators
    - **File Management**: Secure upload, storage, and sharing system
    - **Email Notifications**: Automated communication for assignments, grades, and announcements
    - **AI Integration**: Advanced AI tools for educational content generation and grading
    
    ### 🔐 Authentication
    The API uses session-based authentication. Users must log in through the web interface
    to access protected endpoints. Role-based access control ensures appropriate permissions.
    
    ### 📊 Rate Limiting
    API requests are subject to rate limiting to ensure fair usage and system stability.
    
    ### 🌍 Internationalization
    All responses support multiple languages based on user preferences or Accept-Language headers.
    
    ### 📧 Email Integration
    The platform provides comprehensive email notification system with beautiful HTML templates
    for various educational scenarios.
    
    ### 🤖 AI-Powered Features
    - Intelligent assignment generation based on curriculum standards
    - Automated grading with detailed feedback
    - Content recommendations and personalized learning paths
    - Multi-language content translation and localization
    ''',
    doc='/docs/',
    authorizations={
        'session': {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'session'
        }
    },
    security='session'
)

# Data Models for API Documentation
user_model = api.model('User', {
    'id': fields.Integer(required=True, description='User ID'),
    'email': fields.String(required=True, description='User email address'),
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'role': fields.String(required=True, description='User role', enum=['student', 'teacher', 'school_admin', 'principal', 'system_admin']),
    'school_id': fields.Integer(description='Associated school ID'),
    'is_active': fields.Boolean(description='Account status')
})

school_model = api.model('School', {
    'id': fields.Integer(required=True, description='School ID'),
    'name': fields.String(required=True, description='School name'),
    'province': fields.String(required=True, description='Province'),
    'district': fields.String(required=True, description='District'),
    'type': fields.String(required=True, description='School type'),
    'contact_email': fields.String(description='Contact email'),
    'contact_phone': fields.String(description='Contact phone'),
    'address': fields.String(description='Physical address'),
    'is_active': fields.Boolean(description='School status')
})

assignment_model = api.model('Assignment', {
    'id': fields.Integer(required=True, description='Assignment ID'),
    'title': fields.String(required=True, description='Assignment title'),
    'description': fields.String(required=True, description='Assignment description'),
    'subject': fields.String(required=True, description='Subject area'),
    'grade_level': fields.String(required=True, description='Grade level'),
    'due_date': fields.DateTime(required=True, description='Due date'),
    'total_points': fields.Integer(description='Total points possible'),
    'teacher_id': fields.Integer(required=True, description='Teacher ID'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

email_notification_model = api.model('EmailNotification', {
    'recipient_emails': fields.List(fields.String, required=True, description='List of recipient email addresses'),
    'subject': fields.String(required=True, description='Email subject'),
    'template_type': fields.String(required=True, description='Email template type', 
                                  enum=['assignment', 'grade', 'admission', 'announcement', 'welcome']),
    'template_data': fields.Raw(required=True, description='Template-specific data'),
    'priority': fields.String(description='Email priority', enum=['low', 'normal', 'high', 'urgent'])
})

file_upload_model = api.model('FileUpload', {
    'file_type': fields.String(required=True, description='File type category', 
                              enum=['documents', 'images', 'videos', 'assignments', 'presentations']),
    'max_size': fields.Integer(description='Maximum file size in bytes'),
    'allowed_extensions': fields.List(fields.String, description='Allowed file extensions')
})

analytics_model = api.model('Analytics', {
    'student_performance': fields.Raw(description='Student performance metrics'),
    'assignment_statistics': fields.Raw(description='Assignment completion and grading statistics'),
    'engagement_metrics': fields.Raw(description='Platform engagement metrics'),
    'progress_tracking': fields.Raw(description='Learning progress indicators')
})

ai_generation_model = api.model('AIGeneration', {
    'content_type': fields.String(required=True, description='Type of content to generate',
                                 enum=['assignment', 'quiz', 'lesson_plan', 'feedback']),
    'subject': fields.String(required=True, description='Subject area'),
    'grade_level': fields.String(required=True, description='Grade level'),
    'topic': fields.String(required=True, description='Specific topic'),
    'difficulty': fields.String(description='Difficulty level', enum=['easy', 'medium', 'hard']),
    'language': fields.String(description='Content language', enum=['en', 'af', 'zu', 'xh', 'st', 'tn', 'ss', 've', 'ts', 'nr', 'nso']),
    'additional_requirements': fields.String(description='Additional content requirements')
})

# API Error Models
error_model = api.model('Error', {
    'error': fields.String(required=True, description='Error message'),
    'code': fields.Integer(description='Error code'),
    'details': fields.Raw(description='Additional error details')
})

success_model = api.model('Success', {
    'success': fields.Boolean(required=True, description='Success status'),
    'message': fields.String(description='Success message'),
    'data': fields.Raw(description='Response data')
})

# API Namespaces
auth_ns = api.namespace('auth', description='Authentication operations')
users_ns = api.namespace('users', description='User management operations')
schools_ns = api.namespace('schools', description='School management operations')
assignments_ns = api.namespace('assignments', description='Assignment management operations')
email_ns = api.namespace('email', description='Email notification operations')
files_ns = api.namespace('files', description='File management operations')
analytics_ns = api.namespace('analytics', description='Analytics and reporting operations')
ai_ns = api.namespace('ai', description='AI-powered educational tools')
language_ns = api.namespace('language', description='Multi-language support operations')

# Authentication Endpoints Documentation
@auth_ns.route('/login')
class LoginResource(Resource):
    @api.doc('user_login')
    @api.expect(api.model('LoginRequest', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password'),
        'remember_me': fields.Boolean(description='Remember login session')
    }))
    @api.marshal_with(success_model)
    def post(self):
        """Authenticate user and create session"""
        pass

@auth_ns.route('/logout')
class LogoutResource(Resource):
    @api.doc('user_logout')
    @api.marshal_with(success_model)
    def post(self):
        """End user session and logout"""
        pass

@auth_ns.route('/register')
class RegisterResource(Resource):
    @api.doc('user_register')
    @api.expect(api.model('RegisterRequest', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password'),
        'first_name': fields.String(required=True, description='First name'),
        'last_name': fields.String(required=True, description='Last name'),
        'role': fields.String(required=True, description='User role'),
        'school_id': fields.Integer(description='School ID for non-admin users')
    }))
    @api.marshal_with(user_model)
    def post(self):
        """Register new user account"""
        pass

# User Management Endpoints Documentation
@users_ns.route('/')
class UsersResource(Resource):
    @api.doc('get_users')
    @api.marshal_list_with(user_model)
    def get(self):
        """Get list of all users (admin only)"""
        pass

    @api.doc('create_user')
    @api.expect(user_model)
    @api.marshal_with(user_model)
    def post(self):
        """Create new user (admin only)"""
        pass

@users_ns.route('/<int:user_id>')
class UserResource(Resource):
    @api.doc('get_user')
    @api.marshal_with(user_model)
    def get(self, user_id):
        """Get specific user details"""
        pass

    @api.doc('update_user')
    @api.expect(user_model)
    @api.marshal_with(user_model)
    def put(self, user_id):
        """Update user information"""
        pass

    @api.doc('delete_user')
    @api.marshal_with(success_model)
    def delete(self, user_id):
        """Delete user account (admin only)"""
        pass

# School Management Endpoints Documentation
@schools_ns.route('/')
class SchoolsResource(Resource):
    @api.doc('get_schools')
    @api.marshal_list_with(school_model)
    def get(self):
        """Get list of all schools"""
        pass

    @api.doc('create_school')
    @api.expect(school_model)
    @api.marshal_with(school_model)
    def post(self):
        """Create new school (system admin only)"""
        pass

@schools_ns.route('/<int:school_id>')
class SchoolResource(Resource):
    @api.doc('get_school')
    @api.marshal_with(school_model)
    def get(self, school_id):
        """Get specific school details"""
        pass

    @api.doc('update_school')
    @api.expect(school_model)
    @api.marshal_with(school_model)
    def put(self, school_id):
        """Update school information"""
        pass

# Assignment Management Endpoints Documentation
@assignments_ns.route('/')
class AssignmentsResource(Resource):
    @api.doc('get_assignments')
    @api.marshal_list_with(assignment_model)
    def get(self):
        """Get list of assignments (filtered by user role)"""
        pass

    @api.doc('create_assignment')
    @api.expect(assignment_model)
    @api.marshal_with(assignment_model)
    def post(self):
        """Create new assignment (teachers and admins only)"""
        pass

@assignments_ns.route('/<int:assignment_id>')
class AssignmentResource(Resource):
    @api.doc('get_assignment')
    @api.marshal_with(assignment_model)
    def get(self, assignment_id):
        """Get specific assignment details"""
        pass

    @api.doc('update_assignment')
    @api.expect(assignment_model)
    @api.marshal_with(assignment_model)
    def put(self, assignment_id):
        """Update assignment (teacher/admin only)"""
        pass

    @api.doc('delete_assignment')
    @api.marshal_with(success_model)
    def delete(self, assignment_id):
        """Delete assignment (teacher/admin only)"""
        pass

@assignments_ns.route('/<int:assignment_id>/submit')
class AssignmentSubmissionResource(Resource):
    @api.doc('submit_assignment')
    @api.expect(api.model('AssignmentSubmission', {
        'submission_text': fields.String(description='Text submission'),
        'file_ids': fields.List(fields.Integer, description='List of uploaded file IDs'),
        'notes': fields.String(description='Additional notes')
    }))
    @api.marshal_with(success_model)
    def post(self, assignment_id):
        """Submit assignment solution (students only)"""
        pass

# Email Notification Endpoints Documentation
@email_ns.route('/send-assignment-notification')
class AssignmentNotificationResource(Resource):
    @api.doc('send_assignment_notification')
    @api.expect(api.model('AssignmentNotificationRequest', {
        'student_emails': fields.List(fields.String, required=True, description='Student email addresses'),
        'assignment_title': fields.String(required=True, description='Assignment title'),
        'assignment_id': fields.Integer(required=True, description='Assignment ID'),
        'due_date': fields.DateTime(required=True, description='Assignment due date'),
        'subject': fields.String(required=True, description='Subject area')
    }))
    @api.marshal_with(success_model)
    def post(self):
        """Send assignment notification to students"""
        pass

@email_ns.route('/send-grade-notification')
class GradeNotificationResource(Resource):
    @api.doc('send_grade_notification')
    @api.expect(api.model('GradeNotificationRequest', {
        'student_email': fields.String(required=True, description='Student email address'),
        'assignment_title': fields.String(required=True, description='Assignment title'),
        'grade': fields.String(required=True, description='Grade received'),
        'feedback': fields.String(description='Teacher feedback'),
        'subject': fields.String(required=True, description='Subject area')
    }))
    @api.marshal_with(success_model)
    def post(self):
        """Send grade notification to student"""
        pass

@email_ns.route('/send-system-announcement')
class SystemAnnouncementResource(Resource):
    @api.doc('send_system_announcement')
    @api.expect(api.model('SystemAnnouncementRequest', {
        'title': fields.String(required=True, description='Announcement title'),
        'content': fields.String(required=True, description='Announcement content'),
        'recipient_type': fields.String(required=True, description='Recipient type', 
                                       enum=['all', 'students', 'teachers', 'admins', 'custom']),
        'custom_emails': fields.List(fields.String, description='Custom email list (if recipient_type is custom)'),
        'priority': fields.String(description='Priority level', enum=['low', 'normal', 'high', 'urgent'])
    }))
    @api.marshal_with(success_model)
    def post(self):
        """Send system-wide announcement"""
        pass

# File Management Endpoints Documentation
@files_ns.route('/upload')
class FileUploadResource(Resource):
    @api.doc('upload_file')
    @api.expect(api.parser().add_argument('file', location='files', type='FileStorage', required=True))
    @api.marshal_with(api.model('FileUploadResponse', {
        'file_id': fields.String(required=True, description='Unique file identifier'),
        'filename': fields.String(required=True, description='Original filename'),
        'file_size': fields.Integer(required=True, description='File size in bytes'),
        'mime_type': fields.String(required=True, description='MIME type'),
        'upload_url': fields.String(required=True, description='File access URL')
    }))
    def post(self):
        """Upload file with security validation"""
        pass

@files_ns.route('/download/<string:file_id>')
class FileDownloadResource(Resource):
    @api.doc('download_file')
    def get(self, file_id):
        """Download file by ID"""
        pass

@files_ns.route('/validate')
class FileValidationResource(Resource):
    @api.doc('validate_file')
    @api.expect(file_upload_model)
    @api.marshal_with(success_model)
    def post(self):
        """Validate file before upload"""
        pass

# Analytics Endpoints Documentation
@analytics_ns.route('/student/<int:student_id>')
class StudentAnalyticsResource(Resource):
    @api.doc('get_student_analytics')
    @api.marshal_with(analytics_model)
    def get(self, student_id):
        """Get comprehensive analytics for specific student"""
        pass

@analytics_ns.route('/teacher/<int:teacher_id>')
class TeacherAnalyticsResource(Resource):
    @api.doc('get_teacher_analytics')
    @api.marshal_with(analytics_model)
    def get(self, teacher_id):
        """Get analytics for teacher's classes and assignments"""
        pass

@analytics_ns.route('/school/<int:school_id>')
class SchoolAnalyticsResource(Resource):
    @api.doc('get_school_analytics')
    @api.marshal_with(analytics_model)
    def get(self, school_id):
        """Get comprehensive school-wide analytics"""
        pass

# AI-Powered Endpoints Documentation
@ai_ns.route('/generate-assignment')
class AIAssignmentGenerationResource(Resource):
    @api.doc('generate_assignment_ai')
    @api.expect(ai_generation_model)
    @api.marshal_with(api.model('AIGenerationResponse', {
        'generated_content': fields.String(required=True, description='Generated assignment content'),
        'metadata': fields.Raw(description='Generation metadata'),
        'suggestions': fields.List(fields.String, description='Additional suggestions')
    }))
    def post(self):
        """Generate assignment using AI"""
        pass

@ai_ns.route('/grade-assignment')
class AIGradingResource(Resource):
    @api.doc('grade_assignment_ai')
    @api.expect(api.model('AIGradingRequest', {
        'assignment_id': fields.Integer(required=True, description='Assignment ID'),
        'submission_text': fields.String(required=True, description='Student submission'),
        'rubric': fields.Raw(description='Grading rubric'),
        'grading_criteria': fields.List(fields.String, description='Specific grading criteria')
    }))
    @api.marshal_with(api.model('AIGradingResponse', {
        'grade': fields.String(required=True, description='Assigned grade'),
        'feedback': fields.String(required=True, description='Detailed feedback'),
        'score_breakdown': fields.Raw(description='Detailed score breakdown'),
        'suggestions': fields.List(fields.String, description='Improvement suggestions')
    }))
    def post(self):
        """Grade assignment using AI"""
        pass

# Language Support Endpoints Documentation
@language_ns.route('/switch')
class LanguageSwitchResource(Resource):
    @api.doc('switch_language')
    @api.expect(api.model('LanguageSwitchRequest', {
        'language_code': fields.String(required=True, description='Language code', 
                                      enum=['en', 'af', 'zu', 'xh', 'st', 'tn', 'ss', 've', 'ts', 'nr', 'nso'])
    }))
    @api.marshal_with(success_model)
    def post(self):
        """Switch user interface language"""
        pass

@language_ns.route('/translate')
class TranslationResource(Resource):
    @api.doc('translate_content')
    @api.expect(api.model('TranslationRequest', {
        'text': fields.String(required=True, description='Text to translate'),
        'source_language': fields.String(required=True, description='Source language code'),
        'target_language': fields.String(required=True, description='Target language code'),
        'context': fields.String(description='Translation context for better accuracy')
    }))
    @api.marshal_with(api.model('TranslationResponse', {
        'translated_text': fields.String(required=True, description='Translated text'),
        'confidence': fields.Float(description='Translation confidence score'),
        'alternative_translations': fields.List(fields.String, description='Alternative translations')
    }))
    def post(self):
        """Translate content between supported languages"""
        pass

# Register error handlers
@api.errorhandler
def default_error_handler(error):
    """Default error handler"""
    return {'error': str(error)}, getattr(error, 'code', 500)

@api.errorhandler(ValueError)
def value_error_handler(error):
    """Handle validation errors"""
    return {'error': 'Validation error', 'details': str(error)}, 400

@api.errorhandler(PermissionError)
def permission_error_handler(error):
    """Handle permission errors"""
    return {'error': 'Permission denied', 'details': str(error)}, 403