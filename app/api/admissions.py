from flask import Blueprint, request, jsonify, current_app, render_template
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.extensions import db
from app.models import Application, User, School, UserRole
from app.services.file_service import FileService

admissions_bp = Blueprint('admissions', __name__)

@admissions_bp.route('/apply')
def apply():
    """Application form page"""
    schools = School.query.all()
    return render_template('admissions/apply.html', schools=schools)

@admissions_bp.route('/submit', methods=['POST'])
def submit_application():
    """Submit a school admission application"""
    try:
        # Get form data
        data = request.get_json() if request.content_type == 'application/json' else request.form.to_dict()
        
        # Basic validation
        required_fields = ['school_id', 'student_first_name', 'student_last_name', 
                          'student_birth_date', 'grade_applying_for', 'parent_first_name',
                          'parent_last_name', 'parent_email', 'parent_phone']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Check if school exists
        school = School.query.get(data['school_id'])
        if not school:
            return jsonify({'error': 'School not found'}), 404
        
        if not school.admission_open:
            return jsonify({'error': 'Admissions are currently closed for this school'}), 400
        
        # Create application
        application = Application(
            reference_number=generate_reference_number(),
            school_id=data['school_id'],
            student_first_name=data['student_first_name'],
            student_last_name=data['student_last_name'],
            student_birth_date=datetime.strptime(data['student_birth_date'], '%Y-%m-%d').date(),
            grade_applying_for=int(data['grade_applying_for']),
            parent_first_name=data['parent_first_name'],
            parent_last_name=data['parent_last_name'],
            parent_email=data['parent_email'],
            parent_phone=data['parent_phone'],
            address=data.get('address', ''),
            previous_school=data.get('previous_school', ''),
            medical_conditions=data.get('medical_conditions', ''),
            special_requirements=data.get('special_requirements', ''),
            status='submitted',
            submitted_at=datetime.utcnow()
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully',
            'reference_number': application.reference_number,
            'application_id': application.id
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error submitting application: {str(e)}")
        return jsonify({'error': 'Failed to submit application'}), 500

@admissions_bp.route('/upload-document', methods=['POST'])
def upload_document():
    """Upload supporting documents for an application"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        application_id = request.form.get('application_id')
        document_type = request.form.get('document_type', 'other')
        
        if not application_id:
            return jsonify({'error': 'Application ID required'}), 400
        
        # Check if application exists
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Validate and save file
        file_service = FileService()
        file_info = file_service.save_file(
            file, 
            folder='admissions',
            max_size_mb=10,
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
        )
        
        if not file_info['success']:
            return jsonify({'error': file_info['message']}), 400
        
        # Update application documents
        documents = application.documents or {}
        documents[document_type] = {
            'filename': file_info['filename'],
            'original_name': file.filename,
            'uploaded_at': datetime.utcnow().isoformat(),
            'size': file_info['size']
        }
        application.documents = documents
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document_type': document_type,
            'filename': file_info['filename']
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'error': 'Failed to upload document'}), 500

@admissions_bp.route('/status/<reference_number>', methods=['GET'])
def check_status(reference_number):
    """Check application status by reference number"""
    try:
        application = Application.query.filter_by(reference_number=reference_number).first()
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        return jsonify({
            'reference_number': application.reference_number,
            'student_name': f"{application.student_first_name} {application.student_last_name}",
            'school_name': application.school.name,
            'grade': application.grade_applying_for,
            'status': application.status,
            'submitted_at': application.submitted_at.isoformat() if application.submitted_at else None,
            'reviewed_at': application.reviewed_at.isoformat() if application.reviewed_at else None,
            'documents': list(application.documents.keys()) if application.documents else [],
            'notes': application.notes
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error checking status: {str(e)}")
        return jsonify({'error': 'Failed to check status'}), 500

@admissions_bp.route('/review/<int:application_id>', methods=['PUT'])
def review_application(application_id):
    """Review an application (admin/school staff only)"""
    try:
        # TODO: Add authentication check for admin/school staff roles
        
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if new_status not in ['under_review', 'approved', 'rejected', 'waitlisted']:
            return jsonify({'error': 'Invalid status'}), 400
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Update application
        application.status = new_status
        application.notes = notes
        application.reviewed_at = datetime.utcnow()
        # TODO: Set reviewed_by to current user ID
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Application {new_status}',
            'application_id': application.id,
            'status': application.status
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error reviewing application: {str(e)}")
        return jsonify({'error': 'Failed to review application'}), 500

@admissions_bp.route('/list/<int:school_id>', methods=['GET'])
def list_applications(school_id):
    """List applications for a school (admin/school staff only)"""
    try:
        # TODO: Add authentication check for admin/school staff roles
        
        status_filter = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        query = Application.query.filter_by(school_id=school_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        query = query.order_by(Application.submitted_at.desc())
        applications = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'applications': [{
                'id': app.id,
                'reference_number': app.reference_number,
                'student_name': f"{app.student_first_name} {app.student_last_name}",
                'grade': app.grade_applying_for,
                'status': app.status,
                'submitted_at': app.submitted_at.isoformat() if app.submitted_at else None,
                'parent_email': app.parent_email,
                'documents_count': len(app.documents) if app.documents else 0
            } for app in applications.items],
            'pagination': {
                'page': applications.page,
                'pages': applications.pages,
                'per_page': applications.per_page,
                'total': applications.total,
                'has_next': applications.has_next,
                'has_prev': applications.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error listing applications: {str(e)}")
        return jsonify({'error': 'Failed to list applications'}), 500

@admissions_bp.route('/stats/<int:school_id>', methods=['GET'])
def admission_stats(school_id):
    """Get admission statistics for a school"""
    try:
        # TODO: Add authentication check for admin/school staff roles
        
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': 'School not found'}), 404
        
        # Get application counts by status
        stats = {
            'total_applications': Application.query.filter_by(school_id=school_id).count(),
            'submitted': Application.query.filter_by(school_id=school_id, status='submitted').count(),
            'under_review': Application.query.filter_by(school_id=school_id, status='under_review').count(),
            'approved': Application.query.filter_by(school_id=school_id, status='approved').count(),
            'rejected': Application.query.filter_by(school_id=school_id, status='rejected').count(),
            'waitlisted': Application.query.filter_by(school_id=school_id, status='waitlisted').count(),
        }
        
        # Get applications by grade
        grade_stats = {}
        applications = Application.query.filter_by(school_id=school_id).all()
        for app in applications:
            grade = f"Grade {app.grade_applying_for}"
            if grade not in grade_stats:
                grade_stats[grade] = 0
            grade_stats[grade] += 1
        
        return jsonify({
            'school_name': school.name,
            'admission_open': school.admission_open,
            'status_breakdown': stats,
            'grade_breakdown': grade_stats,
            'capacity': school.student_capacity,
            'current_enrollment': school.current_enrollment,
            'available_spots': school.student_capacity - school.current_enrollment
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting admission stats: {str(e)}")
        return jsonify({'error': 'Failed to get admission statistics'}), 500

def generate_reference_number():
    """Generate a unique reference number for applications"""
    year = datetime.now().year
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"SACEL{year}{unique_id}"