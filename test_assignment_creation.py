#!/usr/bin/env python3
"""Test assignment creation functionality"""
import requests
import json
from datetime import datetime, timedelta

def test_assignment_creation():
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
        
        # Test assignment creation page
        print("Testing assignment creation page access...")
        create_page_response = session.get(f"{base_url}/teachers/assignments/create")
        
        if create_page_response.status_code == 200:
            print("✅ Assignment creation page accessible")
            
            # Test assignment creation
            print("Testing assignment creation...")
            due_date = (datetime.now() + timedelta(days=7)).isoformat()
            
            assignment_data = {
                'title': 'Test Assignment - Python Basics',
                'description': 'A test assignment to check functionality',
                'subject': 'Technology',
                'grade_level': 10,
                'due_date': due_date,
                'max_score': 100,
                'instructions': 'Complete the Python exercises and submit your solutions.',
                'is_draft': False
            }
            
            create_response = session.post(
                f"{base_url}/teachers/assignments",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(assignment_data)
            )
            
            if create_response.status_code == 201:
                response_data = create_response.json()
                print(f"✅ Assignment created successfully! ID: {response_data.get('assignment_id')}")
                
                # Test assignments listing
                print("Testing assignments listing...")
                list_response = session.get(f"{base_url}/teachers/assignments")
                
                if list_response.status_code == 200:
                    print("✅ Assignments listing accessible")
                    print("🎉 Assignment creation system working correctly!")
                    return True
                else:
                    print(f"❌ Assignments listing failed: {list_response.status_code}")
                    return False
            else:
                print(f"❌ Assignment creation failed: {create_response.status_code}")
                print(f"Response: {create_response.text}")
                return False
        else:
            print(f"❌ Assignment creation page not accessible: {create_page_response.status_code}")
            return False
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_assignment_creation()
        print("\n" + "="*50)
        if success:
            print("🎉 ASSIGNMENT CREATION SYSTEM TEST PASSED!")
        else:
            print("❌ ASSIGNMENT CREATION SYSTEM TEST FAILED!")
        print("="*50)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")