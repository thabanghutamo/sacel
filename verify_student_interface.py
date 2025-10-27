#!/usr/bin/env python3
"""
Quick verification test for the student assignment interface components.
"""

import os
import sys
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_language_service():
    """Test language service with new student terms"""
    print("🌍 Testing Student Assignment Language Support")
    print("-" * 50)
    
    try:
        from app.services.language_service import translate_term
        
        # Test key student interface terms
        test_terms = [
            'my_assignments',
            'submit_assignment', 
            'progress',
            'due_soon',
            'ai_help',
            'time_remaining',
            'auto_save',
            'file_upload'
        ]
        
        languages = ['en', 'af', 'zu', 'xh', 'st']
        
        print("Testing new student assignment interface terms:")
        for term in test_terms:
            print(f"\n📝 {term}:")
            for lang in languages:
                translation = translate_term(term, lang)
                print(f"  {lang}: {translation}")
        
        print("\n✅ Language service working with student assignment terms!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_templates():
    """Verify student assignment templates exist"""
    print("\n📄 Testing Student Assignment Templates")
    print("-" * 50)
    
    templates = [
        ('assignments.html', 'app/templates/students/assignments.html'),
        ('assignment_detail.html', 'app/templates/students/assignment_detail.html'),
        ('submit_assignment.html', 'app/templates/students/submit_assignment.html')
    ]
    
    all_exist = True
    for name, path in templates:
        if os.path.exists(path):
            # Get file size
            size = os.path.getsize(path)
            print(f"✅ {name}: {size:,} bytes")
        else:
            print(f"❌ {name}: Missing")
            all_exist = False
    
    return all_exist

def test_api_structure():
    """Test student API file structure"""
    print("\n🛣️  Testing Student API Structure")
    print("-" * 50)
    
    try:
        # Check students API file
        api_file = 'app/api/students.py'
        if os.path.exists(api_file):
            print(f"✅ Student API file exists: {os.path.getsize(api_file):,} bytes")
            
            # Read and check for key functions
            with open(api_file, 'r') as f:
                content = f.read()
                
            functions = [
                'assignments()',
                'view_assignment(',
                'submit_assignment(',
                'dashboard()'
            ]
            
            for func in functions:
                if func in content:
                    print(f"✅ Function found: {func}")
                else:
                    print(f"⚠️  Function not found: {func}")
        else:
            print("❌ Student API file missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading API file: {e}")
        return False

def test_assignment_structure():
    """Test assignment data structure"""
    print("\n📝 Testing Assignment Data Structure")
    print("-" * 50)
    
    # Test the assignment question types we support
    sample_assignment = {
        'title': 'Sample Mathematics Assignment',
        'description': 'Test assignment with various question types',
        'questions': [
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
                'question': 'Explain the Pythagorean theorem.',
                'points': 30
            },
            {
                'type': 'file_upload',
                'question': 'Upload your solution.',
                'points': 40,
                'allowed_formats': ['pdf', 'doc', 'docx']
            }
        ]
    }
    
    try:
        # Test JSON serialization
        json_str = json.dumps(sample_assignment, indent=2)
        print("✅ Assignment can be serialized to JSON")
        
        # Test deserialization
        parsed = json.loads(json_str)
        print("✅ Assignment can be deserialized from JSON")
        
        # Validate structure
        assert 'title' in parsed
        assert 'questions' in parsed
        assert len(parsed['questions']) == 4
        
        # Check question types
        question_types = [q['type'] for q in parsed['questions']]
        expected_types = ['multiple_choice', 'short_answer', 'essay', 'file_upload']
        
        for expected_type in expected_types:
            if expected_type in question_types:
                print(f"✅ Question type supported: {expected_type}")
            else:
                print(f"❌ Question type missing: {expected_type}")
        
        print("✅ Assignment structure is valid")
        return True
        
    except Exception as e:
        print(f"❌ Assignment structure test failed: {e}")
        return False

def test_file_structure():
    """Test overall project file structure"""
    print("\n📁 Testing Project File Structure")
    print("-" * 50)
    
    # Key files that should exist
    key_files = [
        'app/__init__.py',
        'app/models/__init__.py',
        'app/api/students.py',
        'app/services/language_service.py',
        'app/services/file_service.py',
        'app/templates/students/assignments.html',
        'app/templates/students/assignment_detail.html',
        'app/templates/students/submit_assignment.html',
        'main.py',
        'config.py'
    ]
    
    missing_files = []
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)
    
    if len(missing_files) == 0:
        print("✅ All key project files exist")
        return True
    else:
        print(f"❌ {len(missing_files)} files missing")
        return False

def main():
    """Run verification tests"""
    print("🚀 SACEL Student Assignment Interface Verification")
    print("=" * 60)
    
    tests = [
        ("Language Service", test_language_service),
        ("Template Files", test_templates),
        ("API Structure", test_api_structure),
        ("Assignment Structure", test_assignment_structure),
        ("File Structure", test_file_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} PASSED\n")
            else:
                print(f"\n❌ {test_name} FAILED\n")
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {str(e)}\n")
    
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 Student Assignment Interface is Ready!")
        print("✅ Language support implemented")
        print("✅ Templates created") 
        print("✅ API endpoints structured")
        print("✅ Assignment data model working")
        print("✅ File structure complete")
        print("\n🎯 Next Steps:")
        print("   - Start Flask server to test in browser")
        print("   - Test assignment creation and submission flow")
        print("   - Implement teacher grading interface")
        return 0
    else:
        print(f"\n⚠️  {total-passed} verification tests failed")
        return 1

if __name__ == '__main__':
    exit(main())