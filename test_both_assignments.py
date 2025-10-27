#!/usr/bin/env python3
"""Test both assignment routes to see which one shows content."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, UserRole
from app.extensions import db

def test_both_assignment_routes():
    """Test both /student/assignments and /students/assignments."""
    
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
            
            # Simulate login by setting the session
            with client.session_transaction() as sess:
                sess['_user_id'] = str(student.id)
                sess['_fresh'] = True
            
            # Test both assignment routes
            routes_to_test = [
                '/student/assignments',  # student_portal blueprint
                '/students/assignments'  # students blueprint
            ]
            
            for route in routes_to_test:
                print(f"\n--- Testing {route} ---")
                response = client.get(route)
                
                print(f"Response status: {response.status_code}")
                print(f"Response content length: {len(response.data)}")
                
                html_content = response.data.decode('utf-8', errors='replace')
                
                # Check for assignments content
                if 'assignment-card' in html_content:
                    card_count = html_content.count('assignment-card')
                    print(f"✅ Found {card_count} assignment cards")
                elif 'no_assignments_yet' in html_content:
                    print("📋 Shows 'no assignments' empty state")
                elif 'My Assignments' in html_content:
                    print("📋 Shows assignments page but no cards found")
                else:
                    print("❓ Unknown assignments page state")
                
                # Check if it's a redirect or error
                if response.status_code == 302:
                    print(f"🔄 Redirected to: {response.location}")
                elif response.status_code != 200:
                    print(f"❌ HTTP {response.status_code} error")

if __name__ == '__main__':
    test_both_assignment_routes()