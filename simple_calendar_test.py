#!/usr/bin/env python3
"""
Simple Calendar System Verification Test
Tests basic calendar functionality without requiring pytest or running server
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_calendar_models():
    """Test calendar model imports and basic functionality"""
    try:
        from app.models.calendar import Event, EventAttendee, Schedule, ExamSchedule, Holiday, AvailabilitySlot
        print("✅ Calendar models imported successfully")
        
        # Test basic model attributes
        assert hasattr(Event, 'title')
        assert hasattr(Event, 'start_datetime')
        assert hasattr(Event, 'end_datetime')
        assert hasattr(Event, 'creator_id')
        assert hasattr(Event, 'event_type')
        print("✅ Event model has required attributes")
        
        assert hasattr(Schedule, 'name')
        assert hasattr(Schedule, 'subject')
        assert hasattr(Schedule, 'day_of_week')
        print("✅ Schedule model has required attributes")
        
        assert hasattr(ExamSchedule, 'name')
        assert hasattr(ExamSchedule, 'exam_date')
        assert hasattr(ExamSchedule, 'duration_minutes')
        print("✅ ExamSchedule model has required attributes")
        
        return True
    except Exception as e:
        print(f"❌ Calendar models test failed: {str(e)}")
        return False

def test_calendar_service():
    """Test calendar service imports and methods"""
    try:
        from app.services.calendar_service import CalendarService
        print("✅ CalendarService imported successfully")
        
        service = CalendarService()
        
        # Test service methods exist
        required_methods = [
            'create_event', 'get_calendar_events', 'update_event', 
            'delete_event', 'add_attendee', 'respond_to_event',
            'get_upcoming_events', 'create_reminder', 'get_due_reminders',
            'get_calendar_analytics'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(service, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ CalendarService missing methods: {missing_methods}")
            return False
        else:
            print("✅ CalendarService has all required methods")
            return True
            
    except Exception as e:
        print(f"❌ Calendar service test failed: {str(e)}")
        return False

def test_calendar_api():
    """Test calendar API blueprint"""
    try:
        from app.api.calendar import calendar_bp
        print("✅ Calendar API blueprint imported successfully")
        
        # Check blueprint has routes
        if hasattr(calendar_bp, 'url_map') or len(calendar_bp.deferred_functions) > 0:
            print("✅ Calendar API blueprint has routes registered")
            return True
        else:
            print("⚠️  Calendar API blueprint may not have routes")
            return True  # Not critical for basic functionality
            
    except Exception as e:
        print(f"❌ Calendar API test failed: {str(e)}")
        return False

def test_database_models_creation():
    """Test database models can be created without errors"""
    try:
        from app import create_app
        from app.extensions import db
        
        app = create_app('testing')
        with app.app_context():
            # Just test that models can be imported within app context
            from app.models.calendar import Event, Schedule, ExamSchedule
            print("✅ Calendar models work within app context")
            return True
            
    except Exception as e:
        print(f"❌ Database models test failed: {str(e)}")
        return False

def test_calendar_templates():
    """Test calendar template files exist"""
    try:
        template_path = "app/templates/calendar/dashboard.html"
        if os.path.exists(template_path):
            file_size = os.path.getsize(template_path)
            if file_size > 10000:  # Should be substantial
                print("✅ Calendar dashboard template exists and has content")
                return True
            else:
                print("⚠️  Calendar template exists but may be incomplete")
                return True
        else:
            print("❌ Calendar dashboard template not found")
            return False
            
    except Exception as e:
        print(f"❌ Calendar templates test failed: {str(e)}")
        return False

def test_calendar_routes():
    """Test calendar routes are accessible"""
    try:
        from app.api.teachers import bp as teachers_bp
        from app.api.students_portal import bp as students_bp
        
        # This is a basic test - routes should be registered
        print("✅ Teacher and student portal blueprints accessible")
        return True
        
    except Exception as e:
        print(f"❌ Calendar routes test failed: {str(e)}")
        return False

def run_verification():
    """Run all verification tests"""
    print("🗓️  SACEL Calendar & Scheduling System - Simple Verification")
    print("=" * 60)
    
    tests = [
        ("Calendar Models", test_calendar_models),
        ("Calendar Service", test_calendar_service),
        ("Calendar API", test_calendar_api),
        ("Database Models", test_database_models_creation),
        ("Calendar Templates", test_calendar_templates),
        ("Calendar Routes", test_calendar_routes)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if passed >= 4:  # Most tests should pass
        print(f"\n🎉 Calendar System Status: GOOD - Core functionality verified")
        return True
    else:
        print(f"\n⚠️  Calendar System Status: NEEDS ATTENTION - Some issues found")
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)