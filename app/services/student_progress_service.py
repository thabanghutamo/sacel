"""
Student Progress Tracking Service for SACEL Platform
Provides comprehensive progress monitoring and learning analytics
"""

from flask import current_app
from sqlalchemy import desc
from app.extensions import db
from app.models import User, Assignment, Submission
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any
import statistics


class StudentProgressService:
    """Service for tracking and analyzing student progress"""
    
    @staticmethod
    def get_student_overview(student_id: int) -> Dict[str, Any]:
        """Get comprehensive overview of student's academic progress"""
        try:
            student = User.query.get(student_id)
            if not student or student.role.value != 'student':
                return {'error': 'Student not found'}
            
            # Get submissions with grades
            submissions = db.session.query(Submission).filter(
                Submission.student_id == student_id,
                Submission.status == 'graded'
            ).join(Assignment).order_by(desc(Submission.submitted_at)).all()
            
            # Calculate overall statistics
            total_assignments = len(submissions)
            graded_assignments = len([s for s in submissions 
                                      if s.grade is not None])
            
            if graded_assignments > 0:
                grades = [s.grade for s in submissions if s.grade is not None]
                average_grade = round(statistics.mean(grades), 2)
                highest_grade = max(grades)
                lowest_grade = min(grades)
            else:
                average_grade = 0
                highest_grade = 0
                lowest_grade = 0
            
            # Get recent submissions (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_submissions = [s for s in submissions
                                 if s.submitted_at and 
                                 s.submitted_at >= thirty_days_ago]
            
            # Subject performance breakdown
            subject_performance = (
                StudentProgressService._calculate_subject_performance(submissions)
            )
            
            # Assignment completion rate
            total_available = db.session.query(Assignment).filter(
                Assignment.teacher_id.in_(
                    db.session.query(User.id).filter(
                        User.school_id == student.school_id,
                        User.role == 'teacher'
                    )
                )
            ).count()
            
            completion_rate = round((total_assignments / total_available * 100), 2) if total_available > 0 else 0
            
            return {
                'student_info': {
                    'name': student.full_name,
                    'email': student.email,
                    'school': student.school.name if student.school else None,
                    'student_id': student_id
                },
                'academic_summary': {
                    'total_assignments': total_assignments,
                    'graded_assignments': graded_assignments,
                    'average_grade': average_grade,
                    'highest_grade': highest_grade,
                    'lowest_grade': lowest_grade,
                    'completion_rate': completion_rate
                },
                'recent_activity': {
                    'submissions_last_30_days': len(recent_submissions),
                    'recent_average': round(statistics.mean([s.grade for s in recent_submissions if s.grade]), 2) if recent_submissions else 0
                },
                'subject_performance': subject_performance,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in get_student_overview: {str(e)}")
            return {'error': 'Failed to fetch student overview'}
    
    @staticmethod
    def get_grade_history(student_id: int, timeframe: str = '6months') -> Dict[str, Any]:
        """Get detailed grade history with trends"""
        try:
            # Calculate date range
            if timeframe == '1month':
                start_date = datetime.utcnow() - timedelta(days=30)
            elif timeframe == '3months':
                start_date = datetime.utcnow() - timedelta(days=90)
            elif timeframe == '6months':
                start_date = datetime.utcnow() - timedelta(days=180)
            elif timeframe == '1year':
                start_date = datetime.utcnow() - timedelta(days=365)
            else:
                start_date = datetime.utcnow() - timedelta(days=180)  # Default 6 months
            
            # Get submissions with grades in timeframe
            submissions = db.session.query(Submission).filter(
                Submission.student_id == student_id,
                Submission.status == 'graded',
                Submission.grade.isnot(None),
                Submission.submitted_at >= start_date
            ).join(Assignment).order_by(Submission.submitted_at).all()
            
            # Group by week for trend analysis
            weekly_grades = defaultdict(list)
            grade_timeline = []
            
            for submission in submissions:
                if submission.submitted_at:
                    week_key = submission.submitted_at.strftime('%Y-W%U')
                    weekly_grades[week_key].append(submission.grade)
                    
                    grade_timeline.append({
                        'date': submission.submitted_at.isoformat(),
                        'grade': submission.grade,
                        'assignment_title': submission.assignment.title,
                        'subject': submission.assignment.subject,
                        'max_score': submission.assignment.max_score
                    })
            
            # Calculate weekly averages
            weekly_averages = []
            for week, grades in sorted(weekly_grades.items()):
                avg_grade = round(statistics.mean(grades), 2)
                weekly_averages.append({
                    'week': week,
                    'average_grade': avg_grade,
                    'assignment_count': len(grades)
                })
            
            # Calculate trend
            trend = StudentProgressService._calculate_grade_trend(weekly_averages)
            
            # Subject-wise grade history
            subject_history = StudentProgressService._get_subject_grade_history(submissions)
            
            return {
                'timeframe': timeframe,
                'total_graded_assignments': len(submissions),
                'grade_timeline': grade_timeline,
                'weekly_averages': weekly_averages,
                'trend_analysis': trend,
                'subject_history': subject_history,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in get_grade_history: {str(e)}")
            return {'error': 'Failed to fetch grade history'}
    
    @staticmethod
    def get_assignment_submissions(student_id: int, status: str = 'all') -> Dict[str, Any]:
        """Get detailed assignment submission history"""
        try:
            base_query = db.session.query(Submission).filter(
                Submission.student_id == student_id
            ).join(Assignment)
            
            # Filter by status if specified
            if status != 'all':
                base_query = base_query.filter(Submission.status == status)
            
            submissions = base_query.order_by(desc(Submission.created_at)).all()
            
            submission_details = []
            for submission in submissions:
                submission_info = {
                    'id': submission.id,
                    'assignment_title': submission.assignment.title,
                    'subject': submission.assignment.subject,
                    'due_date': submission.assignment.due_date.isoformat() if submission.assignment.due_date else None,
                    'status': submission.status,
                    'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                    'grade': submission.grade,
                    'max_score': submission.assignment.max_score,
                    'feedback': submission.feedback,
                    'is_late': submission.submitted_at > submission.assignment.due_date if submission.submitted_at and submission.assignment.due_date else False,
                    'graded_at': submission.graded_at.isoformat() if submission.graded_at else None
                }
                submission_details.append(submission_info)
            
            # Calculate submission statistics
            total_submissions = len(submissions)
            graded_count = len([s for s in submissions if s.status == 'graded'])
            pending_count = len([s for s in submissions if s.status == 'submitted'])
            draft_count = len([s for s in submissions if s.status == 'draft'])
            
            # Late submission analysis
            late_submissions = [s for s in submissions 
                              if s.submitted_at and s.assignment.due_date and 
                              s.submitted_at > s.assignment.due_date]
            
            return {
                'total_submissions': total_submissions,
                'status_breakdown': {
                    'graded': graded_count,
                    'pending': pending_count,
                    'draft': draft_count
                },
                'late_submissions': len(late_submissions),
                'on_time_rate': round(((total_submissions - len(late_submissions)) / total_submissions * 100), 2) if total_submissions > 0 else 0,
                'submissions': submission_details,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in get_assignment_submissions: {str(e)}")
            return {'error': 'Failed to fetch assignment submissions'}
    
    @staticmethod
    def get_performance_trends(student_id: int) -> Dict[str, Any]:
        """Analyze performance trends and patterns"""
        try:
            # Get all graded submissions
            submissions = db.session.query(Submission).filter(
                Submission.student_id == student_id,
                Submission.status == 'graded',
                Submission.grade.isnot(None)
            ).join(Assignment).order_by(Submission.submitted_at).all()
            
            if not submissions:
                return {'message': 'No graded submissions found'}
            
            # Performance over time
            performance_timeline = []
            for submission in submissions:
                if submission.submitted_at:
                    performance_timeline.append({
                        'date': submission.submitted_at.strftime('%Y-%m-%d'),
                        'grade': submission.grade,
                        'percentage': round((submission.grade / submission.assignment.max_score * 100), 2),
                        'subject': submission.assignment.subject
                    })
            
            # Calculate moving averages
            moving_averages = StudentProgressService._calculate_moving_averages(submissions)
            
            # Subject-wise trends
            subject_trends = StudentProgressService._analyze_subject_trends(submissions)
            
            # Improvement areas identification
            improvement_areas = StudentProgressService._identify_improvement_areas(submissions)
            
            # Strengths identification
            strengths = StudentProgressService._identify_strengths(submissions)
            
            return {
                'performance_timeline': performance_timeline,
                'moving_averages': moving_averages,
                'subject_trends': subject_trends,
                'improvement_areas': improvement_areas,
                'strengths': strengths,
                'total_assignments_analyzed': len(submissions),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in get_performance_trends: {str(e)}")
            return {'error': 'Failed to analyze performance trends'}
    
    @staticmethod
    def get_learning_recommendations(student_id: int) -> Dict[str, Any]:
        """Generate personalized learning recommendations"""
        try:
            # Get student's performance data
            overview = StudentProgressService.get_student_overview(student_id)
            trends = StudentProgressService.get_performance_trends(student_id)
            
            if 'error' in overview or 'error' in trends:
                return {'error': 'Unable to generate recommendations due to insufficient data'}
            
            recommendations = []
            
            # Analyze overall performance
            avg_grade = overview['academic_summary']['average_grade']
            completion_rate = overview['academic_summary']['completion_rate']
            
            # Academic performance recommendations
            if avg_grade < 70:
                recommendations.append({
                    'type': 'academic_support',
                    'priority': 'high',
                    'title': 'Academic Support Needed',
                    'description': 'Consider scheduling additional tutoring sessions or study groups',
                    'action_items': [
                        'Meet with teacher during office hours',
                        'Form study groups with classmates',
                        'Use additional practice resources'
                    ]
                })
            elif avg_grade > 85:
                recommendations.append({
                    'type': 'enrichment',
                    'priority': 'medium',
                    'title': 'Enrichment Opportunities',
                    'description': 'Explore advanced materials and challenging projects',
                    'action_items': [
                        'Consider advanced courses',
                        'Participate in academic competitions',
                        'Mentor other students'
                    ]
                })
            
            # Completion rate recommendations
            if completion_rate < 80:
                recommendations.append({
                    'type': 'time_management',
                    'priority': 'high',
                    'title': 'Improve Assignment Completion',
                    'description': 'Focus on better time management and organization',
                    'action_items': [
                        'Create a study schedule',
                        'Set up assignment reminders',
                        'Break large tasks into smaller steps'
                    ]
                })
            
            # Subject-specific recommendations
            if 'subject_performance' in overview:
                weak_subjects = [subject for subject, data in overview['subject_performance'].items() 
                               if data.get('average_grade', 0) < 70]
                
                for subject in weak_subjects:
                    recommendations.append({
                        'type': 'subject_focus',
                        'priority': 'medium',
                        'title': f'Focus on {subject}',
                        'description': f'Additional attention needed in {subject}',
                        'action_items': [
                            f'Review {subject} fundamentals',
                            f'Practice {subject} problems daily',
                            f'Seek help from {subject} teacher'
                        ]
                    })
            
            # Study habits recommendations
            recommendations.append({
                'type': 'study_habits',
                'priority': 'low',
                'title': 'Optimize Study Habits',
                'description': 'General recommendations for effective learning',
                'action_items': [
                    'Create a dedicated study space',
                    'Use active learning techniques',
                    'Take regular breaks during study sessions',
                    'Review material regularly, not just before tests'
                ]
            })
            
            return {
                'student_id': student_id,
                'recommendations': recommendations,
                'generated_at': datetime.utcnow().isoformat(),
                'data_points_analyzed': {
                    'average_grade': avg_grade,
                    'completion_rate': completion_rate,
                    'total_assignments': overview['academic_summary']['total_assignments']
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in get_learning_recommendations: {str(e)}")
            return {'error': 'Failed to generate learning recommendations'}
    
    @staticmethod
    def compare_with_peers(student_id: int, scope: str = 'school') -> Dict[str, Any]:
        """Compare student performance with peers"""
        try:
            student = User.query.get(student_id)
            if not student:
                return {'error': 'Student not found'}
            
            # Get student's average grade
            student_submissions = db.session.query(Submission).filter(
                Submission.student_id == student_id,
                Submission.status == 'graded',
                Submission.grade.isnot(None)
            ).all()
            
            if not student_submissions:
                return {'message': 'No graded submissions found for comparison'}
            
            student_avg = statistics.mean([s.grade for s in student_submissions])
            
            # Define peer group based on scope
            if scope == 'school':
                # Compare with students in the same school
                peer_query = db.session.query(User).filter(
                    User.role == 'student',
                    User.school_id == student.school_id,
                    User.id != student_id
                )
            elif scope == 'grade':
                # Compare with students in the same grade (if grade info available)
                # For now, use school scope as we don't have grade level in User model
                peer_query = db.session.query(User).filter(
                    User.role == 'student',
                    User.school_id == student.school_id,
                    User.id != student_id
                )
            else:
                return {'error': 'Invalid scope. Use "school" or "grade"'}
            
            peers = peer_query.all()
            peer_averages = []
            
            for peer in peers:
                peer_submissions = db.session.query(Submission).filter(
                    Submission.student_id == peer.id,
                    Submission.status == 'graded',
                    Submission.grade.isnot(None)
                ).all()
                
                if peer_submissions:
                    peer_avg = statistics.mean([s.grade for s in peer_submissions])
                    peer_averages.append(peer_avg)
            
            if not peer_averages:
                return {'message': 'No peer data available for comparison'}
            
            # Calculate comparison statistics
            peer_class_average = statistics.mean(peer_averages)
            peer_median = statistics.median(peer_averages)
            
            # Calculate percentile
            better_than_count = len([avg for avg in peer_averages if avg < student_avg])
            percentile = round((better_than_count / len(peer_averages) * 100), 1)
            
            # Performance classification
            if percentile >= 90:
                performance_level = 'Excellent'
            elif percentile >= 75:
                performance_level = 'Above Average'
            elif percentile >= 50:
                performance_level = 'Average'
            elif percentile >= 25:
                performance_level = 'Below Average'
            else:
                performance_level = 'Needs Improvement'
            
            return {
                'student_average': round(student_avg, 2),
                'peer_group_average': round(peer_class_average, 2),
                'peer_group_median': round(peer_median, 2),
                'percentile': percentile,
                'performance_level': performance_level,
                'total_peers': len(peer_averages),
                'scope': scope,
                'comparison_insights': {
                    'above_average': student_avg > peer_class_average,
                    'difference_from_average': round(student_avg - peer_class_average, 2),
                    'rank_estimate': f"Top {100-percentile:.0f}%" if percentile > 50 else f"Bottom {percentile:.0f}%"
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in compare_with_peers: {str(e)}")
            return {'error': 'Failed to compare with peers'}
    
    # Helper methods
    @staticmethod
    def _calculate_subject_performance(submissions: List[Submission]) -> Dict[str, Any]:
        """Calculate performance breakdown by subject"""
        subject_data = defaultdict(list)
        
        for submission in submissions:
            if submission.grade is not None:
                subject_data[submission.assignment.subject].append(submission.grade)
        
        subject_performance = {}
        for subject, grades in subject_data.items():
            subject_performance[subject] = {
                'assignment_count': len(grades),
                'average_grade': round(statistics.mean(grades), 2),
                'highest_grade': max(grades),
                'lowest_grade': min(grades),
                'std_deviation': round(statistics.stdev(grades), 2) if len(grades) > 1 else 0
            }
        
        return subject_performance
    
    @staticmethod
    def _calculate_grade_trend(weekly_averages: List[Dict]) -> Dict[str, Any]:
        """Calculate grade trend analysis"""
        if len(weekly_averages) < 2:
            return {'trend': 'insufficient_data', 'description': 'Not enough data for trend analysis'}
        
        grades = [week['average_grade'] for week in weekly_averages]
        
        # Simple linear trend
        first_half = grades[:len(grades)//2]
        second_half = grades[len(grades)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        difference = second_avg - first_avg
        
        if difference > 2:
            trend = 'improving'
            description = 'Grades are showing an upward trend'
        elif difference < -2:
            trend = 'declining'
            description = 'Grades are showing a downward trend'
        else:
            trend = 'stable'
            description = 'Grades are relatively stable'
        
        return {
            'trend': trend,
            'description': description,
            'change_magnitude': round(difference, 2),
            'first_period_average': round(first_avg, 2),
            'recent_period_average': round(second_avg, 2)
        }
    
    @staticmethod
    def _get_subject_grade_history(submissions: List[Submission]) -> Dict[str, List]:
        """Get grade history organized by subject"""
        subject_history = defaultdict(list)
        
        for submission in submissions:
            if submission.grade is not None and submission.submitted_at:
                subject_history[submission.assignment.subject].append({
                    'date': submission.submitted_at.strftime('%Y-%m-%d'),
                    'grade': submission.grade,
                    'assignment_title': submission.assignment.title
                })
        
        # Sort by date for each subject
        for subject in subject_history:
            subject_history[subject].sort(key=lambda x: x['date'])
        
        return dict(subject_history)
    
    @staticmethod
    def _calculate_moving_averages(submissions: List[Submission], window: int = 5) -> List[Dict]:
        """Calculate moving averages for grade trends"""
        if len(submissions) < window:
            return []
        
        moving_averages = []
        grades = [s.grade for s in submissions if s.grade is not None]
        
        for i in range(window - 1, len(grades)):
            window_grades = grades[i - window + 1:i + 1]
            avg = statistics.mean(window_grades)
            moving_averages.append({
                'position': i + 1,
                'moving_average': round(avg, 2),
                'window_size': window
            })
        
        return moving_averages
    
    @staticmethod
    def _analyze_subject_trends(submissions: List[Submission]) -> Dict[str, Dict]:
        """Analyze trends for each subject"""
        subject_submissions = defaultdict(list)
        
        for submission in submissions:
            if submission.grade is not None:
                subject_submissions[submission.assignment.subject].append(submission)
        
        subject_trends = {}
        for subject, sub_list in subject_submissions.items():
            if len(sub_list) >= 3:  # Need at least 3 submissions for trend
                grades = [s.grade for s in sorted(sub_list, key=lambda x: x.submitted_at or datetime.min)]
                
                # Calculate trend
                first_third = grades[:len(grades)//3] if len(grades) >= 3 else grades[:1]
                last_third = grades[-len(grades)//3:] if len(grades) >= 3 else grades[-1:]
                
                first_avg = statistics.mean(first_third)
                last_avg = statistics.mean(last_third)
                
                trend_direction = 'improving' if last_avg > first_avg + 1 else 'declining' if last_avg < first_avg - 1 else 'stable'
                
                subject_trends[subject] = {
                    'trend_direction': trend_direction,
                    'change': round(last_avg - first_avg, 2),
                    'current_average': round(last_avg, 2),
                    'assignment_count': len(sub_list)
                }
        
        return subject_trends
    
    @staticmethod
    def _identify_improvement_areas(submissions: List[Submission]) -> List[Dict]:
        """Identify areas needing improvement"""
        subject_performance = defaultdict(list)
        
        for submission in submissions:
            if submission.grade is not None:
                percentage = (submission.grade / submission.assignment.max_score) * 100
                subject_performance[submission.assignment.subject].append(percentage)
        
        improvement_areas = []
        for subject, percentages in subject_performance.items():
            avg_percentage = statistics.mean(percentages)
            if avg_percentage < 75:  # Below 75% threshold
                improvement_areas.append({
                    'subject': subject,
                    'average_percentage': round(avg_percentage, 2),
                    'assignment_count': len(percentages),
                    'recommendation': f'Focus on fundamental concepts in {subject}'
                })
        
        return sorted(improvement_areas, key=lambda x: x['average_percentage'])
    
    @staticmethod
    def _identify_strengths(submissions: List[Submission]) -> List[Dict]:
        """Identify student's academic strengths"""
        subject_performance = defaultdict(list)
        
        for submission in submissions:
            if submission.grade is not None:
                percentage = (submission.grade / submission.assignment.max_score) * 100
                subject_performance[submission.assignment.subject].append(percentage)
        
        strengths = []
        for subject, percentages in subject_performance.items():
            avg_percentage = statistics.mean(percentages)
            if avg_percentage >= 85:  # Above 85% threshold
                strengths.append({
                    'subject': subject,
                    'average_percentage': round(avg_percentage, 2),
                    'assignment_count': len(percentages),
                    'note': f'Consistently strong performance in {subject}'
                })
        
        return sorted(strengths, key=lambda x: x['average_percentage'], reverse=True)


# Global instance
student_progress_service = StudentProgressService()