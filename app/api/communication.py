"""
Communication API endpoints for SACEL Platform
Handles messaging, forums, notifications, and announcements
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.communication_service import CommunicationService
from app.extensions import db
from datetime import datetime
import json

communication_bp = Blueprint('communication', __name__, url_prefix='/api/communication')


@communication_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a message to recipients"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipient_ids', 'subject', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False, 
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Extract data
        recipient_ids = data['recipient_ids']
        subject = data['subject']
        content = data['content']
        message_type = data.get('message_type', 'personal')
        priority = data.get('priority', 'normal')
        attachments = data.get('attachments', [])
        
        # Validate recipient_ids is a list
        if not isinstance(recipient_ids, list) or len(recipient_ids) == 0:
            return jsonify({
                "success": False,
                "error": "recipient_ids must be a non-empty list"
            }), 400
        
        # Send message
        result = CommunicationService.send_message(
            sender_id=current_user.id,
            recipient_ids=recipient_ids,
            subject=subject,
            content=content,
            message_type=message_type,
            priority=priority,
            attachments=attachments
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


@communication_bp.route('/messages', methods=['GET'])
@login_required
def get_messages():
    """Get messages for current user"""
    try:
        folder = request.args.get('folder', 'inbox')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Validate folder
        valid_folders = ['inbox', 'sent', 'drafts', 'archived']
        if folder not in valid_folders:
            return jsonify({
                "success": False,
                "error": f"Invalid folder. Must be one of: {valid_folders}"
            }), 400
        
        result = CommunicationService.get_user_messages(
            user_id=current_user.id,
            folder=folder,
            page=page,
            per_page=per_page
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


@communication_bp.route('/messages/<message_id>/read', methods=['POST'])
@login_required
def mark_message_read(message_id):
    """Mark a message as read"""
    try:
        result = CommunicationService.mark_message_read(
            user_id=current_user.id,
            message_id=message_id
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


@communication_bp.route('/announcements/create', methods=['POST'])
@login_required
def create_announcement():
    """Create a system announcement (admin/teacher only)"""
    try:
        # Check permissions
        if current_user.role not in ['admin', 'teacher']:
            return jsonify({
                "success": False,
                "error": "Insufficient permissions"
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'content', 'target_audience']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        title = data['title']
        content = data['content']
        target_audience = data['target_audience']
        priority = data.get('priority', 'normal')
        expiry_date = None
        
        if 'expiry_date' in data:
            try:
                expiry_date = datetime.fromisoformat(data['expiry_date'])
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid expiry_date format"
                }), 400
        
        result = CommunicationService.create_announcement(
            creator_id=current_user.id,
            title=title,
            content=content,
            target_audience=target_audience,
            priority=priority,
            expiry_date=expiry_date
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


@communication_bp.route('/forum/posts', methods=['GET'])
@login_required
def get_forum_posts():
    """Get forum posts with filtering and pagination"""
    try:
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_by = request.args.get('sort_by', 'latest')
        
        # Validate sort_by
        valid_sorts = ['latest', 'popular', 'most_viewed']
        if sort_by not in valid_sorts:
            return jsonify({
                "success": False,
                "error": f"Invalid sort_by. Must be one of: {valid_sorts}"
            }), 400
        
        result = CommunicationService.get_forum_posts(
            category=category,
            page=page,
            per_page=per_page,
            sort_by=sort_by
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


@communication_bp.route('/forum/posts/create', methods=['POST'])
@login_required
def create_forum_post():
    """Create a new forum post"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category', 'title', 'content']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        category = data['category']
        title = data['title']
        content = data['content']
        tags = data.get('tags', [])
        
        result = CommunicationService.create_forum_post(
            user_id=current_user.id,
            category=category,
            title=title,
            content=content,
            tags=tags
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


@communication_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get notifications for current user"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        result = CommunicationService.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            page=page,
            per_page=per_page
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


@communication_bp.route('/notifications/send', methods=['POST'])
@login_required
def send_notification():
    """Send notifications to users (admin/teacher only)"""
    try:
        # Check permissions
        if current_user.role not in ['admin', 'teacher']:
            return jsonify({
                "success": False,
                "error": "Insufficient permissions"
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_ids', 'title', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        user_ids = data['user_ids']
        title = data['title']
        message = data['message']
        category = data.get('category', 'general')
        action_url = data.get('action_url')
        
        # Validate user_ids is a list
        if not isinstance(user_ids, list) or len(user_ids) == 0:
            return jsonify({
                "success": False,
                "error": "user_ids must be a non-empty list"
            }), 400
        
        result = CommunicationService.send_notification(
            user_ids=user_ids,
            title=title,
            message=message,
            category=category,
            action_url=action_url
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


@communication_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        from app.models.communication import Notification
        
        notification = Notification.query.filter_by(
            id=notification_id, user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({
                "success": False,
                "error": "Notification not found"
            }), 404
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            "success": True,
            "read_at": notification.read_at.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@communication_bp.route('/analytics', methods=['GET'])
@login_required
def get_communication_analytics():
    """Get communication analytics"""
    try:
        timeframe = request.args.get('timeframe', '30d')
        user_id = None
        
        # For personal analytics, use current user ID
        # For system analytics, only allow admin users
        if request.args.get('scope') == 'personal':
            user_id = current_user.id
        elif current_user.role == 'admin':
            user_id = None  # System-wide analytics
        else:
            user_id = current_user.id  # Default to personal for non-admin
        
        # Validate timeframe
        valid_timeframes = ['7d', '30d', '90d', '1y']
        if timeframe not in valid_timeframes:
            return jsonify({
                "success": False,
                "error": f"Invalid timeframe. Must be one of: {valid_timeframes}"
            }), 400
        
        result = CommunicationService.get_communication_analytics(
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


@communication_bp.route('/users/search', methods=['GET'])
@login_required
def search_users():
    """Search for users to send messages to"""
    try:
        query = request.args.get('q', '').strip()
        role = request.args.get('role')
        limit = int(request.args.get('limit', 10))
        
        if len(query) < 2:
            return jsonify({
                "success": False,
                "error": "Search query must be at least 2 characters"
            }), 400
        
        from app.models import User
        from sqlalchemy import or_
        
        # Build search query
        search_query = User.query.filter(
            or_(
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        )
        
        # Filter by role if specified
        if role:
            search_query = search_query.filter_by(role=role)
        
        # Exclude current user from results
        search_query = search_query.filter(User.id != current_user.id)
        
        # Limit results
        users = search_query.limit(limit).all()
        
        # Format results
        user_list = []
        for user in users:
            user_data = {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email,
                "role": user.role
            }
            user_list.append(user_data)
        
        return jsonify({
            "success": True,
            "users": user_list,
            "count": len(user_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@communication_bp.route('/stats/overview', methods=['GET'])
@login_required
def get_communication_overview():
    """Get communication overview stats for current user"""
    try:
        from app.models.communication import MessageRecipient, Notification
        from sqlalchemy import func
        
        # Get unread message count
        unread_messages = MessageRecipient.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).count()
        
        # Get unread notification count
        unread_notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).count()
        
        # Get total messages in last 30 days
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_messages = MessageRecipient.query.filter(
            MessageRecipient.recipient_id == current_user.id,
            MessageRecipient.received_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            "success": True,
            "stats": {
                "unread_messages": unread_messages,
                "unread_notifications": unread_notifications,
                "recent_messages_30d": recent_messages,
                "last_updated": datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500