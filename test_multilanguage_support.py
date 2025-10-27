"""
Multi-Language Support Testing Script for SACEL Platform
Tests language switching, content localization, and AI content generation in multiple languages
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
LANGUAGE_ENDPOINTS = {
    'switch': f"{BASE_URL}/api/language/switch",
    'current': f"{BASE_URL}/api/language/current",
    'available': f"{BASE_URL}/api/language/available",
    'demo_page': f"{BASE_URL}/language-demo"
}

AI_ENDPOINT = f"{BASE_URL}/api/ai/generate-assignment"

# Test languages - South African official languages
TEST_LANGUAGES = [
    ('en', 'English'),
    ('af', 'Afrikaans'),
    ('zu', 'IsiZulu'),
    ('xh', 'IsiXhosa'),
    ('st', 'Sesotho')
]

# Sample assignment data for AI testing in different languages
ASSIGNMENT_DATA_TEMPLATE = {
    'subject': 'Natural Sciences',
    'grade': 7,
    'topic': 'Photosynthesis',
    'assignment_type': 'quiz',
    'difficulty': 'medium',
    'question_count': 3,
    'language': 'english'  # This will be updated for each language
}

class MultiLanguageTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = []
    
    def test_language_detection(self):
        """Test automatic language detection"""
        print("🔍 Testing Language Detection...")
        
        try:
            response = self.session.get(LANGUAGE_ENDPOINTS['current'])
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Current language: {data.get('language')} ({data.get('language_name')})")
                return True
            else:
                print(f"❌ Language detection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Language detection error: {e}")
            return False
    
    def test_available_languages(self):
        """Test getting available languages"""
        print("\n📋 Testing Available Languages...")
        
        try:
            response = self.session.get(LANGUAGE_ENDPOINTS['available'])
            if response.status_code == 200:
                data = response.json()
                languages = data.get('languages', [])
                print(f"✅ Found {len(languages)} supported languages:")
                for lang in languages:
                    indicator = "🔵" if lang.get('current') else "⚪"
                    print(f"   {indicator} {lang['code']}: {lang['name']}")
                return True
            else:
                print(f"❌ Failed to get languages: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting languages: {e}")
            return False
    
    def test_language_switching(self):
        """Test switching between different languages"""
        print("\n🔄 Testing Language Switching...")
        
        success_count = 0
        for code, name in TEST_LANGUAGES:
            try:
                print(f"   Switching to {name} ({code})...")
                
                response = self.session.post(
                    LANGUAGE_ENDPOINTS['switch'],
                    json={'language': code},
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"   ✅ Successfully switched to {data.get('language_name')}")
                        success_count += 1
                    else:
                        print(f"   ❌ Switch failed: {data.get('error')}")
                else:
                    print(f"   ❌ HTTP error: {response.status_code}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error switching to {name}: {e}")
        
        print(f"✅ Language switching: {success_count}/{len(TEST_LANGUAGES)} successful")
        return success_count == len(TEST_LANGUAGES)
    
    def test_ai_content_generation_multilingual(self):
        """Test AI content generation in multiple languages"""
        print("\n🤖 Testing AI Content Generation in Multiple Languages...")
        
        # Login first (you might need to update credentials)
        login_data = {
            'email': 'teacher@example.com',
            'password': 'password123'
        }
        
        login_response = self.session.post(f"{BASE_URL}/auth/login", data=login_data)
        if login_response.status_code != 200:
            print("❌ Could not login to test AI features")
            return False
        
        success_count = 0
        for code, name in TEST_LANGUAGES[:3]:  # Test first 3 languages to save time
            try:
                print(f"   Generating content in {name}...")
                
                # Update assignment data for this language
                assignment_data = ASSIGNMENT_DATA_TEMPLATE.copy()
                assignment_data['language'] = name.lower()
                
                response = self.session.post(
                    AI_ENDPOINT,
                    json=assignment_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        assignment = data.get('assignment', {})
                        questions = assignment.get('questions', [])
                        print(f"   ✅ Generated {len(questions)} questions in {name}")
                        
                        # Show sample question
                        if questions:
                            sample_question = questions[0].get('question', '')[:100]
                            print(f"      Sample: {sample_question}...")
                        
                        success_count += 1
                    else:
                        print(f"   ❌ AI generation failed: {data.get('error')}")
                else:
                    print(f"   ❌ HTTP error: {response.status_code}")
                
                time.sleep(2)  # Rate limiting for AI API
                
            except Exception as e:
                print(f"   ❌ Error generating content in {name}: {e}")
        
        print(f"✅ AI content generation: {success_count}/3 languages successful")
        return success_count > 0
    
    def test_content_localization(self):
        """Test content localization on demo page"""
        print("\n📄 Testing Content Localization...")
        
        try:
            response = self.session.get(LANGUAGE_ENDPOINTS['demo_page'])
            if response.status_code == 200:
                content = response.text
                
                # Check for localized content markers
                localization_markers = [
                    'translate_term',  # Template function usage
                    'current_language',  # Language detection
                    'get_languages'  # Language list
                ]
                
                found_markers = sum(1 for marker in localization_markers if marker in content)
                
                print(f"✅ Demo page loaded successfully")
                print(f"✅ Found {found_markers}/{len(localization_markers)} localization features")
                
                return found_markers > 0
            else:
                print(f"❌ Demo page failed to load: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Content localization test error: {e}")
            return False
    
    def test_performance_impact(self):
        """Test performance impact of language features"""
        print("\n⚡ Testing Performance Impact...")
        
        try:
            # Test response times for language operations
            start_time = time.time()
            
            # Multiple language switches
            for _ in range(5):
                for code, _ in TEST_LANGUAGES[:3]:
                    self.session.post(
                        LANGUAGE_ENDPOINTS['switch'],
                        json={'language': code},
                        headers={'Content-Type': 'application/json'}
                    )
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / 15  # 5 iterations * 3 languages
            
            print(f"✅ Average language switch time: {avg_time:.3f} seconds")
            
            if avg_time < 0.5:
                print("✅ Performance: Excellent (< 0.5s)")
            elif avg_time < 1.0:
                print("✅ Performance: Good (< 1.0s)")
            else:
                print("⚠️ Performance: Could be improved (> 1.0s)")
            
            return avg_time < 1.0
            
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive multi-language testing"""
        print("🌍 SACEL Multi-Language Support Testing Suite")
        print("=" * 60)
        
        tests = [
            ("Language Detection", self.test_language_detection),
            ("Available Languages", self.test_available_languages),
            ("Language Switching", self.test_language_switching),
            ("Content Localization", self.test_content_localization),
            ("AI Multi-Language Generation", self.test_ai_content_generation_multilingual),
            ("Performance Impact", self.test_performance_impact)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                print(f"\n🧪 Running: {test_name}")
                if test_func():
                    passed += 1
                    self.results.append((test_name, "PASS"))
                else:
                    self.results.append((test_name, "FAIL"))
            except Exception as e:
                print(f"❌ Test '{test_name}' crashed: {e}")
                self.results.append((test_name, "ERROR"))
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print("-" * 30)
        
        for test_name, result in self.results:
            emoji = "✅" if result == "PASS" else "❌" if result == "FAIL" else "💥"
            print(f"{emoji} {test_name}: {result}")
        
        print(f"\n🏆 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All multi-language features working perfectly!")
        elif passed >= total * 0.75:
            print("✅ Most multi-language features working well!")
        elif passed >= total * 0.5:
            print("⚠️ Some multi-language features need attention")
        else:
            print("🚨 Multi-language features need significant work")
        
        return passed / total

if __name__ == "__main__":
    tester = MultiLanguageTester()
    success_rate = tester.run_all_tests()
    
    print(f"\n📈 Success Rate: {success_rate:.1%}")
    exit(0 if success_rate >= 0.8 else 1)