#!/usr/bin/env python3
"""
Comprehensive template and authentication testing script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
import time

def test_page_authentication():
    """Test page authentication and content rendering"""
    base_url = "http://localhost:5000"
    
    # Test pages to check
    test_pages = [
        ('/', 'Home Page'),
        ('/auth/login', 'Login Page'),
        ('/student/dashboard', 'Student Dashboard'),
        ('/teachers/dashboard', 'Teacher Dashboard'),
        ('/admin/dashboard', 'Admin Dashboard'),
        ('/student/assignments', 'Student Assignments'),
        ('/teachers/assignments', 'Teacher Assignments'),
        ('/schools', 'Schools Page'),
        ('/about', 'About Page'),
    ]
    
    session = requests.Session()
    
    print("🔍 SACEL Platform Page Analysis")
    print("=" * 60)
    
    results = {}
    
    for path, name in test_pages:
        try:
            print(f"\n📄 Testing: {name} ({path})")
            response = session.get(f"{base_url}{path}", allow_redirects=False, timeout=10)
            
            # Analyze response
            status = response.status_code
            content_length = len(response.content)
            
            if status == 200:
                # Parse HTML to get more details
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title"
                
                # Check for specific content indicators
                has_login_form = bool(soup.find('form', {'action': lambda x: x and 'login' in x}))
                has_dashboard = bool(soup.find('div', class_=lambda x: x and 'dashboard' in x))
                has_error = bool(soup.find('div', class_=lambda x: x and 'error' in x))
                
                print(f"  ✅ Status: {status}")
                print(f"  📝 Title: {title_text}")
                print(f"  📊 Content: {content_length} chars")
                print(f"  🔐 Has login form: {has_login_form}")
                print(f"  📋 Has dashboard: {has_dashboard}")
                print(f"  ❌ Has error: {has_error}")
                
                results[path] = {
                    'status': status,
                    'title': title_text,
                    'content_length': content_length,
                    'has_login_form': has_login_form,
                    'has_dashboard': has_dashboard,
                    'has_error': has_error
                }
                
            elif status == 302:
                location = response.headers.get('Location', 'Unknown')
                print(f"  🔄 Redirect: {status} → {location}")
                results[path] = {'status': status, 'redirect': location}
                
            elif status == 500:
                print(f"  💥 Server Error: {status}")
                print(f"  📊 Content: {content_length} chars")
                # Try to get error details
                if content_length > 0:
                    error_snippet = response.text[:200] if hasattr(response, 'text') else "No error details"
                    print(f"  🔍 Error snippet: {error_snippet}")
                results[path] = {'status': status, 'error': True}
                
            else:
                print(f"  ⚠️  Status: {status}")
                results[path] = {'status': status}
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Connection Error: {str(e)[:100]}")
            results[path] = {'error': str(e)}
        except Exception as e:
            print(f"  💥 Unexpected Error: {str(e)[:100]}")
            results[path] = {'error': str(e)}
    
    # Analyze results
    print(f"\n{'='*60}")
    print("📊 ANALYSIS SUMMARY")
    print("-" * 30)
    
    # Count different types of responses
    status_200_count = sum(1 for r in results.values() if r.get('status') == 200)
    status_302_count = sum(1 for r in results.values() if r.get('status') == 302)
    status_500_count = sum(1 for r in results.values() if r.get('status') == 500)
    error_count = sum(1 for r in results.values() if 'error' in r and r.get('status') != 500)
    
    print(f"✅ Status 200 (OK): {status_200_count}")
    print(f"🔄 Status 302 (Redirect): {status_302_count}")
    print(f"💥 Status 500 (Server Error): {status_500_count}")
    print(f"❌ Connection Errors: {error_count}")
    
    # Check for identical content
    content_lengths = [r.get('content_length') for r in results.values() if r.get('content_length')]
    if content_lengths:
        unique_lengths = set(content_lengths)
        if len(unique_lengths) == 1 and len(content_lengths) > 1:
            print(f"⚠️  WARNING: All pages have identical content length ({content_lengths[0]} chars)")
            print("   This suggests all pages are showing the same content (likely login page)")
    
    # Check authentication issues
    login_forms = sum(1 for r in results.values() if r.get('has_login_form'))
    if login_forms > 3:  # More than just login page
        print(f"🔐 WARNING: {login_forms} pages showing login forms")
        print("   This suggests authentication is not working properly")
    
    return results

def test_login_functionality():
    """Test if login functionality works"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print(f"\n🔐 TESTING LOGIN FUNCTIONALITY")
    print("-" * 40)
    
    try:
        # First get the login page
        login_response = session.get(f"{base_url}/auth/login")
        if login_response.status_code != 200:
            print(f"❌ Cannot access login page: Status {login_response.status_code}")
            return False
        
        print("✅ Login page accessible")
        
        # Parse login form
        soup = BeautifulSoup(login_response.content, 'html.parser')
        form = soup.find('form')
        if not form:
            print("❌ No login form found on login page")
            return False
            
        print("✅ Login form found")
        
        # Check for CSRF token
        csrf_token = soup.find('input', {'name': 'csrf_token'})
        if csrf_token:
            print("✅ CSRF token found")
        else:
            print("⚠️  No CSRF token found")
        
        return True
        
    except Exception as e:
        print(f"❌ Login test error: {str(e)[:100]}")
        return False

if __name__ == '__main__':
    print("🚀 Starting SACEL Platform Diagnosis...")
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    # Test pages
    page_results = test_page_authentication()
    
    # Test login
    login_works = test_login_functionality()
    
    print(f"\n{'='*60}")
    print("🎯 RECOMMENDATIONS")
    print("-" * 20)
    
    # Analyze and provide recommendations
    if any(r.get('status') == 500 for r in page_results.values()):
        print("1. 💥 Fix server errors (500 status) - check Flask logs")
    
    if any(r.get('has_error') for r in page_results.values()):
        print("2. 🔧 Fix template rendering errors")
    
    content_lengths = [r.get('content_length') for r in page_results.values() if r.get('content_length')]
    if len(set(content_lengths)) == 1 and len(content_lengths) > 1:
        print("3. 🔐 Fix authentication - all pages showing same content")
    
    if not login_works:
        print("4. 🔑 Fix login functionality")
    
    print("\n✅ Diagnosis complete!")