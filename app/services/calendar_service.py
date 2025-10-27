"""
Calendar & Scheduling Service for SACEL Platform
Handles events, assignment due dates, exam schedules, and reminders
"""

from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_, desc, asc, func
from app.extensions import db
import json
import uuid
from enum import Enum
from typing import List, Dict, Optional, Tuple
import pytz
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY

class EventType(Enum):
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    CLASS = "class"
    MEETING = "meeting"
    HOLIDAY = "holiday"
    PERSONAL = "personal"
    SCHOOL_EVENT = "school_event"
    PARENT_MEETING = "parent_meeting"

class EventPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ReminderType(Enum):
    EMAIL = "email"
    NOTIFICATION = "notification"
    SMS = "sms"
    PUSH = "push"

class RecurrenceType(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

class CalendarService:
    """Service for handling all calendar and scheduling operations"""
    
    @staticmethod
    def create_event(creator_id: int, title: str, description: str = None,
                    start_datetime: datetime = None, end_datetime: datetime = None,
                    event_type: str = "personal", priority: str = "normal",
                    location: str = None, attendees: List[int] = None,
                    recurrence: Dict = None, reminders: List[Dict] = None,
                    metadata: Dict = None) -> Dict:
        """
        Create a new calendar event
        
        Args:
            creator_id: ID of the user creating the event
            title: Event title
            description: Event description
            start_datetime: Event start time
            end_datetime: Event end time
            event_type: Type of event
            priority: Event priority level
            location: Event location
            attendees: List of user IDs to invite
            recurrence: Recurrence settings
            reminders: List of reminder configurations
            metadata: Additional event metadata
            
        Returns:
            Dictionary with creation results
        """
        try:
            from app.models import User
            from app.models.calendar import Event, EventAttendee, EventReminder
            
            # Validate creator exists
            creator = User.query.get(creator_id)
            if not creator:
                return {"success": False, "error": "Creator not found"}
            
            # Validate datetime fields
            if start_datetime and end_datetime and start_datetime >= end_datetime:
                return {"success": False, "error": "Start time must be before end time"}
            
            # Create main event record
            event = Event(
                id=str(uuid.uuid4()),
                creator_id=creator_id,
                title=title,
                description=description,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                event_type=event_type,
                priority=priority,
                location=location,
                recurrence_rule=json.dumps(recurrence) if recurrence else None,
                event_metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(event)
            db.session.flush()  # Get the event ID
            
            # Add attendees
            if attendees:
                for attendee_id in attendees:
                    attendee = EventAttendee(
                        event_id=event.id,
                        user_id=attendee_id,
                        status='pending',
                        invited_at=datetime.utcnow()
                    )
                    db.session.add(attendee)
            
            # Add reminders
            if reminders:
                for reminder_config in reminders:
                    reminder = EventReminder(
                        event_id=event.id,
                        reminder_type=reminder_config.get('type', 'notification'),
                        minutes_before=reminder_config.get('minutes_before', 15),
                        is_active=True
                    )
                    db.session.add(reminder)
            
            # Handle recurring events
            if recurrence and recurrence.get('type') != 'none':
                CalendarService._create_recurring_events(event, recurrence)
            
            db.session.commit()
            
            # Send notifications for event creation
            if attendees:
                CalendarService._send_event_notifications(event, attendees, 'invited')
            
            return {
                "success": True,
                "event_id": event.id,
                "attendees_count": len(attendees) if attendees else 0,
                "created_at": event.created_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_calendar_events(user_id: int, start_date: date = None, 
                          end_date: date = None, event_types: List[str] = None,
                          include_assignments: bool = True) -> Dict:
        """
        Get calendar events for a user within a date range
        
        Args:
            user_id: ID of the user
            start_date: Start date for filtering
            end_date: End date for filtering
            event_types: Filter by event types
            include_assignments: Whether to include assignment due dates
            
        Returns:
            Dictionary with events
        """
        try:
            from app.models import User, Assignment
            from app.models.calendar import Event, EventAttendee
            
            # Set default date range if not provided
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today() + timedelta(days=90)
            
            # Convert dates to datetime for comparison
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            events = []
            
            # Get calendar events where user is creator or attendee
            event_query = db.session.query(Event).filter(
                and_(
                    Event.start_datetime >= start_datetime,
                    Event.start_datetime <= end_datetime,
                    or_(
                        Event.creator_id == user_id,
                        Event.id.in_(
                            db.session.query(EventAttendee.event_id).filter_by(user_id=user_id)
                        )
                    )
                )
            )
            
            # Filter by event types if specified
            if event_types:
                event_query = event_query.filter(Event.event_type.in_(event_types))
            
            calendar_events = event_query.all()
            
            for event in calendar_events:
                # Get attendee status for this user
                attendee_status = None
                if event.creator_id != user_id:
                    attendee = EventAttendee.query.filter_by(
                        event_id=event.id, user_id=user_id
                    ).first()
                    attendee_status = attendee.status if attendee else None
                
                event_data = {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_datetime": event.start_datetime.isoformat(),
                    "end_datetime": event.end_datetime.isoformat() if event.end_datetime else None,
                    "event_type": event.event_type,
                    "priority": event.priority,
                    "location": event.location,
                    "creator_id": event.creator_id,
                    "is_creator": event.creator_id == user_id,
                    "attendee_status": attendee_status,
                    "recurrence_rule": json.loads(event.recurrence_rule) if event.recurrence_rule else None,
                    "metadata": json.loads(event.event_metadata) if event.event_metadata else {}
                }
                events.append(event_data)
            
            # Include assignment due dates if requested
            if include_assignments:
                user = User.query.get(user_id)
                if user and user.role in ['student', 'teacher']:
                    assignment_events = CalendarService._get_assignment_events(
                        user_id, start_datetime, end_datetime, user.role
                    )
                    events.extend(assignment_events)
            
            # Sort events by start time
            events.sort(key=lambda x: x['start_datetime'])
            
            return {
                "success": True,
                "events": events,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_events": len(events)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def update_event(event_id: str, user_id: int, **kwargs) -> Dict:
        """Update an existing event"""
        try:
            from app.models.calendar import Event
            
            event = Event.query.filter_by(id=event_id).first()
            if not event:
                return {"success": False, "error": "Event not found"}
            
            # Check permissions
            if event.creator_id != user_id:
                return {"success": False, "error": "Permission denied"}
            
            # Update fields
            updatable_fields = [
                'title', 'description', 'start_datetime', 'end_datetime',
                'event_type', 'priority', 'location'
            ]
            
            for field in updatable_fields:
                if field in kwargs:
                    setattr(event, field, kwargs[field])
            
            event.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True,
                "event_id": event.id,
                "updated_at": event.updated_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def delete_event(event_id: str, user_id: int) -> Dict:
        """Delete an event"""
        try:
            from app.models.calendar import Event
            
            event = Event.query.filter_by(id=event_id).first()
            if not event:
                return {"success": False, "error": "Event not found"}
            
            # Check permissions
            if event.creator_id != user_id:
                return {"success": False, "error": "Permission denied"}
            
            db.session.delete(event)
            db.session.commit()
            
            return {"success": True, "message": "Event deleted successfully"}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def add_attendee(event_id: str, attendee_user_id: int, inviter_user_id: int) -> Dict:
        """Add an attendee to an event"""
        try:
            from app.models.calendar import Event, EventAttendee
            
            # Check if event exists and user has permission to invite
            event = Event.query.filter_by(id=event_id).first()
            if not event:
                return {"success": False, "error": "Event not found"}
            
            if event.creator_id != inviter_user_id:
                return {"success": False, "error": "Permission denied"}
            
            # Check if attendee is already invited
            existing_attendee = EventAttendee.query.filter_by(
                event_id=event_id,
                user_id=attendee_user_id
            ).first()
            
            if existing_attendee:
                return {"success": False, "error": "User already invited to this event"}
            
            # Create new attendee
            attendee = EventAttendee(
                id=str(uuid.uuid4()),
                event_id=event_id,
                user_id=attendee_user_id,
                status='pending',
                invited_at=datetime.utcnow()
            )
            
            db.session.add(attendee)
            db.session.commit()
            
            return {
                "success": True,
                "attendee_id": attendee.id,
                "status": attendee.status
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def respond_to_event(event_id: str, user_id: int, response: str) -> Dict:
        """Respond to an event invitation"""
        try:
            from app.models.calendar import EventAttendee
            
            attendee = EventAttendee.query.filter_by(
                event_id=event_id, user_id=user_id
            ).first()
            
            if not attendee:
                return {"success": False, "error": "Invitation not found"}
            
            valid_responses = ['accepted', 'declined', 'tentative']
            if response not in valid_responses:
                return {"success": False, "error": "Invalid response"}
            
            attendee.status = response
            attendee.responded_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                "success": True,
                "response": response,
                "responded_at": attendee.responded_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_upcoming_events(user_id: int, days_ahead: int = 7) -> Dict:
        """Get upcoming events for a user"""
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=days_ahead)
            
            result = CalendarService.get_calendar_events(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if result["success"]:
                # Filter to only future events
                now = datetime.now()
                upcoming_events = [
                    event for event in result["events"]
                    if datetime.fromisoformat(event["start_datetime"]) > now
                ]
                
                result["events"] = upcoming_events
                result["total_events"] = len(upcoming_events)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_reminder(event_id: str, reminder_type: str, 
                       minutes_before: int, user_id: int = None) -> Dict:
        """Create a reminder for an event"""
        try:
            from app.models.calendar import EventReminder
            
            reminder = EventReminder(
                id=str(uuid.uuid4()),
                event_id=event_id,
                user_id=user_id,
                reminder_type=reminder_type,
                minutes_before=minutes_before,
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            db.session.add(reminder)
            db.session.commit()
            
            return {
                "success": True,
                "reminder_id": reminder.id,
                "created_at": reminder.created_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_due_reminders() -> List[Dict]:
        """Get reminders that need to be sent"""
        try:
            from app.models.calendar import EventReminder, Event
            
            now = datetime.utcnow()
            
            # Find reminders for events starting within the reminder window
            due_reminders = db.session.query(EventReminder, Event).join(
                Event, EventReminder.event_id == Event.id
            ).filter(
                and_(
                    EventReminder.is_active == True,
                    EventReminder.sent_at.is_(None),
                    Event.start_datetime <= now + timedelta(minutes=EventReminder.minutes_before),
                    Event.start_datetime > now
                )
            ).all()
            
            reminders_data = []
            for reminder, event in due_reminders:
                reminder_data = {
                    "reminder_id": reminder.id,
                    "event_id": event.id,
                    "event_title": event.title,
                    "event_start": event.start_datetime.isoformat(),
                    "reminder_type": reminder.reminder_type,
                    "minutes_before": reminder.minutes_before,
                    "user_id": reminder.user_id or event.creator_id
                }
                reminders_data.append(reminder_data)
            
            return reminders_data
            
        except Exception as e:
            return []
    
    @staticmethod
    def mark_reminder_sent(reminder_id: str) -> bool:
        """Mark a reminder as sent"""
        try:
            from app.models.calendar import EventReminder
            
            reminder = EventReminder.query.get(reminder_id)
            if reminder:
                reminder.sent_at = datetime.utcnow()
                db.session.commit()
                return True
            return False
            
        except Exception as e:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_calendar_analytics(user_id: int = None, timeframe: str = "30d") -> Dict:
        """Get calendar usage analytics"""
        try:
            from app.models.calendar import Event, EventAttendee
            
            # Calculate date range
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(timeframe, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            analytics = {
                "timeframe": timeframe,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
            
            if user_id:
                # Personal analytics
                analytics.update({
                    "events_created": Event.query.filter(
                        and_(
                            Event.creator_id == user_id,
                            Event.created_at >= start_date
                        )
                    ).count(),
                    "events_attended": EventAttendee.query.filter(
                        and_(
                            EventAttendee.user_id == user_id,
                            EventAttendee.status == 'accepted',
                            EventAttendee.responded_at >= start_date
                        )
                    ).count(),
                    "invitations_received": EventAttendee.query.filter(
                        and_(
                            EventAttendee.user_id == user_id,
                            EventAttendee.invited_at >= start_date
                        )
                    ).count()
                })
            else:
                # System-wide analytics
                analytics.update({
                    "total_events": Event.query.filter(
                        Event.created_at >= start_date
                    ).count(),
                    "total_attendees": EventAttendee.query.filter(
                        EventAttendee.invited_at >= start_date
                    ).count(),
                    "acceptance_rate": CalendarService._calculate_acceptance_rate(start_date)
                })
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Helper methods
    @staticmethod
    def _create_recurring_events(base_event, recurrence_config):
        """Create recurring event instances"""
        # This would implement recurrence logic
        # For now, we'll create a simple implementation
        pass
    
    @staticmethod
    def _send_event_notifications(event, attendee_ids, notification_type):
        """Send notifications for event-related actions"""
        try:
            from app.services.communication_service import CommunicationService
            
            title = f"Event Invitation: {event.title}"
            message = f"You have been invited to '{event.title}' on {event.start_datetime.strftime('%Y-%m-%d %H:%M')}"
            
            if event.location:
                message += f" at {event.location}"
            
            CommunicationService.send_notification(
                user_ids=attendee_ids,
                title=title,
                message=message,
                category="academic"
            )
        except Exception as e:
            # Log error but don't fail the main operation
            pass
    
    @staticmethod
    def _get_assignment_events(user_id: int, start_datetime: datetime, 
                              end_datetime: datetime, user_role: str) -> List[Dict]:
        """Get assignment due dates as calendar events"""
        try:
            from app.models import Assignment, Submission, User
            
            assignment_events = []
            
            if user_role == 'student':
                # Get assignments assigned to this student (through their grade/subjects)
                assignments = Assignment.query.filter(
                    and_(
                        Assignment.due_date >= start_datetime,
                        Assignment.due_date <= end_datetime,
                        Assignment.is_active == True
                    )
                ).all()
                
                for assignment in assignments:
                    # Check if student has submitted
                    submission = Submission.query.filter_by(
                        assignment_id=assignment.id,
                        student_id=user_id
                    ).first()
                    
                    status = "submitted" if submission and submission.status == "submitted" else "pending"
                    
                    event_data = {
                        "id": f"assignment_{assignment.id}",
                        "title": f"Due: {assignment.title}",
                        "description": f"Assignment due for {assignment.subject}",
                        "start_datetime": assignment.due_date.isoformat(),
                        "end_datetime": assignment.due_date.isoformat(),
                        "event_type": "assignment",
                        "priority": "high" if assignment.due_date <= datetime.utcnow() + timedelta(days=1) else "normal",
                        "location": None,
                        "creator_id": assignment.teacher_id,
                        "is_creator": False,
                        "attendee_status": status,
                        "metadata": {
                            "assignment_id": assignment.id,
                            "subject": assignment.subject,
                            "max_score": assignment.max_score,
                            "submission_status": status
                        }
                    }
                    assignment_events.append(event_data)
            
            elif user_role == 'teacher':
                # Get assignments created by this teacher
                assignments = Assignment.query.filter(
                    and_(
                        Assignment.teacher_id == user_id,
                        Assignment.due_date >= start_datetime,
                        Assignment.due_date <= end_datetime,
                        Assignment.is_active == True
                    )
                ).all()
                
                for assignment in assignments:
                    # Count submissions
                    submission_count = Submission.query.filter_by(
                        assignment_id=assignment.id
                    ).count()
                    
                    event_data = {
                        "id": f"assignment_{assignment.id}",
                        "title": f"Assignment Due: {assignment.title}",
                        "description": f"Assignment due date for {assignment.subject}",
                        "start_datetime": assignment.due_date.isoformat(),
                        "end_datetime": assignment.due_date.isoformat(),
                        "event_type": "assignment",
                        "priority": "normal",
                        "location": None,
                        "creator_id": assignment.teacher_id,
                        "is_creator": True,
                        "attendee_status": None,
                        "metadata": {
                            "assignment_id": assignment.id,
                            "subject": assignment.subject,
                            "max_score": assignment.max_score,
                            "submission_count": submission_count
                        }
                    }
                    assignment_events.append(event_data)
            
            return assignment_events
            
        except Exception as e:
            return []
    
    @staticmethod
    def _calculate_acceptance_rate(start_date: datetime) -> float:
        """Calculate event invitation acceptance rate"""
        try:
            from app.models.calendar import EventAttendee
            
            total_invitations = EventAttendee.query.filter(
                EventAttendee.invited_at >= start_date
            ).count()
            
            if total_invitations == 0:
                return 0.0
            
            accepted_invitations = EventAttendee.query.filter(
                and_(
                    EventAttendee.invited_at >= start_date,
                    EventAttendee.status == 'accepted'
                )
            ).count()
            
            return round((accepted_invitations / total_invitations) * 100, 2)
            
        except Exception as e:
            return 0.0