"""
Communication Service for SACEL Platform
Handles messaging, announcements, notifications, and discussion forums
"""

from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc, asc, func
from app.extensions import db
import json
import uuid
from enum import Enum
from typing import List, Dict, Optional, Tuple

class MessageType(Enum):
    PERSONAL = "personal"
    ANNOUNCEMENT = "announcement"
    FORUM_POST = "forum_post"
    NOTIFICATION = "notification"
    SYSTEM = "system"

class MessagePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationCategory(Enum):
    ACADEMIC = "academic"
    ADMINISTRATIVE = "administrative"
    SOCIAL = "social"
    TECHNICAL = "technical"
    EMERGENCY = "emergency"

class CommunicationService:
    """Service for handling all communication-related operations"""
    
    @staticmethod
    def send_message(sender_id: int, recipient_ids: List[int], subject: str, 
                    content: str, message_type: str = "personal", 
                    priority: str = "normal", attachments: List[Dict] = None) -> Dict:
        """
        Send a message to one or multiple recipients
        
        Args:
            sender_id: ID of the user sending the message
            recipient_ids: List of user IDs to receive the message
            subject: Message subject line
            content: Message content/body
            message_type: Type of message (personal, announcement, etc.)
            priority: Priority level (low, normal, high, urgent)
            attachments: List of attachment dictionaries
            
        Returns:
            Dictionary with message creation results
        """
        try:
            # Import here to avoid circular imports
            from app.models import User, Message, MessageRecipient
            
            # Validate sender exists
            sender = User.query.get(sender_id)
            if not sender:
                return {"success": False, "error": "Sender not found"}
            
            # Validate recipients exist
            recipients = User.query.filter(User.id.in_(recipient_ids)).all()
            if len(recipients) != len(recipient_ids):
                return {"success": False, "error": "One or more recipients not found"}
            
            # Create main message record
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                subject=subject,
                content=content,
                message_type=message_type,
                priority=priority,
                attachments=json.dumps(attachments) if attachments else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(message)
            db.session.flush()  # Get the message ID
            
            # Create recipient records
            message_recipients = []
            for recipient in recipients:
                recipient_record = MessageRecipient(
                    message_id=message.id,
                    recipient_id=recipient.id,
                    is_read=False,
                    received_at=datetime.utcnow()
                )
                message_recipients.append(recipient_record)
                db.session.add(recipient_record)
            
            db.session.commit()
            
            # Send notifications for high priority messages
            if priority in ['high', 'urgent']:
                CommunicationService._send_priority_notifications(
                    message, recipients, sender
                )
            
            return {
                "success": True,
                "message_id": message.id,
                "recipients_count": len(recipients),
                "sent_at": message.created_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_messages(user_id: int, folder: str = "inbox", 
                         page: int = 1, per_page: int = 20) -> Dict:
        """
        Get messages for a specific user
        
        Args:
            user_id: ID of the user
            folder: Message folder (inbox, sent, drafts, archived)
            page: Page number for pagination
            per_page: Messages per page
            
        Returns:
            Dictionary with messages and pagination info
        """
        try:
            from app.models import Message, MessageRecipient, User
            
            if folder == "sent":
                # Get sent messages
                query = Message.query.filter_by(sender_id=user_id)
            elif folder == "drafts":
                # Get draft messages (not implemented in this version)
                query = Message.query.filter_by(sender_id=user_id, is_draft=True)
            elif folder == "archived":
                # Get archived messages
                query = (db.session.query(Message)
                        .join(MessageRecipient)
                        .filter(and_(
                            MessageRecipient.recipient_id == user_id,
                            MessageRecipient.is_archived == True
                        )))
            else:  # inbox
                # Get received messages
                query = (db.session.query(Message)
                        .join(MessageRecipient)
                        .filter(and_(
                            MessageRecipient.recipient_id == user_id,
                            MessageRecipient.is_archived != True
                        )))
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Message.created_at))
            
            # Paginate results
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            messages = []
            for message in paginated.items:
                # Get sender info
                sender = User.query.get(message.sender_id)
                
                # Get recipient info for this user
                if folder != "sent":
                    recipient_info = MessageRecipient.query.filter_by(
                        message_id=message.id, recipient_id=user_id
                    ).first()
                else:
                    recipient_info = None
                
                message_data = {
                    "id": message.id,
                    "subject": message.subject,
                    "content": message.content,
                    "message_type": message.message_type,
                    "priority": message.priority,
                    "sender": {
                        "id": sender.id,
                        "name": f"{sender.first_name} {sender.last_name}",
                        "role": sender.role
                    } if sender else None,
                    "created_at": message.created_at.isoformat(),
                    "is_read": recipient_info.is_read if recipient_info else True,
                    "read_at": recipient_info.read_at.isoformat() if recipient_info and recipient_info.read_at else None,
                    "attachments": json.loads(message.attachments) if message.attachments else []
                }
                messages.append(message_data)
            
            return {
                "success": True,
                "messages": messages,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": paginated.total,
                    "pages": paginated.pages,
                    "has_next": paginated.has_next,
                    "has_prev": paginated.has_prev
                },
                "unread_count": CommunicationService._get_unread_count(user_id)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def mark_message_read(user_id: int, message_id: str) -> Dict:
        """Mark a message as read for a specific user"""
        try:
            from app.models import MessageRecipient
            
            recipient = MessageRecipient.query.filter_by(
                message_id=message_id, recipient_id=user_id
            ).first()
            
            if not recipient:
                return {"success": False, "error": "Message not found"}
            
            if not recipient.is_read:
                recipient.is_read = True
                recipient.read_at = datetime.utcnow()
                db.session.commit()
            
            return {"success": True, "read_at": recipient.read_at.isoformat()}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_announcement(creator_id: int, title: str, content: str,
                          target_audience: List[str], priority: str = "normal",
                          expiry_date: datetime = None) -> Dict:
        """
        Create a system-wide announcement
        
        Args:
            creator_id: ID of the user creating the announcement
            title: Announcement title
            content: Announcement content
            target_audience: List of roles or groups to target
            priority: Priority level
            expiry_date: When the announcement expires
            
        Returns:
            Dictionary with creation results
        """
        try:
            from app.models import User
            
            # Get users based on target audience
            if "all" in target_audience:
                recipients = User.query.all()
            else:
                recipients = User.query.filter(User.role.in_(target_audience)).all()
            
            recipient_ids = [user.id for user in recipients]
            
            # Send as announcement message
            result = CommunicationService.send_message(
                sender_id=creator_id,
                recipient_ids=recipient_ids,
                subject=title,
                content=content,
                message_type="announcement",
                priority=priority
            )
            
            if result["success"]:
                # Store announcement metadata
                announcement_data = {
                    "message_id": result["message_id"],
                    "target_audience": target_audience,
                    "expiry_date": expiry_date.isoformat() if expiry_date else None,
                    "created_at": result["sent_at"]
                }
                
                # Could store in separate announcements table for better tracking
                result["announcement_data"] = announcement_data
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_forum_post(user_id: int, category: str, title: str, 
                         content: str, tags: List[str] = None) -> Dict:
        """
        Create a new forum post
        
        Args:
            user_id: ID of the user creating the post
            category: Forum category
            title: Post title
            content: Post content
            tags: List of tags for the post
            
        Returns:
            Dictionary with creation results
        """
        try:
            from app.models import ForumPost, User
            
            # Validate user exists
            user = User.query.get(user_id)
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Create forum post
            post = ForumPost(
                id=str(uuid.uuid4()),
                user_id=user_id,
                category=category,
                title=title,
                content=content,
                tags=json.dumps(tags) if tags else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                views=0,
                likes=0
            )
            
            db.session.add(post)
            db.session.commit()
            
            return {
                "success": True,
                "post_id": post.id,
                "created_at": post.created_at.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_forum_posts(category: str = None, page: int = 1, 
                       per_page: int = 20, sort_by: str = "latest") -> Dict:
        """
        Get forum posts with pagination and filtering
        
        Args:
            category: Filter by category (optional)
            page: Page number
            per_page: Posts per page
            sort_by: Sort order (latest, popular, most_viewed)
            
        Returns:
            Dictionary with posts and pagination info
        """
        try:
            from app.models import ForumPost, User
            
            # Build query
            query = ForumPost.query
            
            if category:
                query = query.filter_by(category=category)
            
            # Apply sorting
            if sort_by == "popular":
                query = query.order_by(desc(ForumPost.likes))
            elif sort_by == "most_viewed":
                query = query.order_by(desc(ForumPost.views))
            else:  # latest
                query = query.order_by(desc(ForumPost.created_at))
            
            # Paginate
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            posts = []
            for post in paginated.items:
                author = User.query.get(post.user_id)
                
                post_data = {
                    "id": post.id,
                    "title": post.title,
                    "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                    "category": post.category,
                    "tags": json.loads(post.tags) if post.tags else [],
                    "author": {
                        "id": author.id,
                        "name": f"{author.first_name} {author.last_name}",
                        "role": author.role
                    } if author else None,
                    "created_at": post.created_at.isoformat(),
                    "updated_at": post.updated_at.isoformat(),
                    "views": post.views,
                    "likes": post.likes,
                    "replies_count": CommunicationService._get_replies_count(post.id)
                }
                posts.append(post_data)
            
            return {
                "success": True,
                "posts": posts,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": paginated.total,
                    "pages": paginated.pages,
                    "has_next": paginated.has_next,
                    "has_prev": paginated.has_prev
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def send_notification(user_ids: List[int], title: str, message: str,
                         category: str = "general", action_url: str = None) -> Dict:
        """
        Send notifications to users
        
        Args:
            user_ids: List of user IDs to notify
            title: Notification title
            message: Notification message
            category: Notification category
            action_url: URL for action button (optional)
            
        Returns:
            Dictionary with notification results
        """
        try:
            from app.models import Notification
            
            notifications = []
            for user_id in user_ids:
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    title=title,
                    message=message,
                    category=category,
                    action_url=action_url,
                    is_read=False,
                    created_at=datetime.utcnow()
                )
                notifications.append(notification)
                db.session.add(notification)
            
            db.session.commit()
            
            return {
                "success": True,
                "notifications_sent": len(notifications),
                "sent_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_notifications(user_id: int, unread_only: bool = False,
                              page: int = 1, per_page: int = 20) -> Dict:
        """Get notifications for a user"""
        try:
            from app.models import Notification
            
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            query = query.order_by(desc(Notification.created_at))
            
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            notifications = []
            for notification in paginated.items:
                notification_data = {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "category": notification.category,
                    "action_url": notification.action_url,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat(),
                    "read_at": notification.read_at.isoformat() if notification.read_at else None
                }
                notifications.append(notification_data)
            
            return {
                "success": True,
                "notifications": notifications,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": paginated.total,
                    "pages": paginated.pages
                },
                "unread_count": Notification.query.filter_by(
                    user_id=user_id, is_read=False
                ).count()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_communication_analytics(user_id: int = None, 
                                  timeframe: str = "30d") -> Dict:
        """
        Get communication analytics
        
        Args:
            user_id: Specific user ID for personal analytics (optional)
            timeframe: Time period (7d, 30d, 90d, 1y)
            
        Returns:
            Dictionary with analytics data
        """
        try:
            from app.models import Message, MessageRecipient, ForumPost, Notification
            
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
                    "messages_sent": Message.query.filter(
                        and_(
                            Message.sender_id == user_id,
                            Message.created_at >= start_date
                        )
                    ).count(),
                    "messages_received": MessageRecipient.query.filter(
                        and_(
                            MessageRecipient.recipient_id == user_id,
                            MessageRecipient.received_at >= start_date
                        )
                    ).count(),
                    "forum_posts": ForumPost.query.filter(
                        and_(
                            ForumPost.user_id == user_id,
                            ForumPost.created_at >= start_date
                        )
                    ).count(),
                    "notifications_received": Notification.query.filter(
                        and_(
                            Notification.user_id == user_id,
                            Notification.created_at >= start_date
                        )
                    ).count()
                })
            else:
                # System-wide analytics
                analytics.update({
                    "total_messages": Message.query.filter(
                        Message.created_at >= start_date
                    ).count(),
                    "total_forum_posts": ForumPost.query.filter(
                        ForumPost.created_at >= start_date
                    ).count(),
                    "total_notifications": Notification.query.filter(
                        Notification.created_at >= start_date
                    ).count(),
                    "active_users": db.session.query(Message.sender_id).filter(
                        Message.created_at >= start_date
                    ).distinct().count()
                })
            
            return {"success": True, "analytics": analytics}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Helper methods
    @staticmethod
    def _send_priority_notifications(message, recipients, sender):
        """Send notifications for high priority messages"""
        notification_title = f"High Priority Message from {sender.first_name} {sender.last_name}"
        notification_message = f"Subject: {message.subject}"
        
        user_ids = [recipient.id for recipient in recipients]
        CommunicationService.send_notification(
            user_ids=user_ids,
            title=notification_title,
            message=notification_message,
            category="urgent"
        )
    
    @staticmethod
    def _get_unread_count(user_id: int) -> int:
        """Get unread message count for a user"""
        try:
            from app.models import MessageRecipient
            return MessageRecipient.query.filter_by(
                recipient_id=user_id, is_read=False
            ).count()
        except:
            return 0
    
    @staticmethod
    def _get_replies_count(post_id: str) -> int:
        """Get reply count for a forum post"""
        try:
            from app.models import ForumReply
            return ForumReply.query.filter_by(post_id=post_id).count()
        except:
            return 0