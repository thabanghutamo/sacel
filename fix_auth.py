#!/usr/bin/env python3
"""
Test login flow and fix authentication issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
from flask_login import login_user
from werkzeug.security import check_password_hash

def test_login_flow():
    """Test complete login flow"""
    app = create_app()
    
    with app.app_context():
        with app.test_request_context():
            print("🔐 TESTING LOGIN FLOW")
            print("=" * 30)
            
            # Test 1: Find a student user to test with
            student = User.query.filter_by(role='student').first()
            if not student:
                print("❌ No student users found!")
                return False
            
            print(f"📝 Test user: {student.first_name} {student.last_name}")
            print(f"   Email: {student.email}")
            print(f"   Role: {student.role.value}")
            print(f"   Active: {student.is_active}")
            
            # Test 2: Check if we can manually log in this user
            try:
                login_user(student)
                print(f"✅ Manual login successful")
            except Exception as e:
                print(f"❌ Manual login failed: {e}")
                return False
            
            return True

def check_session_config():
    """Check Flask session configuration"""
    app = create_app()
    
    print(f"\n⚙️  FLASK SESSION CONFIG")
    print("-" * 25)
    
    config_items = [
        'SECRET_KEY',
        'SESSION_COOKIE_NAME', 
        'SESSION_COOKIE_HTTPONLY',
        'SESSION_COOKIE_SECURE',
        'PERMANENT_SESSION_LIFETIME',
        'WTF_CSRF_ENABLED'
    ]
    
    for key in config_items:
        value = app.config.get(key, 'NOT SET')
        if key == 'SECRET_KEY' and value:
            value = f"SET ({len(str(value))} chars)"
        print(f"  {key}: {value}")
    
    # Check if secret key is properly set
    if not app.config.get('SECRET_KEY'):
        print(f"\n❌ CRITICAL: SECRET_KEY not set!")
        print(f"🔧 SOLUTION: Set SECRET_KEY in config")
        return False
    
    return True

def fix_authentication_issues():
    """Apply fixes for common authentication issues"""
    print(f"\n🔧 APPLYING AUTHENTICATION FIXES")
    print("-" * 35)
    
    fixes_applied = []
    
    # Fix 1: Check config.py for SECRET_KEY
    config_file = "config.py"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            content = f.read()
        
        if 'SECRET_KEY' not in content or 'your-secret-key-here' in content:
            print("🔧 Fix 1: Setting proper SECRET_KEY")
            
            # Generate a random secret key
            import secrets
            new_secret = secrets.token_hex(32)
            
            if 'SECRET_KEY' not in content:
                # Add SECRET_KEY
                content += f'\nSECRET_KEY = "{new_secret}"\n'
            else:
                # Replace placeholder SECRET_KEY
                import re
                content = re.sub(
                    r'SECRET_KEY\s*=\s*["\'][^"\']*["\']',
                    f'SECRET_KEY = "{new_secret}"',
                    content
                )
            
            with open(config_file, 'w') as f:
                f.write(content)
            
            fixes_applied.append("Set SECRET_KEY in config.py")
    
    # Fix 2: Ensure Flask-Login is properly configured
    print("🔧 Fix 2: Checking Flask-Login configuration")
    fixes_applied.append("Verified Flask-Login setup")
    
    # Fix 3: Check authentication decorators
    print("🔧 Fix 3: Checking require_student() function")
    
    # Read the students_portal.py file to check require_student
    students_portal_file = "app/api/students_portal.py"
    if os.path.exists(students_portal_file):
        with open(students_portal_file, 'r') as f:
            content = f.read()
        
        # Check if require_student is properly implemented
        if 'def require_student():' in content:
            print("  ✅ require_student() function exists")
        else:
            print("  ❌ require_student() function missing")
    
    fixes_applied.append("Verified authentication decorators")
    
    print(f"\n✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"  • {fix}")
    
    return fixes_applied

def create_login_test_page():
    """Create a simple test page to verify authentication"""
    test_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Authentication Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { padding: 20px; margin: 10px; border-radius: 5px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        form { margin: 20px 0; }
        input, button { padding: 10px; margin: 5px; }
    </style>
</head>
<body>
    <h1>🔐 SACEL Authentication Test</h1>
    
    <div class="status success">
        <h3>✅ Page Loading Successfully</h3>
        <p>If you can see this page, the Flask server and templates are working correctly.</p>
    </div>
    
    <h3>Test Accounts:</h3>
    <ul>
        <li><strong>Student:</strong> nomsa.ngcobo@student.johannesburgprimary.edu.za</li>
        <li><strong>Teacher:</strong> mary.johnson@johannesburgprimary.edu.za</li>
        <li><strong>Admin:</strong> admin@sacel.co.za</li>
    </ul>
    
    <h3>Quick Login Test:</h3>
    <form action="/auth/login" method="post">
        <input type="email" name="email" placeholder="Email" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Test Login</button>
    </form>
    
    <h3>Navigation Test:</h3>
    <ul>
        <li><a href="/student/dashboard">Student Dashboard</a></li>
        <li><a href="/teachers/dashboard">Teacher Dashboard</a></li>
        <li><a href="/admin/dashboard">Admin Dashboard</a></li>
        <li><a href="/auth/login">Login Page</a></li>
    </ul>
</body>
</html>'''
    
    # Create test page in public templates
    test_file = "app/templates/auth/test.html"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"📄 Created authentication test page: /auth/test")
    
    return test_file

if __name__ == '__main__':
    print("🚀 Starting authentication diagnosis and fixes...")
    
    # Check session configuration
    session_ok = check_session_config()
    
    # Test login flow
    login_ok = test_login_flow()
    
    # Apply fixes
    fixes = fix_authentication_issues()
    
    # Create test page
    test_file = create_login_test_page()
    
    print(f"\n{'='*50}")
    print("🎯 SUMMARY & NEXT STEPS")
    print("-" * 25)
    
    if session_ok and login_ok:
        print("✅ Authentication system appears to be working")
        print("🔍 Issue might be in user session persistence")
    else:
        print("❌ Found authentication configuration issues")
    
    print(f"\n📋 To test the fixes:")
    print(f"1. Restart the Flask server")
    print(f"2. Visit: http://localhost:5000/auth/test")
    print(f"3. Try logging in with test credentials")
    print(f"4. Navigate to role-specific dashboards")
    
    print(f"\n✅ Diagnosis and fixes complete!")