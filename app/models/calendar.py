"""
Calendar Models for SACEL Platform
Database models for events, scheduling, and reminders
"""

from app.extensions import db
from datetime import datetime
import uuid


class Event(db.Model):
    """Model for calendar events"""
    __tablename__ = 'events'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime)
    event_type = db.Column(db.String(20), default='personal')  # assignment, exam, class, meeting, etc.
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    location = db.Column(db.String(200))
    is_all_day = db.Column(db.Boolean, default=False)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_rule = db.Column(db.Text)  # JSON string for recurrence settings
    parent_event_id = db.Column(db.String(36), db.ForeignKey('events.id'))  # For recurring events
    timezone = db.Column(db.String(50), default='UTC')
    status = db.Column(db.String(20), default='confirmed')  # confirmed, tentative, cancelled
    visibility = db.Column(db.String(20), default='public')  # public, private, shared
    event_metadata = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_events')
    parent_event = db.relationship('Event', remote_side=[id], backref='recurring_instances')
    attendees = db.relationship('EventAttendee', backref='event', cascade='all, delete-orphan')
    reminders = db.relationship('EventReminder', backref='event', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.id}: {self.title}>'


class EventAttendee(db.Model):
    """Model for event attendees and their responses"""
    __tablename__ = 'event_attendees'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(36), db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, tentative
    role = db.Column(db.String(20), default='attendee')  # organizer, attendee, optional
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)  # Attendee-specific notes
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='event_attendances')
    
    # Unique constraint to prevent duplicate attendees
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id', name='unique_event_attendee'),)
    
    def __repr__(self):
        return f'<EventAttendee {self.event_id} -> {self.user_id}>'


class EventReminder(db.Model):
    """Model for event reminders"""
    __tablename__ = 'event_reminders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = db.Column(db.String(36), db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Specific user, null for all attendees
    reminder_type = db.Column(db.String(20), default='notification')  # email, notification, sms, push
    minutes_before = db.Column(db.Integer, default=15)  # Minutes before event to remind
    is_active = db.Column(db.Boolean, default=True)
    sent_at = db.Column(db.DateTime)  # When the reminder was sent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='event_reminders')
    
    def __repr__(self):
        return f'<EventReminder {self.id} for {self.event_id}>'


class Calendar(db.Model):
    """Model for user calendars (allowing multiple calendars per user)"""
    __tablename__ = 'calendars'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color code
    is_primary = db.Column(db.Boolean, default=False)
    is_visible = db.Column(db.Boolean, default=True)
    is_shared = db.Column(db.Boolean, default=False)
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = db.relationship('User', foreign_keys=[user_id], backref='calendars')
    shared_with = db.relationship('CalendarShare', backref='calendar', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Calendar {self.id}: {self.name}>'


class CalendarShare(db.Model):
    """Model for calendar sharing permissions"""
    __tablename__ = 'calendar_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.String(36), db.ForeignKey('calendars.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='read')  # read, write, admin
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='shared_calendars')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('calendar_id', 'user_id', name='unique_calendar_share'),)
    
    def __repr__(self):
        return f'<CalendarShare {self.calendar_id} -> {self.user_id}>'


class Holiday(db.Model):
    """Model for holidays and special dates"""
    __tablename__ = 'holidays'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    holiday_type = db.Column(db.String(20), default='public')  # public, school, religious, etc.
    country = db.Column(db.String(2), default='ZA')  # ISO country code
    province = db.Column(db.String(50))  # For regional holidays
    is_recurring = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Holiday {self.name} on {self.date}>'


class Schedule(db.Model):
    """Model for class schedules and timetables"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Grade 10 Mathematics"
    subject = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room = db.Column(db.String(50))
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    term_start = db.Column(db.Date)
    term_end = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    recurring_weeks = db.Column(db.Text)  # JSON array of week numbers (for alternating schedules)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='schedules')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='teaching_schedules')
    
    def __repr__(self):
        return f'<Schedule {self.name} - {self.subject}>'


class ExamSchedule(db.Model):
    """Model for exam schedules"""
    __tablename__ = 'exam_schedules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Term 1 Mathematics Exam"
    subject = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.Integer, nullable=False)
    exam_type = db.Column(db.String(50), default='test')  # test, exam, assessment, practical
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room = db.Column(db.String(50))
    exam_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, default=100)
    instructions = db.Column(db.Text)
    materials_allowed = db.Column(db.Text)  # JSON list of allowed materials
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    school = db.relationship('School', backref='exam_schedules')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='exam_schedules')
    
    def __repr__(self):
        return f'<ExamSchedule {self.name} on {self.exam_date}>'


class TimeSlot(db.Model):
    """Model for time slots in school schedules"""
    __tablename__ = 'time_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    slot_name = db.Column(db.String(50), nullable=False)  # e.g., "Period 1", "Break", "Lunch"
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_type = db.Column(db.String(20), default='class')  # class, break, lunch, assembly
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    school = db.relationship('School', backref='time_slots')
    
    def __repr__(self):
        return f'<TimeSlot {self.slot_name}: {self.start_time}-{self.end_time}>'


class AvailabilitySlot(db.Model):
    """Model for user availability (for scheduling meetings, etc.)"""
    __tablename__ = 'availability_slots'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    recurring = db.Column(db.Boolean, default=True)  # Weekly recurring
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='availability_slots')
    
    def __repr__(self):
        return f'<AvailabilitySlot {self.user_id}: Day {self.day_of_week}>'