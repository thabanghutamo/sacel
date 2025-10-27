#!/usr/bin/env python3
"""
Test script to verify that the previously blank pages now load correctly
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"
STUDENT_EMAIL = "thabo.mthembu@student.johannesburgprimary.edu.za"
STUDENT_PASSWORD = "student123"

def test_pages():
    """Test that the fixed pages now load correctly"""
    session = requests.Session()
    
    print("🔍 Testing fixed pages...")
    
    # Test 1: Language demo (public page)
    print("1. Testing language demo page...")
    try:
        lang_demo = session.get(f"{BASE_URL}/language-demo")
        if lang_demo.status_code == 200:
            print("✅ Language demo page loads successfully")
        else:
            print(f"❌ Language demo page failed: {lang_demo.status_code}")
    except Exception as e:
        print(f"❌ Language demo page error: {e}")
    
    # Login for authenticated pages
    print("\n2. Logging in as student...")
    try:
        login_data = {
            'email': STUDENT_EMAIL,
            'password': STUDENT_PASSWORD
        }
        login_response = session.post(f"{BASE_URL}/auth/login", data=login_data)
        if login_response.status_code in [200, 302]:
            print("✅ Login successful")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test 3: Assignment detail page
    print("\n3. Testing assignment detail page...")
    try:
        assignment_detail = session.get(f"{BASE_URL}/students/assignments/1")
        if assignment_detail.status_code == 200:
            print("✅ Assignment detail page loads successfully")
        else:
            print(f"❌ Assignment detail page failed: {assignment_detail.status_code}")
    except Exception as e:
        print(f"❌ Assignment detail page error: {e}")
    
    # Test 4: Assignment submission page
    print("\n4. Testing assignment submission page...")
    try:
        submit_assignment = session.get(f"{BASE_URL}/students/assignments/1/submit")
        if submit_assignment.status_code == 200:
            print("✅ Assignment submission page loads successfully")
        else:
            print(f"❌ Assignment submission page failed: {submit_assignment.status_code}")
    except Exception as e:
        print(f"❌ Assignment submission page error: {e}")
    
    # Test 5: Search interface
    print("\n5. Testing search interface...")
    try:
        search_page = session.get(f"{BASE_URL}/api/search/")
        if search_page.status_code == 200:
            print("✅ Search interface loads successfully")
        else:
            print(f"❌ Search interface failed: {search_page.status_code}")
    except Exception as e:
        print(f"❌ Search interface error: {e}")
    
    print("\n🎉 Page testing completed!")

if __name__ == "__main__":
    test_pages()