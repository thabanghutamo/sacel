"""
Calendar API endpoints for SACEL Platform
Handles events, scheduling, and reminders
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.calendar_service import CalendarService
from app.extensions import db
from datetime import datetime, date
import json

calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')


@calendar_bp.route('/events/create', methods=['POST'])
@login_required
def create_event():
    """Create a new calendar event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'start_datetime']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Parse datetime fields
        try:
            start_datetime = datetime.fromisoformat(data['start_datetime'])
            end_datetime = None
            if data.get('end_datetime'):
                end_datetime = datetime.fromisoformat(data['end_datetime'])
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Invalid datetime format"
            }), 400
        
        result = CalendarService.create_event(
            creator_id=current_user.id,
            title=data['title'],
            description=data.get('description'),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            event_type=data.get('event_type', 'personal'),
            priority=data.get('priority', 'normal'),
            location=data.get('location'),
            attendees=data.get('attendees', []),
            recurrence=data.get('recurrence'),
            reminders=data.get('reminders', []),
            metadata=data.get('metadata')
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/events', methods=['GET'])
@login_required
def get_events():
    """Get calendar events for the current user"""
    try:
        # Parse query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        event_types = request.args.getlist('event_types')
        include_assignments = request.args.get('include_assignments', 'true').lower() == 'true'
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid start_date format"
                }), 400
        
        if end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid end_date format"
                }), 400
        
        result = CalendarService.get_calendar_events(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types if event_types else None,
            include_assignments=include_assignments
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/events/<event_id>', methods=['PUT'])
@login_required
def update_event(event_id):
    """Update an existing event"""
    try:
        data = request.get_json()
        
        # Parse datetime fields if provided
        update_data = {}
        for field in ['title', 'description', 'location', 'event_type', 'priority']:
            if field in data:
                update_data[field] = data[field]
        
        if 'start_datetime' in data:
            try:
                update_data['start_datetime'] = datetime.fromisoformat(data['start_datetime'])
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid start_datetime format"
                }), 400
        
        if 'end_datetime' in data:
            try:
                update_data['end_datetime'] = datetime.fromisoformat(data['end_datetime'])
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid end_datetime format"
                }), 400
        
        result = CalendarService.update_event(
            event_id=event_id,
            user_id=current_user.id,
            **update_data
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400 if "Permission denied" in result.get("error", "") else 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/events/<event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    """Delete an event"""
    try:
        result = CalendarService.delete_event(
            event_id=event_id,
            user_id=current_user.id
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400 if "Permission denied" in result.get("error", "") else 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/events/<event_id>/respond', methods=['POST'])
@login_required
def respond_to_event(event_id):
    """Respond to an event invitation"""
    try:
        data = request.get_json()
        
        if 'response' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required field: response"
            }), 400
        
        result = CalendarService.respond_to_event(
            event_id=event_id,
            user_id=current_user.id,
            response=data['response']
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/events/upcoming', methods=['GET'])
@login_required
def get_upcoming_events():
    """Get upcoming events for the current user"""
    try:
        days_ahead = int(request.args.get('days', 7))
        
        if days_ahead < 1 or days_ahead > 365:
            return jsonify({
                "success": False,
                "error": "Days ahead must be between 1 and 365"
            }), 400
        
        result = CalendarService.get_upcoming_events(
            user_id=current_user.id,
            days_ahead=days_ahead
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/reminders/create', methods=['POST'])
@login_required
def create_reminder():
    """Create a reminder for an event"""
    try:
        data = request.get_json()
        
        required_fields = ['event_id', 'reminder_type', 'minutes_before']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        result = CalendarService.create_reminder(
            event_id=data['event_id'],
            reminder_type=data['reminder_type'],
            minutes_before=data['minutes_before'],
            user_id=current_user.id
        )
        
        if result["success"]:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/analytics', methods=['GET'])
@login_required
def get_calendar_analytics():
    """Get calendar usage analytics"""
    try:
        timeframe = request.args.get('timeframe', '30d')
        scope = request.args.get('scope', 'personal')
        
        # Validate timeframe
        valid_timeframes = ['7d', '30d', '90d', '1y']
        if timeframe not in valid_timeframes:
            return jsonify({
                "success": False,
                "error": f"Invalid timeframe. Must be one of: {valid_timeframes}"
            }), 400
        
        # Determine user_id based on scope and permissions
        user_id = current_user.id
        if scope == 'system' and current_user.role == 'admin':
            user_id = None
        
        result = CalendarService.get_calendar_analytics(
            user_id=user_id,
            timeframe=timeframe
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/schedules/class', methods=['GET'])
@login_required
def get_class_schedule():
    """Get class schedule for current user"""
    try:
        from app.models.calendar import Schedule
        from app.models import User
        
        # Get week parameter (0 = current week)
        week_offset = int(request.args.get('week', 0))
        
        schedules = []
        
        if current_user.role == 'teacher':
            # Get teaching schedule
            teaching_schedules = Schedule.query.filter_by(
                teacher_id=current_user.id,
                is_active=True
            ).all()
            
            for schedule in teaching_schedules:
                schedule_data = {
                    "id": schedule.id,
                    "name": schedule.name,
                    "subject": schedule.subject,
                    "grade_level": schedule.grade_level,
                    "room": schedule.room,
                    "day_of_week": schedule.day_of_week,
                    "start_time": schedule.start_time.strftime('%H:%M'),
                    "end_time": schedule.end_time.strftime('%H:%M'),
                    "type": "teaching"
                }
                schedules.append(schedule_data)
        
        elif current_user.role == 'student':
            # Get student's class schedule based on grade
            student_profile = current_user.student_profile
            if student_profile:
                class_schedules = Schedule.query.filter_by(
                    grade_level=student_profile.grade,
                    is_active=True
                ).all()
                
                for schedule in class_schedules:
                    # Check if student is enrolled in this subject
                    student_subjects = json.loads(student_profile.subjects or '[]')
                    if schedule.subject in student_subjects:
                        schedule_data = {
                            "id": schedule.id,
                            "name": schedule.name,
                            "subject": schedule.subject,
                            "teacher": schedule.teacher.full_name,
                            "room": schedule.room,
                            "day_of_week": schedule.day_of_week,
                            "start_time": schedule.start_time.strftime('%H:%M'),
                            "end_time": schedule.end_time.strftime('%H:%M'),
                            "type": "class"
                        }
                        schedules.append(schedule_data)
        
        return jsonify({
            "success": True,
            "schedules": schedules,
            "week_offset": week_offset
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/schedules/exam', methods=['GET'])
@login_required
def get_exam_schedule():
    """Get exam schedule for current user"""
    try:
        from app.models.calendar import ExamSchedule
        from datetime import timedelta
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Default to next 30 days if no range specified
        if not start_date_str:
            start_date = date.today()
        else:
            start_date = date.fromisoformat(start_date_str)
        
        if not end_date_str:
            end_date = start_date + timedelta(days=30)
        else:
            end_date = date.fromisoformat(end_date_str)
        
        exams = []
        
        if current_user.role == 'teacher':
            # Get exams created by this teacher
            teacher_exams = ExamSchedule.query.filter(
                ExamSchedule.teacher_id == current_user.id,
                ExamSchedule.exam_date >= start_date,
                ExamSchedule.exam_date <= end_date,
                ExamSchedule.is_published == True
            ).all()
            
            for exam in teacher_exams:
                exam_data = {
                    "id": exam.id,
                    "name": exam.name,
                    "subject": exam.subject,
                    "grade_level": exam.grade_level,
                    "exam_type": exam.exam_type,
                    "room": exam.room,
                    "exam_date": exam.exam_date.isoformat(),
                    "start_time": exam.start_time.strftime('%H:%M'),
                    "end_time": exam.end_time.strftime('%H:%M'),
                    "duration_minutes": exam.duration_minutes,
                    "max_marks": exam.max_marks,
                    "is_creator": True
                }
                exams.append(exam_data)
        
        elif current_user.role == 'student':
            # Get exams for student's grade and subjects
            student_profile = current_user.student_profile
            if student_profile:
                student_subjects = json.loads(student_profile.subjects or '[]')
                
                student_exams = ExamSchedule.query.filter(
                    ExamSchedule.grade_level == student_profile.grade,
                    ExamSchedule.subject.in_(student_subjects),
                    ExamSchedule.exam_date >= start_date,
                    ExamSchedule.exam_date <= end_date,
                    ExamSchedule.is_published == True
                ).all()
                
                for exam in student_exams:
                    exam_data = {
                        "id": exam.id,
                        "name": exam.name,
                        "subject": exam.subject,
                        "exam_type": exam.exam_type,
                        "room": exam.room,
                        "exam_date": exam.exam_date.isoformat(),
                        "start_time": exam.start_time.strftime('%H:%M'),
                        "end_time": exam.end_time.strftime('%H:%M'),
                        "duration_minutes": exam.duration_minutes,
                        "max_marks": exam.max_marks,
                        "teacher": exam.teacher.full_name,
                        "is_creator": False
                    }
                    exams.append(exam_data)
        
        return jsonify({
            "success": True,
            "exams": exams,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/holidays', methods=['GET'])
@login_required
def get_holidays():
    """Get holidays for the calendar"""
    try:
        from app.models.calendar import Holiday
        
        year = int(request.args.get('year', date.today().year))
        country = request.args.get('country', 'ZA')
        
        holidays = Holiday.query.filter(
            Holiday.date >= date(year, 1, 1),
            Holiday.date <= date(year, 12, 31),
            Holiday.country == country,
            Holiday.is_active == True
        ).all()
        
        holidays_data = []
        for holiday in holidays:
            holiday_data = {
                "id": holiday.id,
                "name": holiday.name,
                "date": holiday.date.isoformat(),
                "description": holiday.description,
                "holiday_type": holiday.holiday_type,
                "province": holiday.province
            }
            holidays_data.append(holiday_data)
        
        return jsonify({
            "success": True,
            "holidays": holidays_data,
            "year": year,
            "country": country
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/availability', methods=['GET'])
@login_required
def get_availability():
    """Get user availability"""
    try:
        from app.models.calendar import AvailabilitySlot
        
        availability_slots = AvailabilitySlot.query.filter_by(
            user_id=current_user.id
        ).all()
        
        availability_data = []
        for slot in availability_slots:
            slot_data = {
                "id": slot.id,
                "day_of_week": slot.day_of_week,
                "start_time": slot.start_time.strftime('%H:%M'),
                "end_time": slot.end_time.strftime('%H:%M'),
                "is_available": slot.is_available,
                "recurring": slot.recurring,
                "notes": slot.notes
            }
            availability_data.append(slot_data)
        
        return jsonify({
            "success": True,
            "availability": availability_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@calendar_bp.route('/availability', methods=['POST'])
@login_required
def set_availability():
    """Set user availability"""
    try:
        from app.models.calendar import AvailabilitySlot
        from datetime import time
        
        data = request.get_json()
        
        required_fields = ['day_of_week', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Parse time fields
        try:
            start_time = time.fromisoformat(data['start_time'])
            end_time = time.fromisoformat(data['end_time'])
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Invalid time format"
            }), 400
        
        availability_slot = AvailabilitySlot(
            user_id=current_user.id,
            day_of_week=data['day_of_week'],
            start_time=start_time,
            end_time=end_time,
            is_available=data.get('is_available', True),
            recurring=data.get('recurring', True),
            notes=data.get('notes')
        )
        
        db.session.add(availability_slot)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "availability_id": availability_slot.id,
            "created_at": availability_slot.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500