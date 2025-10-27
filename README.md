# SACEL - South African Comprehensive Education & Learning

A comprehensive Flask web application for educational management in South Africa, featuring school admissions, digital learning environments, and AI-powered educational tools.

## Features

### Core Features
- **School Admissions System**: Online application process for primary and high schools
- **Digital Learning Environment**: Textbooks, assignments, and resource management
- **AI-Powered Tools**: Assignment generation, auto-grading, and personalized learning
- **Multi-language Support**: All 11 official South African languages
- **Role-based Access Control**: Students, teachers, school admins, and parents
- **Analytics Dashboard**: Performance tracking and insights

### AI Features
- Automated assignment generation
- AI-assisted grading and feedback
- Plagiarism detection
- Personalized learning recommendations
- Multi-language content translation
- Smart search through educational materials

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Cache**: Redis for sessions and caching
- **Frontend**: HTML + Tailwind CSS
- **AI**: OpenAI API integration
- **File Storage**: Local/Object storage for documents
- **Testing**: Pytest

## Installation

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- Redis 6.0+
- Node.js (for Tailwind CSS build)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sacel
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE sacel_db;"
   
   # Run migrations
   flask db upgrade
   ```

6. **Initialize Redis**
   ```bash
   redis-server
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database Configuration
DATABASE_URL=mysql://username:password@localhost/sacel_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Mail Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## Project Structure

```
sacel/
├── app/
│   ├── __init__.py              # Application factory
│   ├── extensions.py            # Flask extensions
│   ├── models/                  # Database models
│   │   ├── __init__.py         # User, School, Student, Teacher models
│   │   ├── applications.py     # Application, Assignment, Submission models
│   │   └── library.py          # LibraryItem, Analytics, AuditLog models
│   ├── api/                     # API blueprints
│   │   ├── public.py           # Public routes
│   │   ├── admissions.py       # Admissions management
│   │   ├── schools.py          # School administration
│   │   ├── teachers.py         # Teacher portal
│   │   ├── students.py         # Student dashboard
│   │   └── assignments.py      # Assignment management
│   ├── auth/                    # Authentication
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── services/                # Business logic services
│   │   ├── ai_service.py       # AI integration
│   │   └── file_service.py     # File handling
│   ├── templates/               # HTML templates
│   └── static/                  # CSS, JS, images
├── migrations/                  # Database migrations
├── tests/                       # Test files
├── config.py                    # Configuration settings
├── main.py                      # Application entry point
└── requirements.txt             # Python dependencies
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/register` - User registration

### Public
- `GET /` - Homepage
- `GET /schools` - School directory
- `GET /schools/<id>` - School details

### Admissions
- `POST /admissions/apply` - Submit application
- `GET /admissions/status/<id>` - Check application status

### School Management
- `GET /schools/dashboard` - Admin dashboard
- `POST /schools/teachers` - Add teacher
- `GET /schools/applications` - Review applications

### Student Portal
- `GET /students/dashboard` - Student dashboard
- `GET /students/assignments` - View assignments
- `POST /students/submit` - Submit assignment

### Teacher Portal
- `GET /teachers/dashboard` - Teacher dashboard
- `POST /teachers/assignments` - Create assignment
- `POST /teachers/grade` - Grade submission

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Sort imports
isort .
```

### Database Migrations
```bash
# Create migration
flask db migrate -m "Description"

# Apply migration
flask db upgrade
```

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t sacel .

# Run container
docker run -p 5000:5000 --env-file .env sacel
```

### Production Considerations
- Use environment-specific configuration
- Set up proper logging
- Configure HTTPS/TLS
- Set up database backups
- Use a production WSGI server (Gunicorn)
- Implement monitoring and alerting

## Security Features

- Password hashing with bcrypt
- CSRF protection
- Secure session management
- File upload validation
- SQL injection prevention
- XSS protection
- Rate limiting (recommended for production)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

## Acknowledgments

- South African Department of Education
- OpenAI for AI capabilities
- Flask community
- All contributors and testers