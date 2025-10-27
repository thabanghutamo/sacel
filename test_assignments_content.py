#!/usr/bin/env python3
"""Test the student assignments page with authenticated session."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, UserRole, Assignment
from app.extensions import db

def test_assignments_page():
    """Test assignments page with authenticated test client."""
    
    print("Creating Flask test app...")
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Find a student user
            student = User.query.filter_by(role=UserRole.STUDENT).first()
            if not student:
                print("❌ No student users found in database")
                return
            
            print(f"Found student: {student.first_name} {student.last_name}")
            
            # Check assignments in database
            assignments = Assignment.query.limit(5).all()
            print(f"Total assignments in database: {len(assignments)}")
            for assignment in assignments[:3]:
                print(f"  - {assignment.title} (ID: {assignment.id})")
            
            # Simulate login by setting the session
            with client.session_transaction() as sess:
                sess['_user_id'] = str(student.id)
                sess['_fresh'] = True
            
            # Test the assignments endpoint
            print("Requesting /student/assignments...")
            response = client.get('/student/assignments')
            
            print(f"Response status: {response.status_code}")
            print(f"Response content length: {len(response.data)}")
            
            html_content = response.data.decode('utf-8', errors='replace')
            
            # Check what we got
            if response.status_code == 302:
                print(f"Redirected to: {response.location}")
            elif 'Student Assignments' in html_content or 'assignments' in html_content.lower():
                print("✅ Got assignments page content")
                
                # Check for empty state
                if 'no_assignments_yet' in html_content or 'No assignments' in html_content:
                    print("📋 Page shows 'no assignments' message")
                elif 'assignment-card' in html_content:
                    print("📋 Page shows assignment cards")
                    card_count = html_content.count('assignment-card')
                    print(f"   Found {card_count} assignment cards")
                else:
                    print("📋 Assignments page rendered but content unclear")
                    
            else:
                print("? Got unknown content")
            
            # Show preview of content area
            print("\n--- Content Preview ---")
            # Look for the main content area
            if '<div class="min-h-screen bg-gray-50">' in html_content:
                start = html_content.find('<div class="min-h-screen bg-gray-50">')
                print(html_content[start:start+1000])
            else:
                print(html_content[:1500])

if __name__ == '__main__':
    test_assignments_page()