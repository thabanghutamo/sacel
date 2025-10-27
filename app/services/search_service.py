"""
Advanced Search Service for SACEL Platform
Provides comprehensive search functionality across all platform content
"""

from flask import current_app
from sqlalchemy import or_, and_, func, text
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import (
    User, School, Assignment, Application, UserRole, 
    ApplicationStatus
)
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re


class SearchService:
    """Advanced search service with filtering, sorting, and pagination"""
    
    @staticmethod
    def search_users(query: str = '', filters: Dict[str, Any] = None, 
                    sort_by: str = 'last_name', sort_order: str = 'asc',
                    page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        Search users with advanced filtering and pagination
        
        Args:
            query: Search query string
            filters: Dictionary of filters (role, school_id, is_active, etc.)
            sort_by: Field to sort by (last_name, first_name, email, created_at)
            sort_order: Sort order ('asc' or 'desc')
            page: Page number for pagination
            per_page: Results per page
            
        Returns:
            Dictionary with results, pagination info, and metadata
        """
        filters = filters or {}
        
        # Base query
        base_query = User.query.options(joinedload(User.school))
        
        # Apply text search
        if query:
            search_terms = query.split()
            for term in search_terms:
                search_filter = or_(
                    User.first_name.ilike(f'%{term}%'),
                    User.last_name.ilike(f'%{term}%'),
                    User.email.ilike(f'%{term}%'),
                    User.id_number.ilike(f'%{term}%') if hasattr(User, 'id_number') else False
                )
                base_query = base_query.filter(search_filter)
        
        # Apply filters
        if 'role' in filters and filters['role']:
            if isinstance(filters['role'], list):
                role_filters = [UserRole(role) for role in filters['role']]
                base_query = base_query.filter(User.role.in_(role_filters))
            else:
                base_query = base_query.filter(User.role == UserRole(filters['role']))
        
        if 'school_id' in filters and filters['school_id']:
            base_query = base_query.filter(User.school_id == filters['school_id'])
        
        if 'is_active' in filters and filters['is_active'] is not None:
            base_query = base_query.filter(User.is_active == filters['is_active'])
        
        if 'grade_level' in filters and filters['grade_level']:
            base_query = base_query.filter(User.grade_level == filters['grade_level'])
        
        # Date range filters
        if 'created_after' in filters and filters['created_after']:
            created_after = datetime.fromisoformat(filters['created_after'])
            base_query = base_query.filter(User.created_at >= created_after)
        
        if 'created_before' in filters and filters['created_before']:
            created_before = datetime.fromisoformat(filters['created_before'])
            base_query = base_query.filter(User.created_at <= created_before)
        
        # Apply sorting
        sort_column = getattr(User, sort_by, User.last_name)
        if sort_order.lower() == 'desc':
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())
        
        # Get total count before pagination
        total_count = base_query.count()
        
        # Apply pagination
        paginated_results = base_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare results
        users = []
        for user in paginated_results.items:
            user_data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'role': user.role.value,
                'school_id': user.school_id,
                'school_name': user.school.name if user.school else None,
                'is_active': user.is_active,
                'grade_level': getattr(user, 'grade_level', None)
            }
            users.append(user_data)
        
        return {
            'results': users,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': paginated_results.pages,
                'has_prev': paginated_results.has_prev,
                'has_next': paginated_results.has_next,
                'prev_num': paginated_results.prev_num,
                'next_num': paginated_results.next_num
            },
            'query': query,
            'filters': filters,
            'sort': {'by': sort_by, 'order': sort_order}
        }
    
    @staticmethod
    def search_schools(query: str = '', filters: Dict[str, Any] = None,
                      sort_by: str = 'name', sort_order: str = 'asc',
                      page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Search schools with filtering and pagination"""
        filters = filters or {}
        
        # Base query
        base_query = School.query
        
        # Apply text search
        if query:
            search_terms = query.split()
            for term in search_terms:
                search_filter = or_(
                    School.name.ilike(f'%{term}%'),
                    School.province.ilike(f'%{term}%'),
                    School.district.ilike(f'%{term}%'),
                    School.address.ilike(f'%{term}%') if hasattr(School, 'address') else False
                )
                base_query = base_query.filter(search_filter)
        
        # Apply filters
        if 'province' in filters and filters['province']:
            base_query = base_query.filter(School.province == filters['province'])
        
        if 'district' in filters and filters['district']:
            base_query = base_query.filter(School.district == filters['district'])
        
        if 'school_type' in filters and filters['school_type']:
            base_query = base_query.filter(School.school_type == filters['school_type'])
        
        if 'is_active' in filters and filters['is_active'] is not None:
            base_query = base_query.filter(School.is_active == filters['is_active'])
        
        # Apply sorting
        sort_column = getattr(School, sort_by, School.name)
        if sort_order.lower() == 'desc':
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())
        
        # Get total count
        total_count = base_query.count()
        
        # Apply pagination
        paginated_results = base_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare results
        schools = []
        for school in paginated_results.items:
            school_data = {
                'id': school.id,
                'name': school.name,
                'province': school.province,
                'district': school.district,
                'school_type': getattr(school, 'school_type', 'Public'),
                'is_active': school.is_active,
                'student_count': User.query.filter_by(
                    school_id=school.id, role=UserRole.STUDENT
                ).count(),
                'teacher_count': User.query.filter_by(
                    school_id=school.id, role=UserRole.TEACHER
                ).count()
            }
            schools.append(school_data)
        
        return {
            'results': schools,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': paginated_results.pages,
                'has_prev': paginated_results.has_prev,
                'has_next': paginated_results.has_next
            },
            'query': query,
            'filters': filters,
            'sort': {'by': sort_by, 'order': sort_order}
        }
    
    @staticmethod
    def search_assignments(query: str = '', filters: Dict[str, Any] = None,
                          sort_by: str = 'created_at', sort_order: str = 'desc',
                          page: int = 1, per_page: int = 20, 
                          current_user_id: int = None) -> Dict[str, Any]:
        """Search assignments with filtering and pagination"""
        filters = filters or {}
        
        # Base query with teacher information
        base_query = Assignment.query.options(
            joinedload(Assignment.teacher).joinedload(User.school)
        )
        
        # Apply user-based filtering (role-based access)
        if current_user_id:
            current_user = User.query.get(current_user_id)
            if current_user:
                if current_user.role == UserRole.STUDENT:
                    # Students only see assignments from their school
                    base_query = base_query.join(User, Assignment.teacher_id == User.id)\
                                          .filter(User.school_id == current_user.school_id)
                elif current_user.role == UserRole.TEACHER:
                    # Teachers see their own assignments and school assignments
                    base_query = base_query.filter(
                        or_(
                            Assignment.teacher_id == current_user_id,
                            Assignment.teacher_id.in_(
                                db.session.query(User.id).filter(
                                    User.school_id == current_user.school_id,
                                    User.role == UserRole.TEACHER
                                )
                            )
                        )
                    )
                elif current_user.role in [UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL]:
                    # School admins see all assignments in their school
                    base_query = base_query.join(User, Assignment.teacher_id == User.id)\
                                          .filter(User.school_id == current_user.school_id)
        
        # Apply text search
        if query:
            search_terms = query.split()
            for term in search_terms:
                search_filter = or_(
                    Assignment.title.ilike(f'%{term}%'),
                    Assignment.description.ilike(f'%{term}%'),
                    Assignment.subject.ilike(f'%{term}%'),
                    Assignment.instructions.ilike(f'%{term}%') if hasattr(Assignment, 'instructions') else False
                )
                base_query = base_query.filter(search_filter)
        
        # Apply filters
        if 'subject' in filters and filters['subject']:
            base_query = base_query.filter(Assignment.subject == filters['subject'])
        
        if 'grade_level' in filters and filters['grade_level']:
            base_query = base_query.filter(Assignment.grade_level == filters['grade_level'])
        
        if 'teacher_id' in filters and filters['teacher_id']:
            base_query = base_query.filter(Assignment.teacher_id == filters['teacher_id'])
        
        if 'school_id' in filters and filters['school_id']:
            base_query = base_query.join(User, Assignment.teacher_id == User.id)\
                                  .filter(User.school_id == filters['school_id'])
        
        # Date range filters
        if 'created_after' in filters and filters['created_after']:
            created_after = datetime.fromisoformat(filters['created_after'])
            base_query = base_query.filter(Assignment.created_at >= created_after)
        
        if 'due_after' in filters and filters['due_after']:
            due_after = datetime.fromisoformat(filters['due_after'])
            base_query = base_query.filter(Assignment.due_date >= due_after)
        
        if 'due_before' in filters and filters['due_before']:
            due_before = datetime.fromisoformat(filters['due_before'])
            base_query = base_query.filter(Assignment.due_date <= due_before)
        
        # Status filters
        if 'is_active' in filters and filters['is_active'] is not None:
            base_query = base_query.filter(Assignment.is_active == filters['is_active'])
        
        # Apply sorting
        sort_column = getattr(Assignment, sort_by, Assignment.created_at)
        if sort_order.lower() == 'desc':
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())
        
        # Get total count
        total_count = base_query.count()
        
        # Apply pagination
        paginated_results = base_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare results
        assignments = []
        for assignment in paginated_results.items:
            assignment_data = {
                'id': assignment.id,
                'title': assignment.title,
                'description': assignment.description,
                'subject': assignment.subject,
                'grade_level': assignment.grade_level,
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
                'teacher': {
                    'id': assignment.teacher.id,
                    'name': f"{assignment.teacher.first_name} {assignment.teacher.last_name}",
                    'email': assignment.teacher.email
                } if assignment.teacher else None,
                'school_name': assignment.teacher.school.name if assignment.teacher and assignment.teacher.school else None,
                'total_points': getattr(assignment, 'total_points', None),
                'is_active': getattr(assignment, 'is_active', True)
            }
            assignments.append(assignment_data)
        
        return {
            'results': assignments,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': paginated_results.pages,
                'has_prev': paginated_results.has_prev,
                'has_next': paginated_results.has_next
            },
            'query': query,
            'filters': filters,
            'sort': {'by': sort_by, 'order': sort_order}
        }
    
    @staticmethod
    def search_applications(query: str = '', filters: Dict[str, Any] = None,
                           sort_by: str = 'created_at', sort_order: str = 'desc',
                           page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Search admission applications with filtering and pagination"""
        filters = filters or {}
        
        # Base query with school information
        base_query = Application.query.options(joinedload(Application.school))
        
        # Apply text search
        if query:
            search_terms = query.split()
            for term in search_terms:
                search_filter = or_(
                    Application.student_first_name.ilike(f'%{term}%'),
                    Application.student_last_name.ilike(f'%{term}%'),
                    Application.parent_first_name.ilike(f'%{term}%'),
                    Application.parent_last_name.ilike(f'%{term}%'),
                    Application.parent_email.ilike(f'%{term}%'),
                    Application.application_id.ilike(f'%{term}%') if hasattr(Application, 'application_id') else False
                )
                base_query = base_query.filter(search_filter)
        
        # Apply filters
        if 'status' in filters and filters['status']:
            if isinstance(filters['status'], list):
                status_filters = [ApplicationStatus(status) for status in filters['status']]
                base_query = base_query.filter(Application.status.in_(status_filters))
            else:
                base_query = base_query.filter(Application.status == ApplicationStatus(filters['status']))
        
        if 'school_id' in filters and filters['school_id']:
            base_query = base_query.filter(Application.school_id == filters['school_id'])
        
        if 'grade_applying_for' in filters and filters['grade_applying_for']:
            base_query = base_query.filter(Application.grade_applying_for == filters['grade_applying_for'])
        
        # Date range filters
        if 'submitted_after' in filters and filters['submitted_after']:
            submitted_after = datetime.fromisoformat(filters['submitted_after'])
            base_query = base_query.filter(Application.created_at >= submitted_after)
        
        if 'submitted_before' in filters and filters['submitted_before']:
            submitted_before = datetime.fromisoformat(filters['submitted_before'])
            base_query = base_query.filter(Application.created_at <= submitted_before)
        
        # Apply sorting
        sort_column = getattr(Application, sort_by, Application.created_at)
        if sort_order.lower() == 'desc':
            base_query = base_query.order_by(sort_column.desc())
        else:
            base_query = base_query.order_by(sort_column.asc())
        
        # Get total count
        total_count = base_query.count()
        
        # Apply pagination
        paginated_results = base_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare results
        applications = []
        for application in paginated_results.items:
            application_data = {
                'id': application.id,
                'student_name': f"{application.student_first_name} {application.student_last_name}",
                'parent_name': f"{application.parent_first_name} {application.parent_last_name}",
                'parent_email': application.parent_email,
                'grade_applying_for': application.grade_applying_for,
                'status': application.status.value,
                'school_name': application.school.name if application.school else None,
                'created_at': application.created_at.isoformat() if application.created_at else None,
                'updated_at': application.updated_at.isoformat() if hasattr(application, 'updated_at') and application.updated_at else None
            }
            applications.append(application_data)
        
        return {
            'results': applications,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': paginated_results.pages,
                'has_prev': paginated_results.has_prev,
                'has_next': paginated_results.has_next
            },
            'query': query,
            'filters': filters,
            'sort': {'by': sort_by, 'order': sort_order}
        }
    
    @staticmethod
    def global_search(query: str, search_types: List[str] = None, 
                     current_user_id: int = None, limit: int = 5) -> Dict[str, Any]:
        """
        Perform global search across multiple content types
        
        Args:
            query: Search query string
            search_types: List of types to search ['users', 'schools', 'assignments', 'applications']
            current_user_id: Current user ID for permission filtering
            limit: Maximum results per type
            
        Returns:
            Dictionary with results for each content type
        """
        if not query or len(query.strip()) < 2:
            return {'results': {}, 'query': query, 'total_results': 0}
        
        search_types = search_types or ['users', 'schools', 'assignments', 'applications']
        results = {}
        total_results = 0
        
        # Search users
        if 'users' in search_types:
            user_results = SearchService.search_users(
                query=query, page=1, per_page=limit
            )
            results['users'] = user_results['results']
            total_results += len(results['users'])
        
        # Search schools
        if 'schools' in search_types:
            school_results = SearchService.search_schools(
                query=query, page=1, per_page=limit
            )
            results['schools'] = school_results['results']
            total_results += len(results['schools'])
        
        # Search assignments
        if 'assignments' in search_types:
            assignment_results = SearchService.search_assignments(
                query=query, page=1, per_page=limit, current_user_id=current_user_id
            )
            results['assignments'] = assignment_results['results']
            total_results += len(results['assignments'])
        
        # Search applications
        if 'applications' in search_types:
            application_results = SearchService.search_applications(
                query=query, page=1, per_page=limit
            )
            results['applications'] = application_results['results']
            total_results += len(results['applications'])
        
        return {
            'results': results,
            'query': query,
            'search_types': search_types,
            'total_results': total_results,
            'limit_per_type': limit
        }
    
    @staticmethod
    def get_search_suggestions(query: str, search_type: str = 'all') -> List[str]:
        """
        Get search suggestions based on partial query
        
        Args:
            query: Partial search query
            search_type: Type of content to suggest for
            
        Returns:
            List of suggested search terms
        """
        if not query or len(query.strip()) < 2:
            return []
        
        suggestions = set()
        query = query.strip().lower()
        
        try:
            if search_type in ['all', 'users']:
                # User suggestions
                user_suggestions = db.session.query(User.first_name, User.last_name)\
                    .filter(
                        or_(
                            User.first_name.ilike(f'{query}%'),
                            User.last_name.ilike(f'{query}%')
                        )
                    ).limit(5).all()
                
                for first_name, last_name in user_suggestions:
                    if first_name and first_name.lower().startswith(query):
                        suggestions.add(first_name)
                    if last_name and last_name.lower().startswith(query):
                        suggestions.add(last_name)
            
            if search_type in ['all', 'schools']:
                # School suggestions
                school_suggestions = db.session.query(School.name)\
                    .filter(School.name.ilike(f'{query}%'))\
                    .limit(5).all()
                
                for (name,) in school_suggestions:
                    if name and name.lower().startswith(query):
                        suggestions.add(name)
            
            if search_type in ['all', 'assignments']:
                # Assignment subject suggestions
                subject_suggestions = db.session.query(Assignment.subject)\
                    .filter(Assignment.subject.ilike(f'{query}%'))\
                    .distinct().limit(5).all()
                
                for (subject,) in subject_suggestions:
                    if subject and subject.lower().startswith(query):
                        suggestions.add(subject)
        
        except Exception as e:
            current_app.logger.error(f"Error getting search suggestions: {e}")
        
        return sorted(list(suggestions))[:10]
    
    @staticmethod
    def get_filter_options(content_type: str) -> Dict[str, List[str]]:
        """
        Get available filter options for different content types
        
        Args:
            content_type: Type of content ('users', 'schools', 'assignments', 'applications')
            
        Returns:
            Dictionary with available filter options
        """
        options = {}
        
        try:
            if content_type == 'users':
                options = {
                    'roles': [role.value for role in UserRole],
                    'schools': [
                        {'id': s.id, 'name': s.name} 
                        for s in School.query.filter_by(is_active=True).order_by(School.name).all()
                    ],
                    'grades': ['Grade R', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 
                              'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 
                              'Grade 10', 'Grade 11', 'Grade 12']
                }
            
            elif content_type == 'schools':
                provinces = db.session.query(School.province)\
                    .filter(School.province.isnot(None))\
                    .distinct().order_by(School.province).all()
                districts = db.session.query(School.district)\
                    .filter(School.district.isnot(None))\
                    .distinct().order_by(School.district).all()
                
                options = {
                    'provinces': [p[0] for p in provinces],
                    'districts': [d[0] for d in districts],
                    'school_types': ['Public', 'Private', 'Charter', 'International']
                }
            
            elif content_type == 'assignments':
                subjects = db.session.query(Assignment.subject)\
                    .filter(Assignment.subject.isnot(None))\
                    .distinct().order_by(Assignment.subject).all()
                grades = db.session.query(Assignment.grade_level)\
                    .filter(Assignment.grade_level.isnot(None))\
                    .distinct().order_by(Assignment.grade_level).all()
                
                options = {
                    'subjects': [s[0] for s in subjects],
                    'grades': [g[0] for g in grades],
                    'schools': [
                        {'id': s.id, 'name': s.name} 
                        for s in School.query.filter_by(is_active=True).order_by(School.name).all()
                    ]
                }
            
            elif content_type == 'applications':
                options = {
                    'statuses': [status.value for status in ApplicationStatus],
                    'schools': [
                        {'id': s.id, 'name': s.name} 
                        for s in School.query.filter_by(is_active=True).order_by(School.name).all()
                    ],
                    'grades': ['Grade R', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 
                              'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 
                              'Grade 10', 'Grade 11', 'Grade 12']
                }
        
        except Exception as e:
            current_app.logger.error(f"Error getting filter options for {content_type}: {e}")
        
        return options


# Global search service instance
search_service = SearchService()