"""
File Upload and Management API
Provides secure file upload, validation, and management capabilities
"""

from flask import Blueprint, request, jsonify, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from functools import wraps

from app.services.file_service import FileService
from app.models import User, UserRole

files_bp = Blueprint('files', __name__)

def require_role(*roles):
    """Decorator to require specific user roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

@files_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a file with comprehensive validation and security checks"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Get upload parameters
        file_type = request.form.get('file_type', 'documents')
        subfolder = request.form.get('subfolder', current_user.role.value)
        description = request.form.get('description', '')
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        
        # Validate file type parameter
        if file_type not in FileService.ALLOWED_EXTENSIONS:
            return jsonify({
                'success': False, 
                'error': f'Invalid file type. Allowed: {list(FileService.ALLOWED_EXTENSIONS.keys())}'
            }), 400
        
        # Get upload directory
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        
        # Save file with enhanced security
        result = FileService.save_file(
            file=file,
            upload_folder=upload_folder,
            subfolder=subfolder,
            file_type=file_type,
            user_id=current_user.id
        )
        
        if not result.get('success', False):
            return jsonify(result), 400
        
        # Add additional metadata
        result.update({
            'description': description,
            'is_public': is_public,
            'uploaded_by': {
                'id': current_user.id,
                'name': f"{current_user.first_name} {current_user.last_name}",
                'role': current_user.role.value
            }
        })
        
        # Log the upload
        current_app.logger.info(
            f"File uploaded: {result['original_filename']} by user {current_user.id}"
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"File upload error: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500

@files_bp.route('/upload/multiple', methods=['POST'])
@login_required
def upload_multiple_files():
    """Upload multiple files at once"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        # Get upload parameters
        file_type = request.form.get('file_type', 'documents')
        subfolder = request.form.get('subfolder', current_user.role.value)
        
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        
        results = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            result = FileService.save_file(
                file=file,
                upload_folder=upload_folder,
                subfolder=subfolder,
                file_type=file_type,
                user_id=current_user.id
            )
            
            if result.get('success', False):
                results.append(result)
            else:
                errors.append({
                    'filename': file.filename,
                    'error': result.get('error', 'Unknown error')
                })
        
        return jsonify({
            'success': True,
            'uploaded_count': len(results),
            'error_count': len(errors),
            'files': results,
            'errors': errors
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Multiple file upload error: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500

@files_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download a file with access control"""
    try:
        # Secure the filename
        filename = secure_filename(filename)
        
        # Find file in user's folders or public folders
        possible_paths = [
            os.path.join(current_app.instance_path, 'uploads', current_user.role.value, filename),
            os.path.join(current_app.instance_path, 'uploads', 'public', filename)
        ]
        
        # Allow teachers and admins to access student files
        if current_user.role in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
            possible_paths.extend([
                os.path.join(current_app.instance_path, 'uploads', 'student', filename),
                os.path.join(current_app.instance_path, 'uploads', 'teacher', filename)
            ])
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            abort(404)
        
        # Check file access permissions
        file_info = FileService.get_file_info(file_path)
        if file_info and file_info.get('user_id') and file_info['user_id'] != current_user.id:
            # Check if user has permission to access this file
            if not _has_file_access_permission(file_info, current_user):
                abort(403)
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        current_app.logger.error(f"File download error: {str(e)}")
        abort(500)

@files_bp.route('/preview/<filename>')
@login_required
def preview_file(filename):
    """Preview a file (for images, PDFs, etc.)"""
    try:
        filename = secure_filename(filename)
        
        # Find file path (same logic as download)
        possible_paths = [
            os.path.join(current_app.instance_path, 'uploads', current_user.role.value, filename),
            os.path.join(current_app.instance_path, 'uploads', 'public', filename)
        ]
        
        if current_user.role in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
            possible_paths.extend([
                os.path.join(current_app.instance_path, 'uploads', 'student', filename),
                os.path.join(current_app.instance_path, 'uploads', 'teacher', filename)
            ])
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            abort(404)
        
        # Check if it's a thumbnail request
        if filename.endswith('_thumb.jpg'):
            return send_file(file_path, mimetype='image/jpeg')
        
        # For images, return directly for preview
        file_info = FileService.get_file_info(file_path)
        if file_info and file_info.get('mime_type', '').startswith('image/'):
            return send_file(file_path)
        
        # For other file types, return file info for preview
        return jsonify(file_info)
        
    except Exception as e:
        current_app.logger.error(f"File preview error: {str(e)}")
        abort(500)

@files_bp.route('/list')
@login_required
def list_files():
    """List files accessible to the current user"""
    try:
        file_type = request.args.get('file_type', 'all')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        user_folder = os.path.join(upload_folder, current_user.role.value)
        
        files = []
        
        # Get user's files
        if os.path.exists(user_folder):
            files.extend(_get_files_from_folder(user_folder, current_user.id))
        
        # Get public files
        public_folder = os.path.join(upload_folder, 'public')
        if os.path.exists(public_folder):
            files.extend(_get_files_from_folder(public_folder, None))
        
        # Teachers and admins can see additional files
        if current_user.role in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
            for role_folder in ['student', 'teacher']:
                role_path = os.path.join(upload_folder, role_folder)
                if os.path.exists(role_path):
                    files.extend(_get_files_from_folder(role_path, None))
        
        # Filter by file type
        if file_type != 'all':
            files = [f for f in files if f.get('file_type') == file_type]
        
        # Sort by upload time (newest first)
        files.sort(key=lambda x: x.get('upload_timestamp', ''), reverse=True)
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_files = files[start:end]
        
        return jsonify({
            'success': True,
            'files': paginated_files,
            'total': len(files),
            'page': page,
            'per_page': per_page,
            'has_next': end < len(files),
            'has_prev': page > 1
        })
        
    except Exception as e:
        current_app.logger.error(f"File list error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to list files'}), 500

@files_bp.route('/delete/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """Delete a file"""
    try:
        filename = secure_filename(filename)
        
        # Find file path
        file_path = os.path.join(
            current_app.instance_path, 'uploads', current_user.role.value, filename
        )
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Check ownership or admin permissions
        file_info = FileService.get_file_info(file_path)
        if file_info and file_info.get('user_id') != current_user.id:
            if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Delete file
        if FileService.delete_file(file_path):
            current_app.logger.info(f"File deleted: {filename} by user {current_user.id}")
            return jsonify({'success': True, 'message': 'File deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete file'}), 500
            
    except Exception as e:
        current_app.logger.error(f"File deletion error: {str(e)}")
        return jsonify({'success': False, 'error': 'Deletion failed'}), 500

@files_bp.route('/info/<filename>')
@login_required
def get_file_info(filename):
    """Get detailed information about a file"""
    try:
        filename = secure_filename(filename)
        
        # Find file path (same logic as download)
        possible_paths = [
            os.path.join(current_app.instance_path, 'uploads', current_user.role.value, filename),
            os.path.join(current_app.instance_path, 'uploads', 'public', filename)
        ]
        
        if current_user.role in [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
            possible_paths.extend([
                os.path.join(current_app.instance_path, 'uploads', 'student', filename),
                os.path.join(current_app.instance_path, 'uploads', 'teacher', filename)
            ])
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        file_info = FileService.get_file_info(file_path)
        if not file_info:
            return jsonify({'success': False, 'error': 'Unable to get file info'}), 500
        
        return jsonify({'success': True, 'file_info': file_info})
        
    except Exception as e:
        current_app.logger.error(f"File info error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get file info'}), 500

@files_bp.route('/validate', methods=['POST'])
@login_required
def validate_file():
    """Validate a file before upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'valid': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type', 'documents')
        
        validation = FileService.validate_file(file, file_type)
        
        return jsonify(validation)
        
    except Exception as e:
        current_app.logger.error(f"File validation error: {str(e)}")
        return jsonify({'valid': False, 'error': 'Validation failed'}), 500

# Helper functions

def _has_file_access_permission(file_info, user):
    """Check if user has permission to access a file"""
    # Admins can access all files
    if user.role in [UserRole.SCHOOL_ADMIN, UserRole.SYSTEM_ADMIN]:
        return True
    
    # Teachers can access student files from their school
    if user.role == UserRole.TEACHER:
        file_user_id = file_info.get('user_id')
        if file_user_id:
            file_user = User.query.get(file_user_id)
            if file_user and file_user.school_id == user.school_id:
                return True
    
    # Public files are accessible to all
    if file_info.get('is_public', False):
        return True
    
    return False

def _get_files_from_folder(folder_path, user_id_filter):
    """Get file information from a folder"""
    files = []
    
    try:
        for filename in os.listdir(folder_path):
            if filename.startswith('.'):  # Skip hidden files
                continue
                
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                file_info = FileService.get_file_info(file_path)
                
                if file_info:
                    # Filter by user if specified
                    if user_id_filter and file_info.get('user_id') != user_id_filter:
                        continue
                        
                    # Add relative path for URL generation
                    file_info['filename'] = filename
                    files.append(file_info)
                    
    except Exception as e:
        current_app.logger.error(f"Error reading folder {folder_path}: {str(e)}")
    
    return files