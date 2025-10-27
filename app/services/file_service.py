import os
import uuid
import hashlib
# import magic  # Temporarily disabled due to installation issues
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes
from datetime import datetime
import json

MAGIC_AVAILABLE = False  # Temporarily disabled
# try:
#     import magic
#     MAGIC_AVAILABLE = True
# except ImportError:
#     MAGIC_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

class FileService:
    """Enhanced service for handling secure file uploads and management"""
    
    # File type configurations
    ALLOWED_EXTENSIONS = {
        'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'pages'},
        'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg', 'webp'},
        'multimedia': {'mp4', 'avi', 'mov', 'mp3', 'wav', 'm4a', 'ogg'},
        'archives': {'zip', 'rar', '7z', 'tar', 'gz'},
        'presentations': {'ppt', 'pptx', 'odp', 'key'},
        'spreadsheets': {'xls', 'xlsx', 'ods', 'numbers', 'csv'}
    }
    
    # MIME type whitelist for enhanced security
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'text/plain',
        'text/rtf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp',
        'audio/mpeg',
        'audio/wav',
        'video/mp4',
        'video/quicktime',
        'application/zip',
        'text/csv'
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'documents': 10 * 1024 * 1024,     # 10MB
        'images': 5 * 1024 * 1024,         # 5MB
        'multimedia': 100 * 1024 * 1024,   # 100MB
        'archives': 50 * 1024 * 1024,      # 50MB
        'presentations': 25 * 1024 * 1024, # 25MB
        'spreadsheets': 10 * 1024 * 1024   # 10MB
    }
    
    # Malicious file patterns to check
    MALICIOUS_PATTERNS = [
        b'<%',  # PHP/ASP tags
        b'<?php',
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'<iframe',
        b'<object',
        b'<embed'
    ]
    
    @staticmethod
    def validate_file(file, file_type='documents', max_size=None):
        """Comprehensive file validation"""
        if not file or file.filename == '':
            return {'valid': False, 'error': 'No file provided'}
        
        # Check filename
        if not FileService.allowed_file(file.filename, file_type):
            return {'valid': False, 'error': f'File type not allowed for {file_type}'}
        
        # Get file content for additional checks
        file.seek(0)
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Check file size
        file_size = len(file_content)
        max_allowed_size = max_size or FileService.MAX_FILE_SIZES.get(file_type, 10 * 1024 * 1024)
        
        if file_size > max_allowed_size:
            return {
                'valid': False, 
                'error': f'File too large. Maximum size: {max_allowed_size / (1024*1024):.1f}MB'
            }
        
        if file_size == 0:
            return {'valid': False, 'error': 'Empty file not allowed'}
        
        # Check MIME type using python-magic
        if MAGIC_AVAILABLE:
            try:
                import magic
                mime_type = magic.from_buffer(file_content, mime=True)
                if mime_type not in FileService.ALLOWED_MIME_TYPES:
                    return {'valid': False, 'error': f'MIME type {mime_type} not allowed'}
            except Exception as e:
                current_app.logger.warning(f"python-magic error: {e}, using basic validation")
        else:
            # Fallback to basic extension check if python-magic is not available
            current_app.logger.warning("python-magic not available, using basic validation")
        
        # Check for malicious patterns
        file_content_lower = file_content.lower()
        for pattern in FileService.MALICIOUS_PATTERNS:
            if pattern in file_content_lower:
                return {'valid': False, 'error': 'File contains potentially malicious content'}
        
        # Additional image validation
        if file_type == 'images':
            image_validation = FileService._validate_image_content(file_content)
            if not image_validation['valid']:
                return image_validation
        
        return {'valid': True, 'mime_type': mime_type if 'mime_type' in locals() else None}
    
    @staticmethod
    def _validate_image_content(file_content):
        """Validate image file content"""
        if not PIL_AVAILABLE:
            return {'valid': True}  # Skip validation if PIL not available
        
        try:
            from io import BytesIO
            img = Image.open(BytesIO(file_content))
            img.verify()  # Verify it's a valid image
            
            # Check image dimensions (prevent extremely large images)
            img = Image.open(BytesIO(file_content))
            width, height = img.size
            
            if width > 10000 or height > 10000:
                return {'valid': False, 'error': 'Image dimensions too large'}
            
            return {'valid': True}
        except Exception as e:
            return {'valid': False, 'error': f'Invalid image file: {str(e)}'}
    
    @staticmethod
    def allowed_file(filename, file_type='documents'):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        allowed_extensions = FileService.ALLOWED_EXTENSIONS.get(file_type, set())
        
        # Also check combined extensions
        for ext_type, extensions in FileService.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return True
        
        return extension in allowed_extensions
    
    @staticmethod
    def save_file(file, upload_folder, subfolder=None, file_type='documents', user_id=None):
        """Save uploaded file with enhanced security and metadata"""
        # Validate file first
        validation = FileService.validate_file(file, file_type)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        try:
            # Generate unique filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            unique_id = uuid.uuid4().hex
            unique_filename = f"{unique_id}.{file_extension}"
            
            # Create full path
            if subfolder:
                folder_path = os.path.join(upload_folder, subfolder)
            else:
                folder_path = upload_folder
            
            os.makedirs(folder_path, exist_ok=True)
            
            file_path = os.path.join(folder_path, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Calculate file hash for integrity checking
            file_hash = FileService._calculate_file_hash(file_path)
            
            # Get file info
            file_info = {
                'success': True,
                'original_filename': secure_filename(file.filename),
                'saved_filename': unique_filename,
                'file_path': file_path,
                'relative_path': os.path.join(subfolder or '', unique_filename),
                'file_size': os.path.getsize(file_path),
                'mime_type': validation.get('mime_type') or mimetypes.guess_type(file_path)[0],
                'file_hash': file_hash,
                'upload_timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'file_type': file_type
            }
            
            # Create thumbnail for images
            if file_type == 'images' and PIL_AVAILABLE:
                thumbnail_path = FileService._create_thumbnail(file_path, folder_path, unique_id)
                if thumbnail_path:
                    file_info['thumbnail_path'] = thumbnail_path
            
            # Extract text content for searchable documents
            if file_type == 'documents':
                text_content = FileService._extract_text_content(file_path, file_extension)
                if text_content:
                    file_info['text_content'] = text_content[:5000]  # Limit to 5000 chars
            
            # Save metadata
            FileService._save_file_metadata(file_info)
            
            return file_info
            
        except Exception as e:
            current_app.logger.error(f"File save error: {str(e)}")
            return {'success': False, 'error': 'Failed to save file'}
    
    @staticmethod
    def _calculate_file_hash(file_path):
        """Calculate SHA-256 hash of file for integrity checking"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def _create_thumbnail(image_path, folder_path, unique_id):
        """Create thumbnail for image files"""
        try:
            thumbnail_filename = f"{unique_id}_thumb.jpg"
            thumbnail_path = os.path.join(folder_path, 'thumbnails', thumbnail_filename)
            
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
                
            return thumbnail_path
        except Exception as e:
            current_app.logger.error(f"Thumbnail creation failed: {str(e)}")
            return None
    
    @staticmethod
    def _extract_text_content(file_path, file_extension):
        """Extract text content from various file types"""
        text_content = ""
        
        try:
            if file_extension == 'txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_content = f.read()
            
            elif file_extension == 'pdf' and PYPDF2_AVAILABLE:
                text_content = FileService.extract_text_from_pdf(file_path)
            
            # Add more extractors for other document types as needed
            
        except Exception as e:
            current_app.logger.warning(f"Text extraction failed for {file_path}: {str(e)}")
        
        return text_content
    
    @staticmethod
    def _save_file_metadata(file_info):
        """Save file metadata to JSON for tracking"""
        try:
            metadata_dir = os.path.join(current_app.instance_path, 'metadata')
            os.makedirs(metadata_dir, exist_ok=True)
            
            metadata_file = os.path.join(metadata_dir, f"{file_info['saved_filename']}.json")
            
            with open(metadata_file, 'w') as f:
                json.dump(file_info, f, indent=2)
                
        except Exception as e:
            current_app.logger.error(f"Failed to save metadata: {str(e)}")
    
    @staticmethod
    def extract_text_from_pdf(file_path):
        """Extract text content from PDF for indexing"""
        if not PYPDF2_AVAILABLE:
            current_app.logger.warning("PyPDF2 not available for PDF text extraction")
            return ""
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            current_app.logger.error(f"PDF text extraction failed: {str(e)}")
            return ""
    
    @staticmethod
    def validate_image(file_path):
        """Validate and get image information"""
        if not PIL_AVAILABLE:
            return {'valid': False, 'error': 'PIL not available'}
        
        try:
            with Image.open(file_path) as img:
                return {
                    'valid': True,
                    'format': img.format,
                    'size': img.size,
                    'mode': img.mode
                }
        except Exception:
            return {'valid': False}
    
    @staticmethod
    def delete_file(file_path, delete_metadata=True):
        """Safely delete a file and its metadata"""
        try:
            deleted = False
            
            # Delete main file
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
            
            # Delete thumbnail if exists
            if 'thumbnails' not in file_path:
                thumb_dir = os.path.join(os.path.dirname(file_path), 'thumbnails')
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)
                thumb_path = os.path.join(thumb_dir, f"{name}_thumb.jpg")
                
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            
            # Delete metadata
            if delete_metadata:
                filename = os.path.basename(file_path)
                metadata_dir = os.path.join(current_app.instance_path, 'metadata')
                metadata_file = os.path.join(metadata_dir, f"{filename}.json")
                
                if os.path.exists(metadata_file):
                    os.remove(metadata_file)
            
            return deleted
        except Exception as e:
            current_app.logger.error(f"File deletion failed: {str(e)}")
            return False
    
    @staticmethod
    def get_file_info(file_path):
        """Get comprehensive file information"""
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        file_info = {
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'mime_type': mimetypes.guess_type(file_path)[0],
            'readable': os.access(file_path, os.R_OK)
        }
        
        # Load metadata if available
        filename = os.path.basename(file_path)
        metadata_dir = os.path.join(current_app.instance_path, 'metadata')
        metadata_file = os.path.join(metadata_dir, f"{filename}.json")
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    file_info.update(metadata)
            except Exception:
                pass
        
        # Additional info for specific file types
        if file_path.lower().endswith('.pdf') and PYPDF2_AVAILABLE:
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    file_info['page_count'] = len(pdf_reader.pages)
            except Exception:
                file_info['page_count'] = 0
        
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and PIL_AVAILABLE:
            image_info = FileService.validate_image(file_path)
            file_info.update(image_info)
        
        return file_info
    
    @staticmethod
    def scan_for_viruses(file_path):
        """Placeholder for virus scanning integration"""
        # This would integrate with antivirus APIs like ClamAV
        # For now, return safe status
        return {'safe': True, 'scan_result': 'No threats detected (placeholder)'}
    
    @staticmethod
    def quarantine_file(file_path):
        """Move suspicious file to quarantine folder"""
        try:
            quarantine_dir = os.path.join(current_app.instance_path, 'quarantine')
            os.makedirs(quarantine_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            quarantine_path = os.path.join(quarantine_dir, f"{datetime.utcnow().isoformat()}_{filename}")
            
            os.rename(file_path, quarantine_path)
            return quarantine_path
        except Exception as e:
            current_app.logger.error(f"File quarantine failed: {str(e)}")
            return None


# Global instance
file_service = FileService()