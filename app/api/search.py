"""
Search API endpoints for SACEL Platform
Provides REST API for advanced search functionality
"""

from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from app.services.search_service import search_service
from datetime import datetime
from typing import Dict, Any, List

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
@login_required
def search_interface():
    """Display the advanced search interface"""
    return render_template('search/advanced_search.html')


@search_bp.route('/api/users', methods=['GET'])
@login_required
def search_users():
    """Search users with advanced filtering and pagination"""
    try:
        # Only admins and teachers can search users
        if current_user.role.value not in ['teacher', 'school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get query parameters
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 results per page
        sort_by = request.args.get('sort_by', 'last_name')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Build filters
        filters = {}
        if request.args.get('role'):
            filters['role'] = request.args.get('role')
        if request.args.get('school_id'):
            filters['school_id'] = int(request.args.get('school_id'))
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('grade_level'):
            filters['grade_level'] = request.args.get('grade_level')
        if request.args.get('created_after'):
            filters['created_after'] = request.args.get('created_after')
        if request.args.get('created_before'):
            filters['created_before'] = request.args.get('created_before')
        
        # Apply role-based filtering
        if current_user.role.value in ['school_admin', 'principal']:
            # School admins can only see users from their school
            filters['school_id'] = current_user.school_id
        elif current_user.role.value == 'teacher':
            # Teachers can only see students and other teachers from their school
            filters['school_id'] = current_user.school_id
            if 'role' not in filters:
                filters['role'] = ['student', 'teacher']
        
        # Perform search
        results = search_service.search_users(
            query=query,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"User search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@search_bp.route('/api/schools', methods=['GET'])
@login_required
def search_schools():
    """Search schools with filtering and pagination"""
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        sort_by = request.args.get('sort_by', 'name')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Build filters
        filters = {}
        if request.args.get('province'):
            filters['province'] = request.args.get('province')
        if request.args.get('district'):
            filters['district'] = request.args.get('district')
        if request.args.get('school_type'):
            filters['school_type'] = request.args.get('school_type')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        
        # Perform search
        results = search_service.search_schools(
            query=query,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"School search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@search_bp.route('/api/assignments', methods=['GET'])
@login_required
def search_assignments():
    """Search assignments with filtering and pagination"""
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build filters
        filters = {}
        if request.args.get('subject'):
            filters['subject'] = request.args.get('subject')
        if request.args.get('grade_level'):
            filters['grade_level'] = request.args.get('grade_level')
        if request.args.get('teacher_id'):
            filters['teacher_id'] = int(request.args.get('teacher_id'))
        if request.args.get('school_id'):
            filters['school_id'] = int(request.args.get('school_id'))
        if request.args.get('created_after'):
            filters['created_after'] = request.args.get('created_after')
        if request.args.get('due_after'):
            filters['due_after'] = request.args.get('due_after')
        if request.args.get('due_before'):
            filters['due_before'] = request.args.get('due_before')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        
        # Perform search with user context for role-based filtering
        results = search_service.search_assignments(
            query=query,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page,
            current_user_id=current_user.id
        )
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Assignment search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@search_bp.route('/api/applications', methods=['GET'])
@login_required
def search_applications():
    """Search admission applications with filtering and pagination"""
    try:
        # Only admins can search applications
        if current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get query parameters
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build filters
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('school_id'):
            filters['school_id'] = int(request.args.get('school_id'))
        if request.args.get('grade_applying_for'):
            filters['grade_applying_for'] = request.args.get('grade_applying_for')
        if request.args.get('submitted_after'):
            filters['submitted_after'] = request.args.get('submitted_after')
        if request.args.get('submitted_before'):
            filters['submitted_before'] = request.args.get('submitted_before')
        
        # Apply role-based filtering
        if current_user.role.value in ['school_admin', 'principal']:
            # School admins can only see applications to their school
            filters['school_id'] = current_user.school_id
        
        # Perform search
        results = search_service.search_applications(
            query=query,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page
        )
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Application search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@search_bp.route('/api/global', methods=['GET'])
@login_required
def global_search():
    """Perform global search across multiple content types"""
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({'error': 'Query must be at least 2 characters'}), 400
        
        # Get search types from parameters
        search_types = request.args.getlist('types')
        if not search_types:
            search_types = ['users', 'schools', 'assignments']
            # Add applications for admins
            if current_user.role.value in ['school_admin', 'principal', 'system_admin']:
                search_types.append('applications')
        
        # Limit per type
        limit = min(int(request.args.get('limit', 5)), 10)
        
        # Perform global search
        results = search_service.global_search(
            query=query,
            search_types=search_types,
            current_user_id=current_user.id,
            limit=limit
        )
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Global search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@search_bp.route('/api/suggestions', methods=['GET'])
@login_required
def get_search_suggestions():
    """Get search suggestions based on partial query"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')
        
        if len(query) < 2:
            return jsonify({'suggestions': []})
        
        suggestions = search_service.get_search_suggestions(
            query=query,
            search_type=search_type
        )
        
        return jsonify({'suggestions': suggestions})
        
    except Exception as e:
        current_app.logger.error(f"Search suggestions error: {e}")
        return jsonify({'error': 'Failed to get suggestions'}), 500


@search_bp.route('/api/filter-options/<content_type>', methods=['GET'])
@login_required
def get_filter_options(content_type):
    """Get available filter options for different content types"""
    try:
        if content_type not in ['users', 'schools', 'assignments', 'applications']:
            return jsonify({'error': 'Invalid content type'}), 400
        
        options = search_service.get_filter_options(content_type)
        
        # Apply role-based filtering for school options
        if current_user.role.value in ['school_admin', 'principal']:
            if 'schools' in options:
                # Filter to only show current user's school
                user_school = {'id': current_user.school_id, 'name': current_user.school.name}
                options['schools'] = [user_school] if current_user.school else []
        
        return jsonify(options)
        
    except Exception as e:
        current_app.logger.error(f"Filter options error: {e}")
        return jsonify({'error': 'Failed to get filter options'}), 500


@search_bp.route('/api/advanced', methods=['POST'])
@login_required
def advanced_search():
    """Perform advanced search with complex filters"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No search data provided'}), 400
        
        search_type = data.get('type', 'users')
        query = data.get('query', '').strip()
        filters = data.get('filters', {})
        sort_by = data.get('sort_by', 'created_at')
        sort_order = data.get('sort_order', 'desc')
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 20), 100)
        
        # Validate search type
        if search_type not in ['users', 'schools', 'assignments', 'applications']:
            return jsonify({'error': 'Invalid search type'}), 400
        
        # Apply role-based restrictions
        if search_type == 'users' and current_user.role.value not in ['teacher', 'school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if search_type == 'applications' and current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Apply role-based filtering
        if current_user.role.value in ['school_admin', 'principal']:
            if search_type in ['users', 'assignments']:
                filters['school_id'] = current_user.school_id
            elif search_type == 'applications':
                filters['school_id'] = current_user.school_id
        elif current_user.role.value == 'teacher':
            if search_type == 'users':
                filters['school_id'] = current_user.school_id
                if 'role' not in filters:
                    filters['role'] = ['student', 'teacher']
        
        # Perform search based on type
        if search_type == 'users':
            results = search_service.search_users(
                query=query, filters=filters, sort_by=sort_by, 
                sort_order=sort_order, page=page, per_page=per_page
            )
        elif search_type == 'schools':
            results = search_service.search_schools(
                query=query, filters=filters, sort_by=sort_by,
                sort_order=sort_order, page=page, per_page=per_page
            )
        elif search_type == 'assignments':
            results = search_service.search_assignments(
                query=query, filters=filters, sort_by=sort_by,
                sort_order=sort_order, page=page, per_page=per_page,
                current_user_id=current_user.id
            )
        elif search_type == 'applications':
            results = search_service.search_applications(
                query=query, filters=filters, sort_by=sort_by,
                sort_order=sort_order, page=page, per_page=per_page
            )
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Advanced search error: {e}")
        return jsonify({'error': 'Search failed'}), 500


@search_bp.route('/api/export', methods=['POST'])
@login_required
def export_search_results():
    """Export search results to CSV format"""
    try:
        # Only admins can export search results
        if current_user.role.value not in ['school_admin', 'principal', 'system_admin']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No export data provided'}), 400
        
        search_type = data.get('type', 'users')
        query = data.get('query', '')
        filters = data.get('filters', {})
        
        # Apply role-based filtering
        if current_user.role.value in ['school_admin', 'principal']:
            if search_type in ['users', 'assignments', 'applications']:
                filters['school_id'] = current_user.school_id
        
        # Get all results (no pagination for export)
        if search_type == 'users':
            results = search_service.search_users(
                query=query, filters=filters, page=1, per_page=10000
            )
        elif search_type == 'schools':
            results = search_service.search_schools(
                query=query, filters=filters, page=1, per_page=10000
            )
        elif search_type == 'assignments':
            results = search_service.search_assignments(
                query=query, filters=filters, page=1, per_page=10000,
                current_user_id=current_user.id
            )
        elif search_type == 'applications':
            results = search_service.search_applications(
                query=query, filters=filters, page=1, per_page=10000
            )
        else:
            return jsonify({'error': 'Invalid search type'}), 400
        
        # For now, return the data as JSON (CSV conversion can be done on frontend)
        return jsonify({
            'success': True,
            'data': results['results'],
            'total_records': len(results['results']),
            'export_type': search_type,
            'exported_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Export search results error: {e}")
        return jsonify({'error': 'Export failed'}), 500