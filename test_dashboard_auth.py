#!/usr/bin/env python3
"""Test student dashboard by directly setting up a test client with authenticated session."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, UserRole
from app.extensions import db

def test_authenticated_dashboard():
    """Test dashboard access with authenticated test client."""
    
    print("Creating Flask test app...")
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Find a student user
            student = User.query.filter_by(role=UserRole.STUDENT).first()
            if not student:
                print("❌ No student users found in database")
                return
            
            print(f"Found student: {student.first_name} {student.last_name} ({student.email})")
            
            # Simulate login by setting the session
            with client.session_transaction() as sess:
                sess['_user_id'] = str(student.id)
                sess['_fresh'] = True
            
            # Now test the dashboard endpoint
            print("Requesting /student/dashboard with authenticated session...")
            response = client.get('/student/dashboard')
            
            print(f"Response status: {response.status_code}")
            print(f"Response content length: {len(response.data)}")
            
            html_content = response.data.decode('utf-8', errors='replace')
            
            # Check what we got
            if response.status_code == 302:
                print(f"Redirected to: {response.location}")
            elif '<title>Login - SACEL</title>' in html_content:
                print("❌ Still getting login page")
            elif 'Student Dashboard' in html_content or 'dashboard' in html_content.lower():
                print("✅ Got dashboard content")
            else:
                print("? Got unknown content")
            
            # Show preview
            print("\n--- HTML Preview ---")
            print(html_content[:1500])

if __name__ == '__main__':
    test_authenticated_dashboard()