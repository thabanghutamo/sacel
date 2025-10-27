#!/usr/bin/env python3
"""Test script to login as a student and fetch dashboard content."""

import urllib.request
import urllib.parse
import http.cookiejar

def test_student_dashboard():
    """Test login flow and dashboard access with proper session handling."""
    
    # Create a cookie jar to maintain session
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    base_url = 'http://127.0.0.1:5000'
    
    # Step 1: Get login page and CSRF token
    print("Step 1: Getting login page...")
    login_url = f'{base_url}/auth/login'
    response = opener.open(login_url)
    login_html = response.read().decode('utf-8', errors='replace')
    print(f"Login page status: {response.getcode()}")
    
    # Extract CSRF token from the login page (rough extraction)
    csrf_token = None
    for line in login_html.split('\n'):
        if 'name="csrf_token"' in line and 'value=' in line:
            start = line.find('value="') + 7
            end = line.find('"', start)
            csrf_token = line[start:end]
            break
    
    print(f"CSRF token found: {csrf_token[:20] if csrf_token else 'None'}...")
    
    # Step 2: Perform login with student credentials
    print("\nStep 2: Logging in as student...")
    login_data = {
        'email': 'thabo.mthembu@student.example.com',  # Use a known student email
        'password': 'student_password',
        'csrf_token': csrf_token or '',
        'remember': 'on'
    }
    
    post_data = urllib.parse.urlencode(login_data).encode('utf-8')
    login_request = urllib.request.Request(login_url, data=post_data, method='POST')
    login_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        login_response = opener.open(login_request)
        print(f"Login response status: {login_response.getcode()}")
        print(f"Login response URL: {login_response.url}")
        
        # Check for authentication cookies
        print(f"Cookies after login: {len(cookie_jar)}")
        for cookie in cookie_jar:
            print(f"  Cookie: {cookie.name}={cookie.value[:20]}...")
        
    except urllib.error.HTTPError as e:
        print(f"Login failed with HTTP {e.code}: {e.reason}")
        return
    
    # Step 3: Access student dashboard with session
    print("\nStep 3: Accessing student dashboard...")
    dashboard_url = f'{base_url}/student/dashboard'
    
    try:
        dashboard_response = opener.open(dashboard_url)
        dashboard_html = dashboard_response.read().decode('utf-8', errors='replace')
        
        print(f"Dashboard response status: {dashboard_response.getcode()}")
        print(f"Dashboard response URL: {dashboard_response.url}")
        print(f"Dashboard content length: {len(dashboard_html)}")
        
        # Check if we got the login page or the actual dashboard
        if '<title>Login - SACEL</title>' in dashboard_html:
            print("❌ Still getting login page - authentication failed")
        elif '<title>Student Dashboard - SACEL</title>' in dashboard_html or 'student' in dashboard_html.lower():
            print("✅ Got student dashboard content")
        else:
            print("? Got unknown page")
        
        # Show a preview of the content
        print("\n--- Dashboard HTML Preview ---")
        print(dashboard_html[:1500])
        
    except urllib.error.HTTPError as e:
        print(f"Dashboard access failed with HTTP {e.code}: {e.reason}")

if __name__ == '__main__':
    test_student_dashboard()