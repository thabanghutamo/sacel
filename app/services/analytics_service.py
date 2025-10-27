"""
Student Performance Analytics Service for SACEL Platform
Provides comprehensive analytics for tracking student progress, identifying learning gaps, and generating insights
"""

from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, and_, or_
from app.extensions import db, redis_client
from app.models import User, Assignment, Submission, UserRole
from app.services.redis_service import redis_service
import json
import statistics


class PerformanceAnalytics:
    """Service for analyzing student performance and generating insights"""
    
    @staticmethod
    def get_student_overview(student_id, days=30):
        """Get comprehensive overview of student performance"""
        cache_key = f"student_analytics:{student_id}:{days}"
        
        # Try to get from cache first
        cached_data = redis_service.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get student info
        student = User.query.get(student_id)
        if not student or student.role != UserRole.STUDENT:
            return None
        
        # Get submissions in date range
        submissions = Submission.query.filter(
            and_(
                Submission.student_id == student_id,
                Submission.submitted_at >= start_date,
                Submission.submitted_at <= end_date,
                Submission.status == 'graded'
            )
        ).all()
        
        # Calculate basic metrics
        total_assignments = len(submissions)
        if total_assignments == 0:
            return {
                'student_name': student.full_name,
                'total_assignments': 0,
                'average_score': 0,
                'completion_rate': 0,
                'grade_trend': 'stable',
                'subjects_performance': {},
                'recent_activity': [],
                'learning_insights': []
            }
        
        # Calculate performance metrics
        scores = [s.grade for s in submissions if s.grade is not None]
        average_score = statistics.mean(scores) if scores else 0
        
        # Calculate completion rate (assignments submitted vs total assigned)
        total_assigned = Assignment.query.filter(
            Assignment.due_date >= start_date
        ).count()
        completion_rate = (total_assignments / total_assigned * 100) if total_assigned > 0 else 0
        
        # Analyze grade trend
        grade_trend = PerformanceAnalytics._calculate_grade_trend(submissions)
        
        # Subject-wise performance
        subjects_performance = PerformanceAnalytics._analyze_subject_performance(submissions)
        
        # Recent activity
        recent_activity = PerformanceAnalytics._get_recent_activity(student_id, 10)
        
        # Generate learning insights
        learning_insights = PerformanceAnalytics._generate_learning_insights(
            student_id, submissions, subjects_performance
        )
        
        analytics_data = {
            'student_name': student.full_name,
            'total_assignments': total_assignments,
            'average_score': round(average_score, 2),
            'completion_rate': round(completion_rate, 2),
            'grade_trend': grade_trend,
            'subjects_performance': subjects_performance,
            'recent_activity': recent_activity,
            'learning_insights': learning_insights,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 1 hour
        redis_service.cache_data(cache_key, analytics_data, timeout=3600)
        
        return analytics_data
    
    @staticmethod
    def get_class_analytics(teacher_id, subject=None, grade_level=None):
        """Get analytics for teacher's classes"""
        cache_key = f"class_analytics:{teacher_id}:{subject}:{grade_level}"
        
        cached_data = redis_service.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Get teacher's assignments
        query = Assignment.query.filter_by(teacher_id=teacher_id)
        if subject:
            query = query.filter_by(subject=subject)
        if grade_level:
            query = query.filter_by(grade_level=grade_level)
        
        assignments = query.all()
        assignment_ids = [a.id for a in assignments]
        
        if not assignment_ids:
            return {
                'total_students': 0,
                'total_assignments': 0,
                'average_class_score': 0,
                'completion_rate': 0,
                'top_performers': [],
                'struggling_students': [],
                'subject_breakdown': {},
                'grade_distribution': {}
            }
        
        # Get all submissions for these assignments
        submissions = Submission.query.filter(
            and_(
                Submission.assignment_id.in_(assignment_ids),
                Submission.status == 'graded'
            )
        ).all()
        
        # Calculate class metrics
        total_students = len(set(s.student_id for s in submissions))
        total_assignments = len(assignments)
        
        scores = [s.grade for s in submissions if s.grade is not None]
        average_class_score = statistics.mean(scores) if scores else 0
        
        # Calculate completion rate
        total_possible_submissions = total_assignments * total_students
        actual_submissions = len([s for s in submissions if s.status in ['submitted', 'graded']])
        completion_rate = (actual_submissions / total_possible_submissions * 100) if total_possible_submissions > 0 else 0
        
        # Identify top performers and struggling students
        student_averages = PerformanceAnalytics._calculate_student_averages(submissions)
        top_performers = sorted(student_averages.items(), key=lambda x: x[1], reverse=True)[:5]
        struggling_students = sorted(student_averages.items(), key=lambda x: x[1])[:5]
        
        # Subject breakdown
        subject_breakdown = PerformanceAnalytics._analyze_class_subjects(assignments, submissions)
        
        # Grade distribution
        grade_distribution = PerformanceAnalytics._calculate_grade_distribution(scores)
        
        analytics_data = {
            'total_students': total_students,
            'total_assignments': total_assignments,
            'average_class_score': round(average_class_score, 2),
            'completion_rate': round(completion_rate, 2),
            'top_performers': [
                {'student_name': User.query.get(student_id).full_name, 'average': round(avg, 2)}
                for student_id, avg in top_performers
            ],
            'struggling_students': [
                {'student_name': User.query.get(student_id).full_name, 'average': round(avg, 2)}
                for student_id, avg in struggling_students
            ],
            'subject_breakdown': subject_breakdown,
            'grade_distribution': grade_distribution,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 30 minutes
        redis_service.cache_data(cache_key, analytics_data, timeout=1800)
        
        return analytics_data
    
    @staticmethod
    def get_school_analytics(school_id):
        """Get comprehensive school-level analytics"""
        cache_key = f"school_analytics:{school_id}"
        
        cached_data = redis_service.get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        # Get all students in the school
        students = User.query.filter_by(school_id=school_id, role=UserRole.STUDENT).all()
        student_ids = [s.id for s in students]
        
        # Get all teachers in the school
        teachers = User.query.filter_by(school_id=school_id, role=UserRole.TEACHER).all()
        teacher_ids = [t.id for t in teachers]
        
        # Get all assignments from school's teachers
        assignments = Assignment.query.filter(Assignment.teacher_id.in_(teacher_ids)).all()
        assignment_ids = [a.id for a in assignments]
        
        # Get all submissions
        submissions = Submission.query.filter(
            and_(
                Submission.assignment_id.in_(assignment_ids),
                Submission.student_id.in_(student_ids)
            )
        ).all()
        
        # Calculate school metrics
        total_students = len(students)
        total_teachers = len(teachers)
        total_assignments = len(assignments)
        
        graded_submissions = [s for s in submissions if s.status == 'graded' and s.grade is not None]
        scores = [s.grade for s in graded_submissions]
        
        school_average = statistics.mean(scores) if scores else 0
        
        # Performance by grade level
        grade_performance = PerformanceAnalytics._analyze_grade_level_performance(
            students, assignments, submissions
        )
        
        # Subject performance
        subject_performance = PerformanceAnalytics._analyze_school_subject_performance(
            assignments, submissions
        )
        
        # Teacher effectiveness metrics
        teacher_effectiveness = PerformanceAnalytics._calculate_teacher_effectiveness(
            teachers, assignments, submissions
        )
        
        analytics_data = {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_assignments': total_assignments,
            'school_average': round(school_average, 2),
            'grade_performance': grade_performance,
            'subject_performance': subject_performance,
            'teacher_effectiveness': teacher_effectiveness,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Cache for 1 hour
        redis_service.cache_data(cache_key, analytics_data, timeout=3600)
        
        return analytics_data
    
    @staticmethod
    def _calculate_grade_trend(submissions):
        """Calculate if grades are improving, declining, or stable"""
        if len(submissions) < 3:
            return 'insufficient_data'
        
        # Sort by submission date
        sorted_submissions = sorted(submissions, key=lambda x: x.submitted_at)
        scores = [s.grade for s in sorted_submissions if s.grade is not None]
        
        if len(scores) < 3:
            return 'insufficient_data'
        
        # Calculate trend using simple linear regression slope
        n = len(scores)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(x_values, scores))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.5:
            return 'improving'
        elif slope < -0.5:
            return 'declining'
        else:
            return 'stable'
    
    @staticmethod
    def _analyze_subject_performance(submissions):
        """Analyze performance by subject"""
        subject_data = {}
        
        for submission in submissions:
            if submission.assignment and submission.grade is not None:
                subject = submission.assignment.subject
                if subject not in subject_data:
                    subject_data[subject] = []
                subject_data[subject].append(submission.grade)
        
        result = {}
        for subject, scores in subject_data.items():
            result[subject] = {
                'average': round(statistics.mean(scores), 2),
                'count': len(scores),
                'highest': max(scores),
                'lowest': min(scores)
            }
        
        return result
    
    @staticmethod
    def _get_recent_activity(student_id, limit=10):
        """Get recent activity for a student"""
        recent_submissions = Submission.query.filter_by(
            student_id=student_id
        ).order_by(
            Submission.submitted_at.desc()
        ).limit(limit).all()
        
        activity = []
        for submission in recent_submissions:
            if submission.assignment:
                activity.append({
                    'assignment_title': submission.assignment.title,
                    'subject': submission.assignment.subject,
                    'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                    'grade': submission.grade,
                    'status': submission.status
                })
        
        return activity
    
    @staticmethod
    def _generate_learning_insights(student_id, submissions, subjects_performance):
        """Generate AI-powered learning insights"""
        insights = []
        
        # Analyze subject strengths and weaknesses
        if subjects_performance:
            best_subject = max(subjects_performance.items(), key=lambda x: x[1]['average'])
            worst_subject = min(subjects_performance.items(), key=lambda x: x[1]['average'])
            
            insights.append({
                'type': 'strength',
                'message': f"Strong performance in {best_subject[0]} with {best_subject[1]['average']}% average",
                'subject': best_subject[0]
            })
            
            if worst_subject[1]['average'] < 70:
                insights.append({
                    'type': 'improvement_needed',
                    'message': f"Consider additional practice in {worst_subject[0]} (current average: {worst_subject[1]['average']}%)",
                    'subject': worst_subject[0]
                })
        
        # Analyze submission patterns
        if submissions:
            recent_scores = [s.grade for s in submissions[-5:] if s.grade is not None]
            if len(recent_scores) >= 3:
                recent_avg = statistics.mean(recent_scores)
                overall_avg = statistics.mean([s.grade for s in submissions if s.grade is not None])
                
                if recent_avg > overall_avg + 5:
                    insights.append({
                        'type': 'positive_trend',
                        'message': f"Recent performance shows improvement! Recent average: {recent_avg:.1f}%"
                    })
                elif recent_avg < overall_avg - 5:
                    insights.append({
                        'type': 'concern',
                        'message': f"Recent performance has declined. Consider reaching out for support."
                    })
        
        return insights
    
    @staticmethod
    def _calculate_student_averages(submissions):
        """Calculate average score for each student"""
        student_scores = {}
        
        for submission in submissions:
            if submission.grade is not None:
                if submission.student_id not in student_scores:
                    student_scores[submission.student_id] = []
                student_scores[submission.student_id].append(submission.grade)
        
        return {
            student_id: statistics.mean(scores) 
            for student_id, scores in student_scores.items()
        }
    
    @staticmethod
    def _analyze_class_subjects(assignments, submissions):
        """Analyze performance by subject for a class"""
        subject_data = {}
        
        for assignment in assignments:
            subject = assignment.subject
            if subject not in subject_data:
                subject_data[subject] = {
                    'total_assignments': 0,
                    'scores': []
                }
            subject_data[subject]['total_assignments'] += 1
        
        for submission in submissions:
            if submission.assignment and submission.grade is not None:
                subject = submission.assignment.subject
                if subject in subject_data:
                    subject_data[subject]['scores'].append(submission.grade)
        
        result = {}
        for subject, data in subject_data.items():
            scores = data['scores']
            result[subject] = {
                'total_assignments': data['total_assignments'],
                'completed_submissions': len(scores),
                'average_score': round(statistics.mean(scores), 2) if scores else 0,
                'completion_rate': round(len(scores) / data['total_assignments'] * 100, 2) if data['total_assignments'] > 0 else 0
            }
        
        return result
    
    @staticmethod
    def _calculate_grade_distribution(scores):
        """Calculate grade distribution"""
        if not scores:
            return {}
        
        distribution = {
            'A (90-100)': 0,
            'B (80-89)': 0,
            'C (70-79)': 0,
            'D (60-69)': 0,
            'F (0-59)': 0
        }
        
        for score in scores:
            if score >= 90:
                distribution['A (90-100)'] += 1
            elif score >= 80:
                distribution['B (80-89)'] += 1
            elif score >= 70:
                distribution['C (70-79)'] += 1
            elif score >= 60:
                distribution['D (60-69)'] += 1
            else:
                distribution['F (0-59)'] += 1
        
        total = len(scores)
        return {
            grade: {
                'count': count,
                'percentage': round(count / total * 100, 1)
            }
            for grade, count in distribution.items()
        }
    
    @staticmethod
    def _analyze_grade_level_performance(students, assignments, submissions):
        """Analyze performance by grade level"""
        grade_data = {}
        
        # Group students by grade level based on assignments
        for assignment in assignments:
            grade_level = assignment.grade_level
            if grade_level not in grade_data:
                grade_data[grade_level] = {
                    'students': set(),
                    'scores': []
                }
        
        for submission in submissions:
            if submission.assignment and submission.grade is not None:
                grade_level = submission.assignment.grade_level
                if grade_level in grade_data:
                    grade_data[grade_level]['students'].add(submission.student_id)
                    grade_data[grade_level]['scores'].append(submission.grade)
        
        result = {}
        for grade_level, data in grade_data.items():
            scores = data['scores']
            result[f"Grade {grade_level}"] = {
                'student_count': len(data['students']),
                'average_score': round(statistics.mean(scores), 2) if scores else 0,
                'total_submissions': len(scores)
            }
        
        return result
    
    @staticmethod
    def _analyze_school_subject_performance(assignments, submissions):
        """Analyze subject performance across the school"""
        return PerformanceAnalytics._analyze_class_subjects(assignments, submissions)
    
    @staticmethod
    def _calculate_teacher_effectiveness(teachers, assignments, submissions):
        """Calculate teacher effectiveness metrics"""
        teacher_data = {}
        
        for teacher in teachers:
            teacher_assignments = [a for a in assignments if a.teacher_id == teacher.id]
            assignment_ids = [a.id for a in teacher_assignments]
            
            teacher_submissions = [
                s for s in submissions 
                if s.assignment_id in assignment_ids and s.grade is not None
            ]
            
            if teacher_submissions:
                scores = [s.grade for s in teacher_submissions]
                teacher_data[teacher.full_name] = {
                    'total_assignments': len(teacher_assignments),
                    'total_submissions': len(teacher_submissions),
                    'average_student_score': round(statistics.mean(scores), 2),
                    'subjects_taught': list(set(a.subject for a in teacher_assignments))
                }
        
        return teacher_data


# Analytics utility functions
def invalidate_analytics_cache(student_id=None, teacher_id=None, school_id=None):
    """Invalidate analytics cache when data changes"""
    patterns = []
    
    if student_id:
        patterns.append(f"student_analytics:{student_id}:*")
    if teacher_id:
        patterns.append(f"class_analytics:{teacher_id}:*")
    if school_id:
        patterns.append(f"school_analytics:{school_id}")
    
    for pattern in patterns:
        redis_service.delete_pattern(pattern)


def get_learning_recommendations(student_id):
    """Get AI-powered learning recommendations for a student"""
    analytics = PerformanceAnalytics.get_student_overview(student_id)
    
    if not analytics or analytics['total_assignments'] == 0:
        return []
    
    recommendations = []
    
    # Performance-based recommendations
    if analytics['average_score'] < 70:
        recommendations.append({
            'type': 'improvement',
            'priority': 'high',
            'title': 'Focus on Foundation Skills',
            'description': 'Your average score indicates you may benefit from reviewing fundamental concepts.',
            'action': 'Schedule study sessions with a teacher or tutor'
        })
    
    # Subject-specific recommendations
    subjects_performance = analytics.get('subjects_performance', {})
    for subject, performance in subjects_performance.items():
        if performance['average'] < 60:
            recommendations.append({
                'type': 'subject_focus',
                'priority': 'high',
                'title': f'Improve {subject} Performance',
                'description': f'Your {subject} average is {performance["average"]}%. Additional practice recommended.',
                'action': f'Complete extra {subject} exercises and seek teacher feedback'
            })
    
    # Completion rate recommendations
    if analytics['completion_rate'] < 80:
        recommendations.append({
            'type': 'organization',
            'priority': 'medium',
            'title': 'Improve Assignment Completion',
            'description': f'You\'ve completed {analytics["completion_rate"]}% of assignments. Better organization can help.',
            'action': 'Create a study schedule and set assignment reminders'
        })
    
    return recommendations