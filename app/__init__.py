from flask import Flask, render_template
from config import config
from app.extensions import init_app
import os

def create_app(config_name=None):
    """Application factory function."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_app(app)
    
    # Configure Babel locale selector (Flask-Babel 4.0.0+ approach)
    from app.extensions import babel
    from app.services.language_service import get_locale
    
    babel.init_app(app, locale_selector=get_locale)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    from app.api.public import bp as public_bp
    app.register_blueprint(public_bp, url_prefix='/')
    
    from app.api.admissions import admissions_bp
    app.register_blueprint(admissions_bp, url_prefix='/api/admissions')
    
    from app.api.schools import bp as schools_bp
    app.register_blueprint(schools_bp, url_prefix='/schools')
    
    from app.api.teachers import bp as teachers_bp
    app.register_blueprint(teachers_bp, url_prefix='/teachers')
    
    from app.api.students import bp as students_bp
    app.register_blueprint(students_bp, url_prefix='/students')
    
    from app.api.assignments import bp as assignments_bp
    app.register_blueprint(assignments_bp, url_prefix='/assignments')
    
    from app.api.ai import bp as ai_bp
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    
    from app.api.language import bp as language_bp
    app.register_blueprint(language_bp, url_prefix='/api/language')
    
    from app.api.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    from app.api.real_time_analytics import analytics_api_bp
    app.register_blueprint(analytics_api_bp, url_prefix='/api/analytics')
    
    from app.api.grading import grading_bp
    app.register_blueprint(grading_bp, url_prefix='/api/grading')
    
    from app.api.files import files_bp
    app.register_blueprint(files_bp, url_prefix='/api/files')
    
    from app.api.email import email_bp
    app.register_blueprint(email_bp, url_prefix='/api/email')
    
    from app.api.docs import docs_bp
    app.register_blueprint(docs_bp, url_prefix='/api')
    
    from app.api.search import search_bp
    app.register_blueprint(search_bp, url_prefix='/api/search')
    
    from app.api.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.api.students_portal import bp as students_portal_bp
    app.register_blueprint(students_portal_bp, url_prefix='/student')
    
    from app.api.student_progress import student_progress_bp
    app.register_blueprint(student_progress_bp, 
                          url_prefix='/api/student-progress')
    
    from app.api.advanced_assignments import advanced_assignments_bp
    app.register_blueprint(advanced_assignments_bp,
                          url_prefix='/api/advanced-assignments')
    
    from app.api.communication import communication_bp
    app.register_blueprint(communication_bp,
                          url_prefix='/api/communication')
    
    from app.api.calendar import calendar_bp
    app.register_blueprint(calendar_bp,
                          url_prefix='/api/calendar')
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Register language helpers
    from app.services.language_service import register_language_helpers
    register_language_helpers(app)
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(app.instance_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True)
    
    return app


def register_error_handlers(app):
    """Register global error handlers for the application."""
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        return render_template('errors/500.html'), 500
