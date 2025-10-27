"""
AI Integration Testing Script for SACEL Platform
Tests the AI-enhanced assignment creation and content generation features
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_ENDPOINT = f"{BASE_URL}/auth/login"
AI_ENDPOINTS = {
    'generate_assignment': f"{BASE_URL}/api/ai/generate-assignment",
    'generate_content': f"{BASE_URL}/api/ai/generate-content",
    'grade_assignment': f"{BASE_URL}/api/ai/grade-assignment",
    'check_plagiarism': f"{BASE_URL}/api/ai/check-plagiarism",
    'translate_content': f"{BASE_URL}/api/ai/translate-content"
}

# Test data
TEST_TEACHER_CREDENTIALS = {
    'email': 'teacher@example.com',
    'password': 'password123'
}

ASSIGNMENT_DATA = {
    'subject': 'Natural Sciences',
    'grade': 7,
    'topic': 'Photosynthesis',
    'assignment_type': 'quiz',
    'difficulty': 'medium',
    'question_count': 5,
    'language': 'english'
}

RUBRIC_DATA = {
    'content_type': 'rubric',
    'subject': 'Mathematics',
    'grade': 9,
    'topic': 'Algebra',
    'assignment_type': 'test',
    'language': 'english'
}

INSTRUCTIONS_DATA = {
    'content_type': 'instructions',
    'subject': 'English',
    'grade': 8,
    'topic': 'Creative Writing',
    'title': 'Short Story Assignment',
    'existing_instructions': 'Write a short story about friendship.',
    'language': 'english'
}

GRADING_DATA = {
    'questions': [
        'What is photosynthesis?',
        'Name the main components needed for photosynthesis.',
        'Where does photosynthesis occur in plants?'
    ],
    'answers': [
        'The process by which plants make their own food using sunlight.',
        'Sunlight, water, carbon dioxide, and chlorophyll.',
        'In the leaves, specifically in the chloroplasts.'
    ],
    'assignment_type': 'quiz'
}

PLAGIARISM_DATA = {
    'student_text': 'Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.',
    'reference_texts': [
        'Photosynthesis is a process used by plants to convert light energy into chemical energy.',
        'Plants use photosynthesis to make glucose from carbon dioxide and water using sunlight.'
    ]
}

TRANSLATION_DATA = {
    'text': 'Complete this assignment by reading the chapter and answering all questions.',
    'target_language': 'afrikaans'
}

class AITester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self):
        """Login as a teacher to access AI endpoints"""
        print("🔐 Logging in as teacher...")
        
        response = self.session.post(LOGIN_ENDPOINT, data=TEST_TEACHER_CREDENTIALS)
        
        if response.status_code == 200:
            self.logged_in = True
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    
    def test_assignment_generation(self):
        """Test AI assignment generation"""
        print("\n📝 Testing AI Assignment Generation...")
        
        response = self.session.post(
            AI_ENDPOINTS['generate_assignment'],
            json=ASSIGNMENT_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                assignment = data.get('assignment', {})
                print(f"✅ Generated assignment: {assignment.get('title', 'No title')}")
                print(f"   Questions: {len(assignment.get('questions', []))}")
                print(f"   Estimated time: {assignment.get('estimated_time', 'Not specified')}")
                return True
            else:
                print(f"❌ Assignment generation failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return False
    
    def test_rubric_generation(self):
        """Test AI rubric generation"""
        print("\n📊 Testing AI Rubric Generation...")
        
        response = self.session.post(
            AI_ENDPOINTS['generate_content'],
            json=RUBRIC_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                rubric = data.get('rubric', '')
                print(f"✅ Generated rubric ({len(rubric)} characters)")
                print(f"   Subject: {data.get('metadata', {}).get('subject')}")
                return True
            else:
                print(f"❌ Rubric generation failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
        
        return False
    
    def test_instructions_enhancement(self):
        """Test AI instruction enhancement"""
        print("\n📋 Testing AI Instructions Enhancement...")
        
        response = self.session.post(
            AI_ENDPOINTS['generate_content'],
            json=INSTRUCTIONS_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                instructions = data.get('instructions', '')
                print(f"✅ Enhanced instructions ({len(instructions)} characters)")
                print(f"   Topic: {data.get('metadata', {}).get('topic')}")
                return True
            else:
                print(f"❌ Instructions enhancement failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
        
        return False
    
    def test_grading_assistance(self):
        """Test AI grading assistance"""
        print("\n🎯 Testing AI Grading Assistance...")
        
        response = self.session.post(
            AI_ENDPOINTS['grade_assignment'],
            json=GRADING_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                result = data.get('grading_result', {})
                print(f"✅ Grading completed: {result.get('overall_score', 'No score')}%")
                print(f"   Feedback items: {len(result.get('feedback', []))}")
                return True
            else:
                print(f"❌ Grading failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
        
        return False
    
    def test_plagiarism_detection(self):
        """Test AI plagiarism detection"""
        print("\n🔍 Testing AI Plagiarism Detection...")
        
        response = self.session.post(
            AI_ENDPOINTS['check_plagiarism'],
            json=PLAGIARISM_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                analysis = data.get('plagiarism_analysis', {})
                similarity = analysis.get('similarity_score', 0)
                print(f"✅ Plagiarism check completed: {similarity}% similarity")
                print(f"   Risk level: {analysis.get('risk_level', 'Unknown')}")
                return True
            else:
                print(f"❌ Plagiarism check failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
        
        return False
    
    def test_translation(self):
        """Test AI content translation"""
        print("\n🌍 Testing AI Content Translation...")
        
        response = self.session.post(
            AI_ENDPOINTS['translate_content'],
            json=TRANSLATION_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                translated = data.get('translated_text', '')
                target_lang = data.get('target_language', '')
                print(f"✅ Translation to {target_lang} completed")
                print(f"   Original: {data.get('original_text', '')[:50]}...")
                print(f"   Translated: {translated[:50]}...")
                return True
            else:
                print(f"❌ Translation failed: {data.get('error')}")
        else:
            print(f"❌ Request failed: {response.status_code}")
        
        return False
    
    def run_all_tests(self):
        """Run comprehensive AI feature tests"""
        print("🤖 SACEL AI Integration Testing Suite")
        print("=" * 50)
        
        if not self.login():
            print("❌ Cannot proceed without login")
            return
        
        tests = [
            self.test_assignment_generation,
            self.test_rubric_generation,
            self.test_instructions_enhancement,
            self.test_grading_assistance,
            self.test_plagiarism_detection,
            self.test_translation
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"❌ Test error: {e}")
        
        print("\n" + "=" * 50)
        print(f"🏆 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All AI features working correctly!")
        elif passed > total // 2:
            print("⚠️  Most AI features working, some issues detected")
        else:
            print("🚨 Multiple AI features have issues")
        
        return passed == total

if __name__ == "__main__":
    tester = AITester()
    tester.run_all_tests()