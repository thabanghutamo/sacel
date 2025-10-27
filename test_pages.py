#!/usr/bin/env python3
"""
Simple page testing script to identify routing issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import url_for

def test_url_building():
    """Test if URL building works for common routes"""
    app = create_app()
    
    # Routes to test
    routes_to_test = [
        # Student routes
        ('student_portal.dashboard', {}, 'Student Dashboard'),
        ('student_portal.assignments', {}, 'Student Assignments'),
        ('student_portal.calendar', {}, 'Student Calendar'),
        ('student_portal.grades', {}, 'Student Grades'),
        ('student_portal.progress', {}, 'Student Progress'),
        
        # Teacher routes
        ('teachers.dashboard', {}, 'Teacher Dashboard'),
        ('teachers.assignments', {}, 'Teacher Assignments'), 
        ('teachers.calendar', {}, 'Teacher Calendar'),
        ('teachers.grading', {}, 'Teacher Grading'),
        ('teachers.communication', {}, 'Teacher Communication'),
        
        # Admin routes
        ('admin.dashboard', {}, 'Admin Dashboard'),
        ('admin.users', {}, 'Admin Users'),
        ('admin.schools', {}, 'Admin Schools'),
        ('admin.applications', {}, 'Admin Applications'),
        ('admin.analytics', {}, 'Admin Analytics'),
        ('admin.email_management', {}, 'Admin Email Management'),
        ('admin.settings', {}, 'Admin Settings'),
        
        # Public routes
        ('public.index', {}, 'Home Page'),
        ('public.schools', {}, 'Schools'),
        ('public.upload', {}, 'Upload'),
        
        # Analytics routes
        ('analytics.real_time_dashboard', {}, 'Real-time Analytics'),
        
        # Student detailed routes
        ('students.view_assignment', {'assignment_id': 1}, 'Student View Assignment'),
        ('students.submit_assignment', {'assignment_id': 1}, 'Student Submit Assignment'),
        ('students.progress', {}, 'Student Progress (students blueprint)'),
    ]
    
    print("Testing URL building for common routes...")
    print("=" * 60)
    
    with app.app_context():
        working_routes = []
        broken_routes = []
        
        for endpoint, params, description in routes_to_test:
            try:
                url = url_for(endpoint, **params)
                print(f"✅ {description:<35} {endpoint:<30} → {url}")
                working_routes.append((endpoint, description))
            except Exception as e:
                print(f"❌ {description:<35} {endpoint:<30} → ERROR: {str(e)}")
                broken_routes.append((endpoint, description, str(e)))
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: {len(working_routes)} working, {len(broken_routes)} broken")
        
        if broken_routes:
            print("\nBROKEN ROUTES:")
            for endpoint, description, error in broken_routes:
                print(f"  • {endpoint}: {error}")
        
        return working_routes, broken_routes

if __name__ == '__main__':
    test_url_building()