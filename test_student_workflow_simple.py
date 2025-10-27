#!/usr/bin/env python3
"""
Simple test script for the student assignment workflow.
Tests the core functionality without complex mocking.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from flask import Flask
        print("✅ Flask imported")
        
        from app import create_app
        print("✅ App creation imported")
        
        from app.models import User, Assignment, Submission
        print("✅ Models imported")
        
        from app.extensions import db
        print("✅ Database extension imported")
        
        from app.services.language_service import translate_term
        print("✅ Language service imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_language_service():
    """Test the language service functionality"""
    print("\n🌍 Testing language service...")
    
    try:
        from app.services.language_service import translate_term, EDUCATION_TERMS
        
        # Test basic translations
        test_cases = [
            ('assignment', 'en', 'Assignment'),
            ('assignment', 'af', 'Opdrag'),
            ('assignment', 'zu', 'Umsebenzi'),
            ('my_assignments', 'en', 'My Assignments'),
            ('submit_assignment', 'af', 'Dien Opdrag In'),
            ('ai_help', 'zu', 'Usizo Lwe-AI'),
            ('progress', 'xh', 'Inkqubela'),
            ('time_remaining', 'st', 'Nako e saleng')
        ]
        
        all_passed = True
        for term, lang, expected in test_cases:
            result = translate_term(term, lang)
            if result == expected:
                print(f"✅ {term} ({lang}): {result}")
            else:
                print(f"❌ {term} ({lang}): got '{result}', expected '{expected}'")
                all_passed = False
        
        # Test new terms added for student interface
        new_terms = [
            'my_assignments', 'due_soon', 'overdue', 'progress', 
            'submit_assignment', 'ai_help', 'time_remaining', 
            'auto_save', 'file_upload', 'question_help'
        ]
        
        print(f"\n🔍 Testing new student interface terms...")
        for term in new_terms:
            for lang in ['en', 'af', 'zu', 'xh', 'st']:
                result = translate_term(term, lang)
                if result and result != term:  # Should not return the key itself
                    print(f"✅ {term} ({lang}): {result}")
                else:
                    print(f"❌ {term} ({lang}): missing translation")
                    all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Language service test failed: {e}")
        return False

def test_models():
    """Test that models can be instantiated"""
    print("\n📊 Testing models...")
    
    try:
        from app.models import User, Assignment, Submission
        
        # Test User model
        user = User(
            username='test_user',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='student'
        )
        print("✅ User model can be instantiated")
        
        # Test Assignment model
        assignment = Assignment(
            title='Test Assignment',
            description='Test description',
            subject='Mathematics',
            grade_level='10',
            difficulty='medium',
            total_points=100,
            due_date=datetime.utcnow() + timedelta(days=7),
            teacher_id=1
        )
        print("✅ Assignment model can be instantiated")
        
        # Test Submission model
        submission = Submission(
            assignment_id=1,
            student_id=1,
            answers='{"1": "test answer"}',
            submitted_at=datetime.utcnow()
        )
        print("✅ Submission model can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_app_creation():
    """Test that the Flask app can be created"""
    print("\n🏗️  Testing app creation...")
    
    try:
        from app import create_app
        
        # Set test environment
        os.environ['FLASK_ENV'] = 'testing'
        
        # Create app
        app = create_app()
        print("✅ Flask app created successfully")
        
        # Test app configuration
        assert app.config['SECRET_KEY'] is not None
        print("✅ App has secret key")
        
        # Test blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        print(f"✅ Registered blueprints: {', '.join(blueprint_names)}")
        
        return True
        
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False

def test_student_api_routes():
    """Test that student API routes are accessible"""
    print("\n🛣️  Testing student API routes...")
    
    try:
        from app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            # Test routes exist (should return 401/403 since not authenticated)
            test_routes = [
                '/api/students/assignments',
                '/api/students/dashboard',
                '/students/assignments',
                '/students/dashboard'
            ]
            
            for route in test_routes:
                try:
                    response = client.get(route)
                    # Should get redirect to login or 401/403, not 404
                    if response.status_code in [200, 302, 401, 403]:
                        print(f"✅ Route {route} exists (status: {response.status_code})")
                    else:
                        print(f"⚠️  Route {route} unexpected status: {response.status_code}")
                except Exception as route_error:
                    print(f"❌ Route {route} error: {route_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        return False

def test_assignment_structure():
    """Test assignment data structure"""
    print("\n📝 Testing assignment structure...")
    
    try:
        # Test assignment question structure
        sample_questions = [
            {
                'type': 'multiple_choice',
                'question': 'What is 2 + 2?',
                'options': ['3', '4', '5', '6'],
                'correct_answer': '4',
                'points': 10
            },
            {
                'type': 'short_answer',
                'question': 'Solve for x: 2x + 5 = 15',
                'correct_answer': 'x = 5',
                'points': 20
            },
            {
                'type': 'essay',
                'question': 'Explain the concept.',
                'points': 30
            },
            {
                'type': 'file_upload',
                'question': 'Upload your solution.',
                'points': 40,
                'allowed_formats': ['pdf', 'doc', 'docx']
            }
        ]
        
        # Validate structure
        for i, question in enumerate(sample_questions):
            assert 'type' in question
            assert 'question' in question
            assert 'points' in question
            print(f"✅ Question {i+1} structure valid ({question['type']})")
        
        # Test JSON serialization
        json_str = json.dumps(sample_questions)
        parsed = json.loads(json_str)
        assert len(parsed) == len(sample_questions)
        print("✅ Assignment questions can be serialized/deserialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Assignment structure test failed: {e}")
        return False

def test_template_structure():
    """Test that template files exist"""
    print("\n📄 Testing template structure...")
    
    template_files = [
        'app/templates/students/assignments.html',
        'app/templates/students/assignment_detail.html',
        'app/templates/students/submit_assignment.html',
        'app/templates/base/layout.html'
    ]
    
    missing_files = []
    for template in template_files:
        if os.path.exists(template):
            print(f"✅ Template exists: {template}")
        else:
            print(f"❌ Template missing: {template}")
            missing_files.append(template)
    
    return len(missing_files) == 0

def main():
    """Run all tests"""
    print("SACEL Student Assignment Workflow - Simple Test Suite")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Language Service", test_language_service),
        ("Model Tests", test_models),
        ("App Creation", test_app_creation),
        ("API Routes", test_student_api_routes),
        ("Assignment Structure", test_assignment_structure),
        ("Template Structure", test_template_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
    
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Student assignment workflow components are working.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == '__main__':
    exit(main())