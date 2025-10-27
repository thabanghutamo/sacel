#!/usr/bin/env python3
"""
Test script to verify the assignments page works correctly after fixing the template issues
"""
import requests
import json

# Test student credentials
STUDENT_EMAIL = "thabo.mthembu@student.johannesburgprimary.edu.za"
STUDENT_PASSWORD = "student123"
BASE_URL = "http://127.0.0.1:5000"

def test_assignments_page():
    """Test login and assignments page access"""
    session = requests.Session()
    
    print("🔍 Testing assignments page functionality...")
    
    # Step 1: Get login page to check for CSRF token
    print("1. Loading login page...")
    login_page = session.get(f"{BASE_URL}/auth/login")
    if login_page.status_code != 200:
        print(f"❌ Login page failed: {login_page.status_code}")
        return False
    print("✓ Login page loaded successfully")
    
    # Step 2: Login with student credentials
    print("2. Attempting login...")
    login_data = {
        'email': STUDENT_EMAIL,
        'password': STUDENT_PASSWORD
    }
    
    login_response = session.post(f"{BASE_URL}/auth/login", data=login_data)
    if login_response.status_code == 200 and "dashboard" in login_response.url:
        print("✓ Login successful, redirected to dashboard")
    elif login_response.status_code == 302:
        print("✓ Login successful with redirect")
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response URL: {login_response.url}")
        return False
    
    # Step 3: Test assignments page
    print("3. Testing assignments page...")
    assignments_response = session.get(f"{BASE_URL}/students/assignments")
    
    if assignments_response.status_code == 200:
        print("✓ Assignments page loaded successfully")
        
        # Check if page contains expected content
        content = assignments_response.text
        if "assignments" in content.lower() and "assignment-card" in content:
            print("✓ Assignments page contains expected assignment elements")
            print(f"✓ Page size: {len(content)} characters")
            return True
        else:
            print("❌ Assignments page missing expected content")
            print("Content preview:", content[:500])
            return False
    else:
        print(f"❌ Assignments page failed: {assignments_response.status_code}")
        print(f"Response content: {assignments_response.text[:500]}")
        return False

if __name__ == "__main__":
    try:
        success = test_assignments_page()
        if success:
            print("\n🎉 All tests passed! The modern assignments page is working correctly.")
        else:
            print("\n❌ Tests failed. There may be template or backend issues.")
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()