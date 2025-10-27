# SACEL Project - South African Comprehensive Education & Learning

## Project Overview
This is a comprehensive Flask web application for educational management in South Africa, featuring:
- School admissions system
- Digital learning environment
- AI-powered tools for assignment generation and grading
- Multi-language support for SA official languages
- Role-based access control
- Secure file management

## Architecture
- Backend: Flask with modular blueprint structure
- Database: MySQL with SQLAlchemy ORM
- Cache: Redis for sessions and caching
- Frontend: HTML + Tailwind CSS
- AI Integration: OpenAI API
- File Storage: Object storage for documents and media

## Security Requirements
- All credentials in environment variables
- Password hashing with bcrypt
- TLS/HTTPS everywhere
- Encrypted data at rest
- Role-based permissions

## Development Guidelines
- Follow Flask best practices
- Use blueprints for modular organization
- Implement proper error handling
- Write unit tests for core functionality
- Use Alembic for database migrations