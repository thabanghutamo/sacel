#!/usr/bin/env python3
"""
Simple page testing without external dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import urllib.request
import urllib.error
import re

def test_pages():
    """Test pages using built-in urllib"""
    base_url = "http://localhost:5000"
    
    test_pages = [
        ('/', 'Home Page'),
        ('/auth/login', 'Login Page'), 
        ('/student/dashboard', 'Student Dashboard'),
        ('/teachers/dashboard', 'Teacher Dashboard'),
        ('/admin/dashboard', 'Admin Dashboard'),
        ('/schools', 'Schools Page'),
        ('/about', 'About Page'),
    ]
    
    print("🔍 SACEL Platform Page Testing")
    print("=" * 50)
    
    results = {}
    
    for path, name in test_pages:
        print(f"\n📄 Testing: {name} ({path})")
        
        try:
            url = f"{base_url}{path}"
            response = urllib.request.urlopen(url, timeout=10)
            
            content = response.read().decode('utf-8')
            content_length = len(content)
            
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "No title"
            
            # Check for key indicators
            has_login = 'login' in content.lower()
            has_dashboard = 'dashboard' in content.lower() 
            has_error = 'error' in content.lower() or 'traceback' in content.lower()
            has_form = '<form' in content.lower()
            
            print(f"  ✅ Status: 200 OK")
            print(f"  📝 Title: {title}")
            print(f"  📊 Content: {content_length} chars")
            print(f"  🔐 Has login: {has_login}")
            print(f"  📋 Has dashboard: {has_dashboard}")
            print(f"  📝 Has form: {has_form}")
            print(f"  ❌ Has error: {has_error}")
            
            results[path] = {
                'status': 200,
                'title': title,
                'content_length': content_length,
                'has_login': has_login,
                'has_dashboard': has_dashboard,
                'has_error': has_error,
                'content_preview': content[:200]
            }
            
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP Error: {e.code}")
            if e.code == 302:
                print(f"  🔄 Likely redirect (authentication required)")
            results[path] = {'status': e.code, 'error': str(e)}
            
        except Exception as e:
            print(f"  💥 Error: {str(e)[:100]}")
            results[path] = {'error': str(e)}
    
    # Analysis
    print(f"\n{'='*50}")
    print("📊 ANALYSIS")
    print("-" * 20)
    
    # Check for identical content
    content_lengths = [r['content_length'] for r in results.values() if 'content_length' in r]
    if content_lengths:
        unique_lengths = set(content_lengths)
        if len(unique_lengths) == 1 and len(content_lengths) > 1:
            print(f"⚠️  WARNING: All pages have identical content ({content_lengths[0]} chars)")
            print("   All pages are likely showing the same content")
        else:
            print(f"✅ Pages have different content lengths: {unique_lengths}")
    
    # Check titles
    titles = [r['title'] for r in results.values() if 'title' in r]
    unique_titles = set(titles)
    if len(unique_titles) == 1 and len(titles) > 1:
        print(f"⚠️  WARNING: All pages have same title: '{titles[0]}'")
    else:
        print(f"✅ Pages have different titles")
    
    # Check for login patterns
    login_pages = sum(1 for r in results.values() if r.get('has_login', False))
    if login_pages > 2:  # More than just login page itself
        print(f"🔐 WARNING: {login_pages} pages show login content")
        print("   Authentication might be redirecting all pages to login")
    
    return results

if __name__ == '__main__':
    results = test_pages()
    
    print(f"\n{'='*50}")
    print("🎯 NEXT STEPS")
    print("-" * 15)
    
    # Show content preview of one page to understand what's being served
    if results:
        first_result = next(iter(results.values()))
        if 'content_preview' in first_result:
            print("📄 Content preview:")
            print(first_result['content_preview'])
    
    print("\n✅ Testing complete!")