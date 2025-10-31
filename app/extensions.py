from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_session import Session
from flask_babel import Babel
import redis


# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
cache = Cache()
session = Session()
babel = Babel()

# Redis connection will be initialized in create_app
redis_client = None


def init_app(app):
    """Initialize Flask extensions with app."""
    global redis_client
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    
    # Initialize Redis
    redis_client = redis.from_url(app.config['REDIS_URL'])
    
    # Configure session storage to use Redis
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis_client
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'sacel:'
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', False)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Initialize Flask-Session
    session.init_app(app)
    
    # Initialize AI Service
    from app.services.ai_service import ai_service
    ai_service.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    from app.models import User
    return User.query.get(int(user_id))