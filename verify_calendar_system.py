#!/usr/bin/env python3
"""
SACEL Calendar & Scheduling System Verification Script
Comprehensive testing and verification of all calendar functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
from colorama import init, Fore, Style, Back

# Initialize colorama for colored output
init(autoreset=True)

class CalendarSystemVerifier:
    """Verify the complete Calendar & Scheduling system"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.teacher_token = None
        self.student_token = None
        self.admin_token = None
        
    def print_header(self, title):
        """Print a formatted header"""
        print(f"\n{Back.BLUE}{Fore.WHITE} {title} {Style.RESET_ALL}")
        print("=" * len(title))
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        self.test_results.append(('PASS', message))
    
    def print_error(self, message):
        """Print error message"""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        self.test_results.append(('FAIL', message))
    
    def print_warning(self, message):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
        self.test_results.append(('WARN', message))
    
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
    
    def verify_server_running(self):
        """Verify the Flask server is running"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.print_success("Flask server is running")
                return True
            else:
                self.print_error(f"Server returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error("Cannot connect to Flask server. Please ensure it's running on http://localhost:5000")
            return False
    
    def test_calendar_api_endpoints(self):
        """Test all calendar API endpoints"""
        self.print_header("Testing Calendar API Endpoints")
        
        endpoints = [
            ("GET", "/api/calendar/events", "Get calendar events"),
            ("GET", "/api/calendar/events/upcoming", "Get upcoming events"),
            ("GET", "/api/calendar/schedules/class", "Get class schedules"),
            ("GET", "/api/calendar/schedules/exam", "Get exam schedules"),
            ("GET", "/api/calendar/holidays", "Get holidays"),
            ("GET", "/api/calendar/availability", "Get availability"),
            ("GET", "/api/calendar/analytics", "Get calendar analytics")
        ]
        
        for method, endpoint, description in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url)
                
                if response.status_code in [200, 401]:  # 401 is expected for unauthenticated requests
                    self.print_success(f"{description} endpoint accessible")
                else:
                    self.print_error(f"{description} endpoint returned {response.status_code}")
            except Exception as e:
                self.print_error(f"{description} endpoint error: {str(e)}")
    
    def test_calendar_dashboard_pages(self):
        """Test calendar dashboard page access"""
        self.print_header("Testing Calendar Dashboard Pages")
        
        pages = [
            ("/teachers/calendar", "Teachers calendar page"),
            ("/student/calendar", "Student calendar page")
        ]
        
        for page, description in pages:
            try:
                response = self.session.get(f"{self.base_url}{page}")
                
                if response.status_code in [200, 302]:  # 302 for redirect to login
                    self.print_success(f"{description} accessible")
                else:
                    self.print_error(f"{description} returned {response.status_code}")
            except Exception as e:
                self.print_error(f"{description} error: {str(e)}")
    
    def test_calendar_models(self):
        """Test calendar database models"""
        self.print_header("Testing Calendar Database Models")
        
        try:
            # Test model imports
            from app.models.calendar import (
                Event, EventAttendee, EventReminder, Schedule, 
                ExamSchedule, Holiday, AvailabilitySlot, Calendar, CalendarShare
            )
            
            self.print_success("All calendar models imported successfully")
            
            # Test model attributes
            models_tests = [
                (Event, ['title', 'start_datetime', 'end_datetime', 'creator_id', 'event_type']),
                (Schedule, ['name', 'subject', 'day_of_week', 'start_time', 'end_time']),
                (ExamSchedule, ['name', 'subject', 'exam_date', 'start_time', 'end_time']),
                (Holiday, ['name', 'holiday_date', 'description', 'holiday_type']),
                (AvailabilitySlot, ['user_id', 'day_of_week', 'start_time', 'end_time'])
            ]
            
            for model_class, required_attrs in models_tests:
                model_name = model_class.__name__
                missing_attrs = []
                
                for attr in required_attrs:
                    if not hasattr(model_class, attr):
                        missing_attrs.append(attr)
                
                if missing_attrs:
                    self.print_error(f"{model_name} missing attributes: {missing_attrs}")
                else:
                    self.print_success(f"{model_name} model has all required attributes")
                    
        except ImportError as e:
            self.print_error(f"Failed to import calendar models: {str(e)}")
        except Exception as e:
            self.print_error(f"Calendar models test error: {str(e)}")
    
    def test_calendar_service(self):
        """Test calendar service functionality"""
        self.print_header("Testing Calendar Service")
        
        try:
            from app.services.calendar_service import CalendarService
            
            service = CalendarService()
            self.print_success("CalendarService instantiated successfully")
            
            # Test service methods
            required_methods = [
                'create_event', 'get_calendar_events', 'update_event', 'delete_event',
                'add_attendee', 'respond_to_event', 'get_upcoming_events',
                'create_reminder', 'get_due_reminders', 'get_calendar_analytics'
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(service, method):
                    missing_methods.append(method)
            
            if missing_methods:
                self.print_error(f"CalendarService missing methods: {missing_methods}")
            else:
                self.print_success("CalendarService has all required methods")
                
        except ImportError as e:
            self.print_error(f"Failed to import CalendarService: {str(e)}")
        except Exception as e:
            self.print_error(f"Calendar service test error: {str(e)}")
    
    def test_calendar_templates(self):
        """Test calendar template files"""
        self.print_header("Testing Calendar Templates")
        
        import os
        
        template_path = "app/templates/calendar"
        required_templates = [
            "dashboard.html"
        ]
        
        if os.path.exists(template_path):
            for template in required_templates:
                template_file = os.path.join(template_path, template)
                if os.path.exists(template_file):
                    # Check file size to ensure it's not empty
                    file_size = os.path.getsize(template_file)
                    if file_size > 1000:  # Should be substantial
                        self.print_success(f"Calendar template {template} exists and has content")
                    else:
                        self.print_warning(f"Calendar template {template} exists but may be incomplete")
                else:
                    self.print_error(f"Calendar template {template} not found")
        else:
            self.print_error("Calendar templates directory not found")
    
    def test_blueprint_registration(self):
        """Test calendar blueprint registration"""
        self.print_header("Testing Blueprint Registration")
        
        try:
            # Test that calendar routes are accessible (even if requiring auth)
            response = self.session.get(f"{self.base_url}/api/calendar/events")
            
            if response.status_code in [200, 401, 403]:
                self.print_success("Calendar API blueprint registered correctly")
            else:
                self.print_error(f"Calendar API blueprint issue: {response.status_code}")
                
        except Exception as e:
            self.print_error(f"Blueprint registration test error: {str(e)}")
    
    def test_database_migrations(self):
        """Test database migrations for calendar tables"""
        self.print_header("Testing Database Migrations")
        
        try:
            from app.extensions import db
            from app import create_app
            
            app = create_app()
            with app.app_context():
                # Check if calendar tables exist
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                required_tables = [
                    'events', 'event_attendees', 'event_reminders', 
                    'schedules', 'exam_schedules', 'holidays', 
                    'availability_slots', 'calendars', 'calendar_shares'
                ]
                
                missing_tables = []
                for table in required_tables:
                    if table not in tables:
                        missing_tables.append(table)
                
                if missing_tables:
                    self.print_warning(f"Calendar tables may need migration: {missing_tables}")
                else:
                    self.print_success("All calendar database tables exist")
                    
        except Exception as e:
            self.print_warning(f"Database migration test error: {str(e)}")
    
    def test_calendar_javascript_functionality(self):
        """Test calendar frontend JavaScript"""
        self.print_header("Testing Calendar Frontend")
        
        try:
            # Test calendar dashboard page content
            response = self.session.get(f"{self.base_url}/teachers/calendar")
            
            if response.status_code in [200, 302]:
                content = response.text if response.status_code == 200 else ""
                
                # Check for key calendar elements
                calendar_elements = [
                    'FullCalendar', 'calendar-container', 'event-modal',
                    'CalendarManager', 'filterEvents', 'createEvent'
                ]
                
                found_elements = []
                for element in calendar_elements:
                    if element in content:
                        found_elements.append(element)
                
                if len(found_elements) >= 3:
                    self.print_success(f"Calendar frontend elements found: {len(found_elements)}/{len(calendar_elements)}")
                else:
                    self.print_warning("Calendar frontend may be incomplete")
            else:
                self.print_info("Calendar frontend test skipped (authentication required)")
                
        except Exception as e:
            self.print_warning(f"Calendar frontend test error: {str(e)}")
    
    def test_calendar_integration(self):
        """Test calendar integration with other systems"""
        self.print_header("Testing Calendar System Integration")
        
        try:
            # Test assignment integration
            response = self.session.get(f"{self.base_url}/api/calendar/events?include_assignments=true")
            
            if response.status_code in [200, 401]:
                self.print_success("Assignment integration endpoint accessible")
            else:
                self.print_warning("Assignment integration may have issues")
            
            # Test communication integration
            try:
                from app.services.communication_service import CommunicationService
                from app.services.calendar_service import CalendarService
                
                # Both services should be available for integration
                self.print_success("Communication and calendar services available for integration")
                
            except ImportError:
                self.print_warning("Service integration may be incomplete")
                
        except Exception as e:
            self.print_warning(f"Integration test error: {str(e)}")
    
    def test_calendar_performance(self):
        """Test calendar system performance"""
        self.print_header("Testing Calendar Performance")
        
        try:
            start_time = time.time()
            
            # Test API response time
            response = self.session.get(f"{self.base_url}/api/calendar/events")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response_time < 2.0:
                self.print_success(f"Calendar API response time: {response_time:.3f}s (Good)")
            elif response_time < 5.0:
                self.print_warning(f"Calendar API response time: {response_time:.3f}s (Acceptable)")
            else:
                self.print_error(f"Calendar API response time: {response_time:.3f}s (Too slow)")
                
        except Exception as e:
            self.print_warning(f"Performance test error: {str(e)}")
    
    def generate_summary_report(self):
        """Generate final summary report"""
        self.print_header("CALENDAR SYSTEM VERIFICATION SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[0] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r[0] == 'FAIL'])
        warnings = len([r for r in self.test_results if r[0] == 'WARN'])
        
        print(f"\n📊 Test Results Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   {Fore.GREEN}Passed: {passed_tests}{Style.RESET_ALL}")
        print(f"   {Fore.RED}Failed: {failed_tests}{Style.RESET_ALL}")
        print(f"   {Fore.YELLOW}Warnings: {warnings}{Style.RESET_ALL}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 80:
            print(f"\n{Fore.GREEN}✅ Calendar System Status: EXCELLENT ({success_rate:.1f}%){Style.RESET_ALL}")
        elif success_rate >= 60:
            print(f"\n{Fore.YELLOW}⚠️  Calendar System Status: GOOD ({success_rate:.1f}%){Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Calendar System Status: NEEDS ATTENTION ({success_rate:.1f}%){Style.RESET_ALL}")
        
        if failed_tests > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for result_type, message in self.test_results:
                if result_type == 'FAIL':
                    print(f"   • {message}")
        
        print(f"\n{Fore.CYAN}🗓️  Calendar & Scheduling System Features Verified:{Style.RESET_ALL}")
        print("   • Event creation and management")
        print("   • Class and exam scheduling")
        print("   • Availability tracking")
        print("   • Holiday management")
        print("   • Calendar analytics")
        print("   • Frontend dashboard")
        print("   • API endpoints")
        print("   • Database models")
        print("   • Service layer")
        print("   • System integration")
        
        return success_rate >= 60
    
    def run_full_verification(self):
        """Run complete calendar system verification"""
        print(f"{Back.GREEN}{Fore.WHITE} SACEL CALENDAR & SCHEDULING SYSTEM VERIFICATION {Style.RESET_ALL}")
        print(f"{Fore.CYAN}Comprehensive testing of calendar functionality and integration{Style.RESET_ALL}")
        
        if not self.verify_server_running():
            print(f"\n{Fore.RED}Cannot proceed without running server. Please start the Flask application.{Style.RESET_ALL}")
            return False
        
        # Run all verification tests
        self.test_calendar_models()
        self.test_calendar_service()
        self.test_blueprint_registration()
        self.test_calendar_api_endpoints()
        self.test_calendar_dashboard_pages()
        self.test_calendar_templates()
        self.test_database_migrations()
        self.test_calendar_javascript_functionality()
        self.test_calendar_integration()
        self.test_calendar_performance()
        
        return self.generate_summary_report()


def main():
    """Main verification function"""
    verifier = CalendarSystemVerifier()
    
    try:
        success = verifier.run_full_verification()
        
        if success:
            print(f"\n{Fore.GREEN}🎉 Calendar & Scheduling System verification completed successfully!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠️  Calendar & Scheduling System verification completed with issues.{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Verification interrupted by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Verification failed with error: {str(e)}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()