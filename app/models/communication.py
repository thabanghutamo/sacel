"""
Communication Models for SACEL Platform
Database models for messaging, forums, notifications, and announcements
"""

from app.extensions import db
from datetime import datetime
import uuid


class Message(db.Model):
    """Model for messages between users"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='personal')  # personal, announcement, system
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    attachments = db.Column(db.Text)  # JSON string of attachment info
    is_draft = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipients = db.relationship('MessageRecipient', backref='message', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Message {self.id}: {self.subject}>'


class MessageRecipient(db.Model):
    """Model for message recipients and read status"""
    __tablename__ = 'message_recipients'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    is_starred = db.Column(db.Boolean, default=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')
    
    def __repr__(self):
        return f'<MessageRecipient {self.message_id} -> {self.recipient_id}>'


class ForumCategory(db.Model):
    """Model for forum categories"""
    __tablename__ = 'forum_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color code
    icon = db.Column(db.String(50))  # Font Awesome icon class
    is_active = db.Column(db.Boolean, default=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('ForumPost', backref='category_obj', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumCategory {self.name}>'


class ForumPost(db.Model):
    """Model for forum posts"""
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'))
    category = db.Column(db.String(50))  # For backward compatibility
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text)  # JSON string of tags
    is_pinned = db.Column(db.Boolean, default=False)
    is_locked = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', foreign_keys=[user_id], backref='forum_posts')
    replies = db.relationship('ForumReply', backref='post', cascade='all, delete-orphan')
    likes_rel = db.relationship('ForumPostLike', backref='post', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumPost {self.id}: {self.title}>'


class ForumReply(db.Model):
    """Model for forum post replies"""
    __tablename__ = 'forum_replies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = db.Column(db.String(36), db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_reply_id = db.Column(db.String(36), db.ForeignKey('forum_replies.id'))  # For nested replies
    content = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    likes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', foreign_keys=[user_id], backref='forum_replies')
    parent_reply = db.relationship('ForumReply', remote_side=[id], backref='child_replies')
    likes_rel = db.relationship('ForumReplyLike', backref='reply', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ForumReply {self.id} on {self.post_id}>'


class ForumPostLike(db.Model):
    """Model for forum post likes"""
    __tablename__ = 'forum_post_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(36), db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate likes
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_like'),)
    
    def __repr__(self):
        return f'<ForumPostLike {self.post_id} by {self.user_id}>'


class ForumReplyLike(db.Model):
    """Model for forum reply likes"""
    __tablename__ = 'forum_reply_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    reply_id = db.Column(db.String(36), db.ForeignKey('forum_replies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate likes
    __table_args__ = (db.UniqueConstraint('reply_id', 'user_id', name='unique_reply_like'),)
    
    def __repr__(self):
        return f'<ForumReplyLike {self.reply_id} by {self.user_id}>'


class Notification(db.Model):
    """Model for user notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='general')  # academic, administrative, social, etc.
    action_url = db.Column(db.String(500))  # URL for notification action
    action_text = db.Column(db.String(50))  # Text for action button
    is_read = db.Column(db.Boolean, default=False)
    is_dismissed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    expires_at = db.Column(db.DateTime)  # Optional expiration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'


class Announcement(db.Model):
    """Model for system announcements"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='general')
    priority = db.Column(db.String(10), default='normal')
    target_roles = db.Column(db.Text)  # JSON string of target roles
    target_schools = db.Column(db.Text)  # JSON string of target school IDs
    is_active = db.Column(db.Boolean, default=True)
    is_urgent = db.Column(db.Boolean, default=False)
    show_until = db.Column(db.DateTime)  # When to stop showing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='announcements')
    views = db.relationship('AnnouncementView', backref='announcement', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Announcement {self.id}: {self.title}>'


class AnnouncementView(db.Model):
    """Model to track who has viewed announcements"""
    __tablename__ = 'announcement_views'
    
    id = db.Column(db.Integer, primary_key=True)
    announcement_id = db.Column(db.String(36), db.ForeignKey('announcements.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate views
    __table_args__ = (db.UniqueConstraint('announcement_id', 'user_id', name='unique_announcement_view'),)
    
    def __repr__(self):
        return f'<AnnouncementView {self.announcement_id} by {self.user_id}>'


class ChatRoom(db.Model):
    """Model for chat rooms"""
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    room_type = db.Column(db.String(20), default='group')  # private, group, class, school
    is_private = db.Column(db.Boolean, default=False)
    max_participants = db.Column(db.Integer, default=50)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[creator_id], backref='created_chat_rooms')
    participants = db.relationship('ChatParticipant', backref='room', cascade='all, delete-orphan')
    messages = db.relationship('ChatMessage', backref='room', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ChatRoom {self.id}: {self.name}>'


class ChatParticipant(db.Model):
    """Model for chat room participants"""
    __tablename__ = 'chat_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # admin, moderator, member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_muted = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='chat_participations')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='unique_room_participant'),)
    
    def __repr__(self):
        return f'<ChatParticipant {self.user_id} in {self.room_id}>'


class ChatMessage(db.Model):
    """Model for chat messages"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, file, system
    attachments = db.Column(db.Text)  # JSON string of attachments
    reply_to_id = db.Column(db.String(36), db.ForeignKey('chat_messages.id'))  # For replies
    is_edited = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='chat_messages')
    reply_to = db.relationship('ChatMessage', remote_side=[id], backref='replies')
    
    def __repr__(self):
        return f'<ChatMessage {self.id} in {self.room_id}>'