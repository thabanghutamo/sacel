"""
Test script for Communication Center functionality
Verifies all communication features are working correctly
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/auth/login"
COMMUNICATION_API_URL = f"{BASE_URL}/api/communication"

# Test credentials (you'll need to adjust these)
TEST_TEACHER = {
    "email": "teacher@test.com",
    "password": "password123"
}

TEST_STUDENT = {
    "email": "student@test.com", 
    "password": "password123"
}

class CommunicationTester:
    def __init__(self):
        self.session = requests.Session()
        self.teacher_session = requests.Session()
        self.student_session = requests.Session()
        
    def login_as_teacher(self):
        """Login as teacher and store session"""
        try:
            login_data = {
                "email": TEST_TEACHER["email"],
                "password": TEST_TEACHER["password"]
            }
            
            response = self.teacher_session.post(LOGIN_URL, data=login_data)
            if response.status_code == 200:
                print("✓ Teacher login successful")
                return True
            else:
                print(f"✗ Teacher login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Teacher login error: {str(e)}")
            return False
    
    def login_as_student(self):
        """Login as student and store session"""
        try:
            login_data = {
                "email": TEST_STUDENT["email"],
                "password": TEST_STUDENT["password"]
            }
            
            response = self.student_session.post(LOGIN_URL, data=login_data)
            if response.status_code == 200:
                print("✓ Student login successful")
                return True
            else:
                print(f"✗ Student login failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Student login error: {str(e)}")
            return False
    
    def test_send_message(self):
        """Test sending a message"""
        print("\n--- Testing Message Sending ---")
        
        try:
            message_data = {
                "recipient_ids": [2],  # Assuming student has ID 2
                "subject": "Test Message from Communication Center",
                "content": "This is a test message to verify the communication center is working correctly.",
                "priority": "normal",
                "message_type": "personal"
            }
            
            response = self.teacher_session.post(
                f"{COMMUNICATION_API_URL}/messages/send",
                json=message_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✓ Message sent successfully")
                print(f"  Message ID: {result.get('message_id')}")
                print(f"  Recipients: {result.get('recipients_count')}")
                return result.get('message_id')
            else:
                print(f"✗ Failed to send message: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error sending message: {str(e)}")
            return None
    
    def test_get_messages(self):
        """Test getting messages"""
        print("\n--- Testing Message Retrieval ---")
        
        try:
            response = self.student_session.get(f"{COMMUNICATION_API_URL}/messages?folder=inbox")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Messages retrieved successfully")
                print(f"  Total messages: {len(result.get('messages', []))}")
                print(f"  Unread count: {result.get('unread_count', 0)}")
                
                if result.get('messages'):
                    latest_message = result['messages'][0]
                    print(f"  Latest message: {latest_message.get('subject')}")
                    return latest_message.get('id')
                return None
            else:
                print(f"✗ Failed to get messages: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error getting messages: {str(e)}")
            return None
    
    def test_mark_message_read(self, message_id):
        """Test marking a message as read"""
        print("\n--- Testing Mark Message as Read ---")
        
        if not message_id:
            print("✗ No message ID provided")
            return False
            
        try:
            response = self.student_session.post(
                f"{COMMUNICATION_API_URL}/messages/{message_id}/read"
            )
            
            if response.status_code == 200:
                print("✓ Message marked as read successfully")
                return True
            else:
                print(f"✗ Failed to mark message as read: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error marking message as read: {str(e)}")
            return False
    
    def test_create_announcement(self):
        """Test creating an announcement"""
        print("\n--- Testing Announcement Creation ---")
        
        try:
            announcement_data = {
                "title": "Test System Announcement",
                "content": "This is a test announcement from the communication center testing script.",
                "target_audience": ["student", "teacher"],
                "priority": "normal"
            }
            
            response = self.teacher_session.post(
                f"{COMMUNICATION_API_URL}/announcements/create",
                json=announcement_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✓ Announcement created successfully")
                print(f"  Message ID: {result.get('message_id')}")
                print(f"  Recipients: {result.get('recipients_count')}")
                return True
            else:
                print(f"✗ Failed to create announcement: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error creating announcement: {str(e)}")
            return False
    
    def test_forum_post(self):
        """Test creating a forum post"""
        print("\n--- Testing Forum Post Creation ---")
        
        try:
            post_data = {
                "category": "general",
                "title": "Test Forum Post from Communication Center",
                "content": "This is a test forum post to verify the forum functionality is working correctly.",
                "tags": ["test", "communication", "forum"]
            }
            
            response = self.teacher_session.post(
                f"{COMMUNICATION_API_URL}/forum/posts/create",
                json=post_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✓ Forum post created successfully")
                print(f"  Post ID: {result.get('post_id')}")
                return result.get('post_id')
            else:
                print(f"✗ Failed to create forum post: {response.status_code}")
                print(f"  Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"✗ Error creating forum post: {str(e)}")
            return None
    
    def test_get_forum_posts(self):
        """Test getting forum posts"""
        print("\n--- Testing Forum Post Retrieval ---")
        
        try:
            response = self.student_session.get(f"{COMMUNICATION_API_URL}/forum/posts")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Forum posts retrieved successfully")
                print(f"  Total posts: {len(result.get('posts', []))}")
                
                if result.get('posts'):
                    latest_post = result['posts'][0]
                    print(f"  Latest post: {latest_post.get('title')}")
                return True
            else:
                print(f"✗ Failed to get forum posts: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error getting forum posts: {str(e)}")
            return False
    
    def test_send_notification(self):
        """Test sending a notification"""
        print("\n--- Testing Notification Sending ---")
        
        try:
            notification_data = {
                "user_ids": [2],  # Assuming student has ID 2
                "title": "Test Notification",
                "message": "This is a test notification from the communication center.",
                "category": "academic"
            }
            
            response = self.teacher_session.post(
                f"{COMMUNICATION_API_URL}/notifications/send",
                json=notification_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                result = response.json()
                print("✓ Notification sent successfully")
                print(f"  Notifications sent: {result.get('notifications_sent')}")
                return True
            else:
                print(f"✗ Failed to send notification: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error sending notification: {str(e)}")
            return False
    
    def test_get_notifications(self):
        """Test getting notifications"""
        print("\n--- Testing Notification Retrieval ---")
        
        try:
            response = self.student_session.get(f"{COMMUNICATION_API_URL}/notifications")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Notifications retrieved successfully")
                print(f"  Total notifications: {len(result.get('notifications', []))}")
                print(f"  Unread count: {result.get('unread_count', 0)}")
                
                if result.get('notifications'):
                    latest_notification = result['notifications'][0]
                    print(f"  Latest notification: {latest_notification.get('title')}")
                    return latest_notification.get('id')
                return None
            else:
                print(f"✗ Failed to get notifications: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"✗ Error getting notifications: {str(e)}")
            return None
    
    def test_communication_stats(self):
        """Test getting communication statistics"""
        print("\n--- Testing Communication Statistics ---")
        
        try:
            response = self.student_session.get(f"{COMMUNICATION_API_URL}/stats/overview")
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Communication stats retrieved successfully")
                stats = result.get('stats', {})
                print(f"  Unread messages: {stats.get('unread_messages', 0)}")
                print(f"  Unread notifications: {stats.get('unread_notifications', 0)}")
                print(f"  Recent messages (30d): {stats.get('recent_messages_30d', 0)}")
                return True
            else:
                print(f"✗ Failed to get communication stats: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error getting communication stats: {str(e)}")
            return False
    
    def test_user_search(self):
        """Test user search functionality"""
        print("\n--- Testing User Search ---")
        
        try:
            response = self.teacher_session.get(
                f"{COMMUNICATION_API_URL}/users/search?q=test&limit=5"
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✓ User search successful")
                print(f"  Users found: {result.get('count', 0)}")
                
                for user in result.get('users', []):
                    print(f"    - {user.get('name')} ({user.get('role')})")
                return True
            else:
                print(f"✗ Failed to search users: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error searching users: {str(e)}")
            return False
    
    def test_communication_analytics(self):
        """Test communication analytics"""
        print("\n--- Testing Communication Analytics ---")
        
        try:
            response = self.teacher_session.get(
                f"{COMMUNICATION_API_URL}/analytics?timeframe=30d&scope=personal"
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✓ Communication analytics retrieved successfully")
                analytics = result.get('analytics', {})
                print(f"  Timeframe: {analytics.get('timeframe')}")
                print(f"  Messages sent: {analytics.get('messages_sent', 0)}")
                print(f"  Messages received: {analytics.get('messages_received', 0)}")
                return True
            else:
                print(f"✗ Failed to get communication analytics: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"✗ Error getting communication analytics: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all communication center tests"""
        print("=" * 60)
        print("COMMUNICATION CENTER TESTING")
        print("=" * 60)
        
        # Test server connection
        try:
            response = requests.get(BASE_URL, timeout=5)
            print("✓ Server is running and accessible")
        except Exception as e:
            print(f"✗ Cannot connect to server: {str(e)}")
            print("Please ensure the Flask development server is running on localhost:5000")
            return False
        
        # Login tests
        teacher_login = self.login_as_teacher()
        student_login = self.login_as_student()
        
        if not teacher_login or not student_login:
            print("\n✗ Login tests failed. Please check user credentials.")
            return False
        
        # Core functionality tests
        message_id = self.test_send_message()
        retrieved_message_id = self.test_get_messages()
        
        if retrieved_message_id:
            self.test_mark_message_read(retrieved_message_id)
        
        self.test_create_announcement()
        post_id = self.test_forum_post()
        self.test_get_forum_posts()
        self.test_send_notification()
        notification_id = self.test_get_notifications()
        self.test_communication_stats()
        self.test_user_search()
        self.test_communication_analytics()
        
        print("\n" + "=" * 60)
        print("COMMUNICATION CENTER TESTING COMPLETE")
        print("=" * 60)
        
        return True

def main():
    """Main test function"""
    tester = CommunicationTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 Communication Center testing completed!")
            print("Review the results above to verify all features are working correctly.")
        else:
            print("\n❌ Communication Center testing failed!")
            print("Please check the error messages and ensure all components are properly configured.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")

if __name__ == "__main__":
    main()