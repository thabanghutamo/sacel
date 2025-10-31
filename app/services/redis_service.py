"""
Redis service for caching and session management in SACEL application.
Provides helper functions for common caching operations.
"""
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
from app.extensions import redis_client, cache


class RedisService:
    """Service class for Redis operations with graceful fallback."""
    
    def __init__(self):
        self.redis = redis_client
        self.cache = cache
        self.redis_available = False
        self._check_redis_availability()
    
    def _check_redis_availability(self):
        """Check if Redis is available."""
        try:
            if self.redis:
                self.redis.ping()
                self.redis_available = True
        except Exception:
            self.redis_available = False
    
    # Session Management
    def get_user_session_data(self, user_id: int, key: str) -> Optional[Any]:
        """Get user-specific session data."""
        session_key = f"user:{user_id}:session:{key}"
        try:
            data = self.redis.get(session_key)
            return pickle.loads(data) if data else None
        except Exception:
            return None
    
    def set_user_session_data(self, user_id: int, key: str, value: Any, 
                             expire: int = 3600) -> bool:
        """Set user-specific session data with expiration."""
        session_key = f"user:{user_id}:session:{key}"
        try:
            serialized_data = pickle.dumps(value)
            return self.redis.setex(session_key, expire, serialized_data)
        except Exception:
            return False
    
    def delete_user_session_data(self, user_id: int, key: str = None) -> bool:
        """Delete user session data. If key is None, deletes all user session data."""
        try:
            if key:
                session_key = f"user:{user_id}:session:{key}"
                return bool(self.redis.delete(session_key))
            else:
                # Delete all user session data
                pattern = f"user:{user_id}:session:*"
                keys = self.redis.keys(pattern)
                if keys:
                    return bool(self.redis.delete(*keys))
                return True
        except Exception:
            return False
    
    # Dashboard & Stats Caching
    def cache_teacher_stats(self, teacher_id: int, stats: dict,
                           expire: int = 300) -> bool:
        """Cache teacher dashboard statistics for 5 minutes."""
        if not self.redis_available:
            return False
            
        cache_key = f"teacher:{teacher_id}:dashboard_stats"
        try:
            serialized_stats = json.dumps(stats, default=str)
            return self.redis.setex(cache_key, expire, serialized_stats)
        except Exception:
            return False
    
    def get_teacher_stats(self, teacher_id: int) -> Optional[dict]:
        """Get cached teacher dashboard statistics."""
        if not self.redis_available:
            return None
            
        cache_key = f"teacher:{teacher_id}:dashboard_stats"
        try:
            data = self.redis.get(cache_key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    def cache_student_performance(self, teacher_id: int, performance_data: list, 
                                 expire: int = 600) -> bool:
        """Cache student performance data for 10 minutes."""
        cache_key = f"teacher:{teacher_id}:student_performance"
        try:
            serialized_data = json.dumps(performance_data, default=str)
            return self.redis.setex(cache_key, expire, serialized_data)
        except Exception:
            return False
    
    def get_student_performance(self, teacher_id: int) -> Optional[list]:
        """Get cached student performance data."""
        cache_key = f"teacher:{teacher_id}:student_performance"
        try:
            data = self.redis.get(cache_key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    # Assignment & Submission Caching
    def cache_assignment_submissions(self, assignment_id: int, submissions: list,
                                   expire: int = 180) -> bool:
        """Cache assignment submissions for 3 minutes."""
        cache_key = f"assignment:{assignment_id}:submissions"
        try:
            # Convert SQLAlchemy objects to dictionaries
            serializable_submissions = []
            for submission in submissions:
                if hasattr(submission, '__dict__'):
                    # Convert SQLAlchemy object to dict
                    submission_dict = {
                        'id': submission.id,
                        'student_id': submission.student_id,
                        'assignment_id': submission.assignment_id,
                        'grade': submission.grade,
                        'status': submission.status,
                        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                        'graded_at': submission.graded_at.isoformat() if submission.graded_at else None
                    }
                    serializable_submissions.append(submission_dict)
                else:
                    serializable_submissions.append(submission)
            
            serialized_data = json.dumps(serializable_submissions)
            return self.redis.setex(cache_key, expire, serialized_data)
        except Exception:
            return False
    
    def get_assignment_submissions(self, assignment_id: int) -> Optional[list]:
        """Get cached assignment submissions."""
        cache_key = f"assignment:{assignment_id}:submissions"
        try:
            data = self.redis.get(cache_key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    # School & User Data Caching
    def cache_school_users(self, school_id: int, users: list, 
                          expire: int = 1800) -> bool:
        """Cache school users for 30 minutes."""
        cache_key = f"school:{school_id}:users"
        try:
            # Serialize user data safely
            serializable_users = []
            for user in users:
                user_dict = {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'role': user.role.value if hasattr(user.role, 'value') else str(user.role),
                    'is_active': user.is_active
                }
                serializable_users.append(user_dict)
            
            serialized_data = json.dumps(serializable_users)
            return self.redis.setex(cache_key, expire, serialized_data)
        except Exception:
            return False
    
    def get_school_users(self, school_id: int) -> Optional[list]:
        """Get cached school users."""
        cache_key = f"school:{school_id}:users"
        try:
            data = self.redis.get(cache_key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    # Cache Invalidation
    def invalidate_teacher_cache(self, teacher_id: int) -> bool:
        """Invalidate all teacher-related cache."""
        try:
            patterns = [
                f"teacher:{teacher_id}:*",
                f"user:{teacher_id}:session:*"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = self.redis.keys(pattern)
                if keys:
                    deleted_count += self.redis.delete(*keys)
            
            return deleted_count > 0
        except Exception:
            return False
    
    def invalidate_assignment_cache(self, assignment_id: int) -> bool:
        """Invalidate assignment-related cache."""
        try:
            pattern = f"assignment:{assignment_id}:*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception:
            return False
    
    def invalidate_school_cache(self, school_id: int) -> bool:
        """Invalidate school-related cache."""
        try:
            pattern = f"school:{school_id}:*"
            keys = self.redis.keys(pattern)
            if keys:
                return bool(self.redis.delete(*keys))
            return True
        except Exception:
            return False
    
    # Health Check
    def health_check(self) -> dict:
        """Check Redis connection health."""
        try:
            # Test basic Redis operations
            test_key = "sacel:health_check"
            test_value = "ok"
            
            # Set and get a test value
            self.redis.setex(test_key, 10, test_value)
            result = self.redis.get(test_key)
            self.redis.delete(test_key)
            
            if result and result.decode('utf-8') == test_value:
                return {
                    'status': 'healthy',
                    'message': 'Redis connection is working',
                    'connected': True
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'Redis set/get operation failed',
                    'connected': False
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Redis connection error: {str(e)}',
                'connected': False
            }


# Global Redis service instance
redis_service = RedisService()


def init_redis_service():
    """Initialize Redis service after extensions are set up."""
    global redis_service
    redis_service = RedisService()
    return redis_service