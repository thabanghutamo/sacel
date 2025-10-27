#!/usr/bin/env python3
"""
Test login functionality
"""

import requests
import sys

def test_login():
    # First get the login page to get the CSRF token
    login_url = "http://localhost:5000/auth/login"
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    try:
        # Get the login page
        print("Getting login page...")
        response = session.get(login_url)
        print(f"GET {login_url} - Status: {response.status_code}")
        
        if response.status_code != 200:
            print("Failed to get login page")
            return False
        
        # Extract CSRF token from the page (simple regex approach)
        import re
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        
        if not csrf_match:
            print("CSRF token not found in login page")
            print("Page content sample:")
            print(response.text[:1000])
            return False
        
        csrf_value = csrf_match.group(1)
        print(f"Found CSRF token: {csrf_value[:20]}...")
        
        # Prepare login data
        login_data = {
            'email': 'admin@sacel.co.za',
            'password': 'admin123',
            'csrf_token': csrf_value
        }
        
        print("Attempting login...")
        response = session.post(login_url, data=login_data)
        print(f"POST {login_url} - Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if we're still on login page (failed) or redirected (success)
            if 'login' in response.url:
                print("Login failed - still on login page")
                # Look for error messages in the response
                if 'Invalid email or password' in response.text:
                    print("Error: Invalid email or password")
                elif 'CSRF' in response.text:
                    print("Error: CSRF token issue")
                return False
            else:
                print(f"Login successful - redirected to: {response.url}")
                return True
        else:
            print(f"Login failed with status code: {response.status_code}")
            print(f"Response text: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error testing login: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)