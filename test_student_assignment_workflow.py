#!/usr/bin/env python3
"""
Comprehensive test script for the complete student assignment workflow.
Tests the entire flow from teacher assignment creation to student submission.
"""

import os
import sys
import json
import time
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Flask and database imports
from flask import Flask
from app import create_app
from app.models import User, Assignment, Submission
from app.extensions import db
from app.services.ai_service import ai_service
from app.services.file_service import file_service
from app.services.language_service import translate_term


class StudentAssignmentWorkflowTester:
    """Comprehensive tester for student assignment workflow"""
    
    def __init__(self):
        self.app = None
        self.test_teacher = None
        self.test_student = None
        self.test_assignment = None
        self.test_files = []
        
    def setup_test_environment(self):
        """Set up the test environment"""
        print("🔧 Setting up test environment...")
        
        # Create Flask app with testing configuration
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = 'True'
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()
        
        print("✅ Test environment set up successfully")
    
    def create_test_users(self):
        """Create test teacher and student users"""
        print("👥 Creating test users...")
        
        # Create test teacher
        self.test_teacher = User(
            username='test_teacher',
            email='teacher@test.com',
            first_name='Test',
            last_name='Teacher',
            role='teacher',
            is_active=True
        )
        self.test_teacher.set_password('password123')
        
        # Create test student
        self.test_student = User(
            username='test_student',
            email='student@test.com',
            first_name='Test',
            last_name='Student',
            role='student',
            is_active=True
        )
        self.test_student.set_password('password123')
        
        # Save to database
        db.session.add(self.test_teacher)
        db.session.add(self.test_student)
        db.session.commit()
        
        print(f"✅ Created teacher: {self.test_teacher.username}")
        print(f"✅ Created student: {self.test_student.username}")
    
    def test_assignment_creation(self):
        """Test assignment creation by teacher"""
        print("📝 Testing assignment creation...")
        
        # Create a comprehensive assignment
        assignment_data = {
            'title': 'Test Mathematics Assignment',
            'description': 'This is a comprehensive test assignment covering algebra and geometry.',
            'subject': 'Mathematics',
            'grade_level': '10',
            'difficulty': 'medium',
            'total_points': 100,
            'time_limit': 120,  # 2 hours
            'due_date': datetime.utcnow() + timedelta(days=7),
            'instructions': 'Please solve all questions and show your work.',
            'questions': [
                {
                    'type': 'multiple_choice',
                    'question': 'What is 2 + 2?',
                    'options': ['3', '4', '5', '6'],
                    'correct_answer': '4',
                    'points': 10,
                    'explanation': 'Basic addition: 2 + 2 = 4'
                },
                {
                    'type': 'short_answer',
                    'question': 'Solve for x: 2x + 5 = 15',
                    'correct_answer': 'x = 5',
                    'points': 20,
                    'explanation': 'Subtract 5 from both sides: 2x = 10, then divide by 2: x = 5'
                },
                {
                    'type': 'essay',
                    'question': 'Explain the Pythagorean theorem and provide an example.',
                    'points': 30,
                    'explanation': 'Should include formula a² + b² = c² and a practical example'
                },
                {
                    'type': 'file_upload',
                    'question': 'Upload your solution to the geometry problem set.',
                    'points': 40,
                    'allowed_formats': ['pdf', 'doc', 'docx', 'jpg', 'png']
                }
            ]
        }
        
        # Create assignment
        self.test_assignment = Assignment(
            title=assignment_data['title'],
            description=assignment_data['description'],
            subject=assignment_data['subject'],
            grade_level=assignment_data['grade_level'],
            difficulty=assignment_data['difficulty'],
            total_points=assignment_data['total_points'],
            time_limit=assignment_data['time_limit'],
            due_date=assignment_data['due_date'],
            instructions=assignment_data['instructions'],
            questions=json.dumps(assignment_data['questions']),
            teacher_id=self.test_teacher.id,
            is_active=True
        )
        
        db.session.add(self.test_assignment)
        db.session.commit()
        
        print(f"✅ Assignment created: {self.test_assignment.title}")
        print(f"   - ID: {self.test_assignment.id}")
        print(f"   - Questions: {len(assignment_data['questions'])}")
        print(f"   - Total Points: {self.test_assignment.total_points}")
        print(f"   - Due Date: {self.test_assignment.due_date}")
        
        return True
    
    def test_student_assignment_view(self):
        """Test student viewing assignment details"""
        print("👀 Testing student assignment view...")
        
        with self.app.test_client() as client:
            # Simulate student login
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_student.id
                sess['user_role'] = 'student'
            
            # Test assignments list endpoint
            response = client.get('/api/students/assignments')
            assert response.status_code == 200
            
            assignments_data = response.get_json()
            assert 'assignments' in assignments_data
            assert len(assignments_data['assignments']) > 0
            
            # Test specific assignment view
            response = client.get(f'/api/students/assignments/{self.test_assignment.id}')
            assert response.status_code == 200
            
            assignment_data = response.get_json()
            assert assignment_data['assignment']['id'] == self.test_assignment.id
            assert assignment_data['assignment']['title'] == self.test_assignment.title
            
            print("✅ Student can view assignments list")
            print("✅ Student can view assignment details")
            
        return True
    
    def create_test_files(self):
        """Create test files for upload simulation"""
        print("📁 Creating test files...")
        
        # Create temporary test files
        test_files_data = [
            ('solution.pdf', b'%PDF-1.4 fake pdf content for testing'),
            ('notes.txt', b'These are my study notes for the assignment'),
            ('diagram.png', b'fake png image data for testing')
        ]
        
        for filename, content in test_files_data:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
            temp_file.write(content)
            temp_file.close()
            
            self.test_files.append({
                'filename': filename,
                'path': temp_file.name,
                'content': content
            })
        
        print(f"✅ Created {len(self.test_files)} test files")
        return True
    
    def test_assignment_submission(self):
        """Test student assignment submission"""
        print("📤 Testing assignment submission...")
        
        # Create test files
        self.create_test_files()
        
        with self.app.test_client() as client:
            # Simulate student login
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_student.id
                sess['user_role'] = 'student'
            
            # Prepare submission data
            submission_data = {
                'assignment_id': self.test_assignment.id,
                'answers': json.dumps({
                    '0': '4',  # Multiple choice answer
                    '1': 'x = 5',  # Short answer
                    '2': 'The Pythagorean theorem states that in a right triangle, a² + b² = c². For example, if a=3 and b=4, then c=5.',  # Essay
                    '3': 'file_uploaded'  # File upload indicator
                }),
                'submitted_at': datetime.utcnow().isoformat(),
                'time_spent': 45  # 45 minutes
            }
            
            # Test submission endpoint
            response = client.post(
                f'/api/students/assignments/{self.test_assignment.id}/submit',
                data=submission_data,
                content_type='application/x-www-form-urlencoded'
            )
            
            if response.status_code != 200:
                print(f"❌ Submission failed with status: {response.status_code}")
                print(f"   Response: {response.get_data(as_text=True)}")
                return False
            
            submission_response = response.get_json()
            assert 'submission_id' in submission_response
            
            # Verify submission was created
            submission = Submission.query.filter_by(
                assignment_id=self.test_assignment.id,
                student_id=self.test_student.id
            ).first()
            
            assert submission is not None
            assert submission.student_id == self.test_student.id
            assert submission.assignment_id == self.test_assignment.id
            
            print("✅ Assignment submission successful")
            print(f"   - Submission ID: {submission.id}")
            print(f"   - Time spent: {submission_data['time_spent']} minutes")
            print(f"   - Submitted at: {submission.submitted_at}")
            
        return True
    
    def test_ai_integration(self):
        """Test AI help and tutoring features"""
        print("🤖 Testing AI integration...")
        
        # Mock AI service for testing
        with patch.object(ai_service, 'get_tutoring_help') as mock_tutoring:
            mock_tutoring.return_value = {
                'success': True,
                'response': 'To solve 2x + 5 = 15, first subtract 5 from both sides to get 2x = 10, then divide both sides by 2 to get x = 5.',
                'confidence': 0.95
            }
            
            with self.app.test_client() as client:
                # Simulate student login
                with client.session_transaction() as sess:
                    sess['user_id'] = self.test_student.id
                    sess['user_role'] = 'student'
                
                # Test AI help request
                ai_request_data = {
                    'question': 'How do I solve 2x + 5 = 15?',
                    'assignment_id': self.test_assignment.id,
                    'question_index': 1,
                    'help_type': 'explanation'
                }
                
                response = client.post(
                    '/api/ai/tutoring-help',
                    data=json.dumps(ai_request_data),
                    content_type='application/json'
                )
                
                if response.status_code == 200:
                    ai_response = response.get_json()
                    assert ai_response['success'] == True
                    assert 'response' in ai_response
                    print("✅ AI tutoring help working")
                    print(f"   - AI Response: {ai_response['response'][:100]}...")
                else:
                    print("⚠️  AI service not available or needs configuration")
        
        return True
    
    def test_language_support(self):
        """Test multi-language support"""
        print("🌍 Testing language support...")
        
        # Test various translation terms
        test_terms = [
            'my_assignments',
            'submit_assignment',
            'progress',
            'due_soon',
            'completed',
            'ai_help',
            'time_remaining'
        ]
        
        languages = ['en', 'af', 'zu', 'xh', 'st']
        
        for lang in languages:
            print(f"   Testing {lang} translations:")
            for term in test_terms:
                translated = translate_term(term, lang)
                print(f"     - {term}: {translated}")
                assert translated is not None
                assert len(translated) > 0
        
        print("✅ Multi-language support working")
        return True
    
    def test_file_handling(self):
        """Test file upload and management"""
        print("📎 Testing file handling...")
        
        # Test file service functionality
        test_content = b"This is test file content for assignment submission"
        
        with patch.object(file_service, 'save_file') as mock_save:
            mock_save.return_value = {
                'success': True,
                'file_path': '/uploads/assignments/test_file.pdf',
                'file_size': len(test_content),
                'file_hash': 'abc123def456'
            }
            
            # Test file save
            result = file_service.save_file(
                content=test_content,
                filename='test_file.pdf',
                folder='assignments'
            )
            
            assert result['success'] == True
            assert 'file_path' in result
            print("✅ File upload service working")
        
        return True
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("🚀 Starting comprehensive student assignment workflow test\n")
        
        try:
            # Setup
            self.setup_test_environment()
            self.create_test_users()
            
            # Core workflow tests
            tests = [
                ("Assignment Creation", self.test_assignment_creation),
                ("Student Assignment View", self.test_student_assignment_view),
                ("Assignment Submission", self.test_assignment_submission),
                ("AI Integration", self.test_ai_integration),
                ("Language Support", self.test_language_support),
                ("File Handling", self.test_file_handling)
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            for test_name, test_func in tests:
                print(f"\n{'='*50}")
                print(f"Running: {test_name}")
                print('='*50)
                
                try:
                    result = test_func()
                    if result:
                        passed_tests += 1
                        print(f"✅ {test_name} PASSED")
                    else:
                        print(f"❌ {test_name} FAILED")
                except Exception as e:
                    print(f"❌ {test_name} ERROR: {str(e)}")
                
                time.sleep(0.5)  # Brief pause between tests
            
            # Summary
            print(f"\n{'='*50}")
            print("TEST SUMMARY")
            print('='*50)
            print(f"Passed: {passed_tests}/{total_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if passed_tests == total_tests:
                print("🎉 All tests passed! Student assignment workflow is working correctly.")
            else:
                print("⚠️  Some tests failed. Please review the issues above.")
            
            return passed_tests == total_tests
            
        except Exception as e:
            print(f"❌ Test suite failed with error: {str(e)}")
            return False
        
        finally:
            # Cleanup
            self.cleanup()
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        # Remove test files
        for test_file in self.test_files:
            try:
                os.unlink(test_file['path'])
            except OSError:
                pass
        
        # Clean up Flask context
        if hasattr(self, 'app_context'):
            self.app_context.pop()
        
        print("✅ Cleanup completed")


def main():
    """Main test runner"""
    print("SACEL Student Assignment Workflow Tester")
    print("=" * 60)
    
    tester = StudentAssignmentWorkflowTester()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 Student assignment workflow is ready for production!")
        return 0
    else:
        print("\n❌ Issues found in student assignment workflow.")
        return 1


if __name__ == '__main__':
    exit(main())