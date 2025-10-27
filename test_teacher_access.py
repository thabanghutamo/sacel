#!/usr/bin/env python3
"""Test teacher dashboard access after role checking fix"""
import requests
import sys

def test_teacher_access():
    base_url = "http://127.0.0.1:5000"
    
    # Test login first
    login_data = {
        'email': 'teacher@school.co.za',
        'password': 'password123'
    }
    
    session = requests.Session()
    
    # Login
    print("Testing teacher login...")
    login_response = session.post(f"{base_url}/auth/login", data=login_data)
    
    if login_response.status_code == 200:
        print("✅ Login successful")
        
        # Test teacher dashboard access
        print("Testing teacher dashboard access...")
        dashboard_response = session.get(f"{base_url}/teachers/dashboard")
        
        if dashboard_response.status_code == 200:
            print("✅ Teacher dashboard access successful!")
            print("✅ Role checking fix worked correctly")
            return True
        elif dashboard_response.status_code == 403:
            print("❌ Still getting 403 error - role checking issue persists")
            return False
        else:
            print(f"❌ Unexpected status code: {dashboard_response.status_code}")
            return False
    else:
        print(f"❌ Login failed with status code: {login_response.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_teacher_access()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)