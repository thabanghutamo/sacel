"""
Advanced Assignment Features Service for SACEL Platform
Provides multimedia support, collaboration, peer review, and plagiarism detection
"""

from flask import current_app
from sqlalchemy import desc, and_, or_
from app.extensions import db
from app.models import User, Assignment, Submission, Teacher, Student
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import hashlib
import difflib
import re
from collections import defaultdict
import statistics


class AdvancedAssignmentService:
    """Service for advanced assignment features"""
    
    @staticmethod
    def create_multimedia_assignment(teacher_id: int, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create assignment with multimedia support"""
        try:
            # Validate teacher permissions
            teacher = User.query.get(teacher_id)
            if not teacher or teacher.role.value != 'teacher':
                return {'error': 'Invalid teacher credentials'}
            
            # Create assignment with enhanced features
            assignment = Assignment(
                title=assignment_data.get('title'),
                description=assignment_data.get('description'),
                subject=assignment_data.get('subject'),
                grade_level=assignment_data.get('grade_level'),
                teacher_id=teacher_id,
                instructions=assignment_data.get('instructions'),
                due_date=datetime.fromisoformat(assignment_data.get('due_date')),
                max_score=assignment_data.get('max_score', 100)
            )
            
            # Add multimedia content
            multimedia_content = {
                'attachments': assignment_data.get('attachments', []),
                'embedded_videos': assignment_data.get('embedded_videos', []),
                'interactive_elements': assignment_data.get('interactive_elements', []),
                'resource_links': assignment_data.get('resource_links', []),
                'submission_types': assignment_data.get('submission_types', ['text']),
                'collaboration_settings': {
                    'allow_collaboration': assignment_data.get('allow_collaboration', False),
                    'max_collaborators': assignment_data.get('max_collaborators', 3),
                    'collaboration_deadline': assignment_data.get('collaboration_deadline')
                },
                'peer_review_settings': {
                    'enable_peer_review': assignment_data.get('enable_peer_review', False),
                    'reviews_per_student': assignment_data.get('reviews_per_student', 2),
                    'peer_review_deadline': assignment_data.get('peer_review_deadline'),
                    'anonymous_reviews': assignment_data.get('anonymous_reviews', True)
                },
                'plagiarism_detection': {
                    'enabled': assignment_data.get('plagiarism_detection', True),
                    'similarity_threshold': assignment_data.get('similarity_threshold', 80),
                    'check_internet': assignment_data.get('check_internet', False),
                    'check_internal': assignment_data.get('check_internal', True)
                }
            }
            
            assignment.ai_generated_content = json.dumps(multimedia_content)
            
            db.session.add(assignment)
            db.session.commit()
            
            return {
                'assignment_id': assignment.id,
                'title': assignment.title,
                'features_enabled': {
                    'multimedia': len(multimedia_content['attachments']) > 0,
                    'collaboration': multimedia_content['collaboration_settings']['allow_collaboration'],
                    'peer_review': multimedia_content['peer_review_settings']['enable_peer_review'],
                    'plagiarism_detection': multimedia_content['plagiarism_detection']['enabled']
                },
                'created_at': assignment.created_at.isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error creating multimedia assignment: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to create assignment'}
    
    @staticmethod
    def submit_collaborative_assignment(submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle collaborative assignment submissions"""
        try:
            assignment_id = submission_data.get('assignment_id')
            student_ids = submission_data.get('student_ids', [])
            content = submission_data.get('content')
            attachments = submission_data.get('attachments', [])
            
            # Validate assignment supports collaboration
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return {'error': 'Assignment not found'}
            
            assignment_settings = json.loads(assignment.ai_generated_content or '{}')
            collab_settings = assignment_settings.get('collaboration_settings', {})
            
            if not collab_settings.get('allow_collaboration', False):
                return {'error': 'Collaboration not allowed for this assignment'}
            
            if len(student_ids) > collab_settings.get('max_collaborators', 3):
                return {'error': 'Too many collaborators'}
            
            # Create collaborative submission group
            group_id = f"collab_{assignment_id}_{datetime.utcnow().timestamp()}"
            
            submissions = []
            for student_id in student_ids:
                # Check if student already has a submission
                existing = Submission.query.filter_by(
                    assignment_id=assignment_id,
                    student_id=student_id
                ).first()
                
                if existing:
                    return {'error': f'Student {student_id} already has a submission'}
                
                submission = Submission(
                    assignment_id=assignment_id,
                    student_id=student_id,
                    content=content,
                    status='submitted',
                    submitted_at=datetime.utcnow()
                )
                
                # Add collaboration metadata
                collaboration_data = {
                    'is_collaborative': True,
                    'group_id': group_id,
                    'collaborators': student_ids,
                    'attachments': attachments,
                    'submission_type': submission_data.get('submission_type', 'text')
                }
                
                if submission.attachment_url:
                    submission.attachment_url = json.dumps(collaboration_data)
                else:
                    submission.attachment_url = json.dumps(collaboration_data)
                
                submissions.append(submission)
                db.session.add(submission)
            
            db.session.commit()
            
            # Check for plagiarism if enabled
            plagiarism_results = []
            if assignment_settings.get('plagiarism_detection', {}).get('enabled', True):
                plagiarism_results = AdvancedAssignmentService.check_plagiarism(
                    assignment_id, content, group_id
                )
            
            return {
                'group_id': group_id,
                'submissions_created': len(submissions),
                'collaborators': student_ids,
                'plagiarism_check': plagiarism_results,
                'submitted_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error in collaborative submission: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to submit collaborative assignment'}
    
    @staticmethod
    def check_plagiarism(assignment_id: int, content: str, exclude_group_id: str = None) -> Dict[str, Any]:
        """Advanced plagiarism detection system"""
        try:
            # Get all submissions for this assignment
            submissions_query = Submission.query.filter(
                Submission.assignment_id == assignment_id,
                Submission.content.isnot(None)
            )
            
            # Exclude current group from plagiarism check
            if exclude_group_id:
                submissions_query = submissions_query.filter(
                    ~Submission.attachment_url.contains(exclude_group_id)
                )
            
            existing_submissions = submissions_query.all()
            
            plagiarism_results = {
                'overall_similarity': 0,
                'suspicious_matches': [],
                'flagged': False,
                'checked_against': len(existing_submissions),
                'analysis_details': {}
            }
            
            if not existing_submissions:
                return plagiarism_results
            
            # Preprocess content for comparison
            clean_content = AdvancedAssignmentService._preprocess_text(content)
            
            similarities = []
            for submission in existing_submissions:
                if not submission.content:
                    continue
                    
                clean_existing = AdvancedAssignmentService._preprocess_text(submission.content)
                
                # Calculate similarity using different methods
                char_similarity = AdvancedAssignmentService._calculate_character_similarity(
                    clean_content, clean_existing
                )
                word_similarity = AdvancedAssignmentService._calculate_word_similarity(
                    clean_content, clean_existing
                )
                phrase_similarity = AdvancedAssignmentService._calculate_phrase_similarity(
                    clean_content, clean_existing
                )
                
                overall_similarity = (char_similarity + word_similarity + phrase_similarity) / 3
                
                if overall_similarity > 0.3:  # 30% threshold for reporting
                    similarities.append({
                        'submission_id': submission.id,
                        'student_id': submission.student_id,
                        'similarity_score': round(overall_similarity * 100, 2),
                        'character_similarity': round(char_similarity * 100, 2),
                        'word_similarity': round(word_similarity * 100, 2),
                        'phrase_similarity': round(phrase_similarity * 100, 2),
                        'matching_phrases': AdvancedAssignmentService._find_matching_phrases(
                            clean_content, clean_existing
                        )
                    })
            
            if similarities:
                plagiarism_results['overall_similarity'] = max(s['similarity_score'] for s in similarities)
                plagiarism_results['suspicious_matches'] = sorted(
                    similarities, key=lambda x: x['similarity_score'], reverse=True
                )
                
                # Flag if high similarity detected
                if plagiarism_results['overall_similarity'] > 80:
                    plagiarism_results['flagged'] = True
            
            # Additional analysis
            plagiarism_results['analysis_details'] = {
                'content_length': len(content),
                'unique_words': len(set(clean_content.split())),
                'readability_score': AdvancedAssignmentService._calculate_readability(content),
                'writing_patterns': AdvancedAssignmentService._analyze_writing_patterns(content)
            }
            
            return plagiarism_results
            
        except Exception as e:
            current_app.logger.error(f"Error in plagiarism check: {str(e)}")
            return {'error': 'Plagiarism check failed'}
    
    @staticmethod
    def create_peer_review_assignments(assignment_id: int) -> Dict[str, Any]:
        """Create peer review assignments for submitted work"""
        try:
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return {'error': 'Assignment not found'}
            
            # Get assignment settings
            assignment_settings = json.loads(assignment.ai_generated_content or '{}')
            peer_review_settings = assignment_settings.get('peer_review_settings', {})
            
            if not peer_review_settings.get('enable_peer_review', False):
                return {'error': 'Peer review not enabled for this assignment'}
            
            # Get all submitted work
            submissions = Submission.query.filter(
                Submission.assignment_id == assignment_id,
                Submission.status == 'submitted'
            ).all()
            
            if len(submissions) < 2:
                return {'error': 'Not enough submissions for peer review'}
            
            reviews_per_student = peer_review_settings.get('reviews_per_student', 2)
            peer_assignments = []
            
            # Create review assignments using round-robin approach
            for i, submission in enumerate(submissions):
                reviewers = []
                for j in range(reviews_per_student):
                    reviewer_index = (i + j + 1) % len(submissions)
                    if reviewer_index != i:  # Don't assign self-review
                        reviewers.append(submissions[reviewer_index].student_id)
                
                peer_assignments.append({
                    'submission_id': submission.id,
                    'author_id': submission.student_id,
                    'reviewers': reviewers
                })
            
            # Store peer review assignments
            peer_review_data = {
                'assignments': peer_assignments,
                'created_at': datetime.utcnow().isoformat(),
                'deadline': peer_review_settings.get('peer_review_deadline'),
                'anonymous': peer_review_settings.get('anonymous_reviews', True)
            }
            
            # Update assignment with peer review data
            assignment_settings['peer_review_data'] = peer_review_data
            assignment.ai_generated_content = json.dumps(assignment_settings)
            db.session.commit()
            
            return {
                'peer_assignments_created': len(peer_assignments),
                'total_reviews_to_complete': sum(len(pa['reviewers']) for pa in peer_assignments),
                'deadline': peer_review_settings.get('peer_review_deadline'),
                'anonymous_reviews': peer_review_settings.get('anonymous_reviews', True)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error creating peer review assignments: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to create peer review assignments'}
    
    @staticmethod
    def submit_peer_review(review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a peer review"""
        try:
            submission_id = review_data.get('submission_id')
            reviewer_id = review_data.get('reviewer_id')
            scores = review_data.get('scores', {})
            comments = review_data.get('comments', '')
            suggestions = review_data.get('suggestions', '')
            
            # Validate submission exists
            submission = Submission.query.get(submission_id)
            if not submission:
                return {'error': 'Submission not found'}
            
            # Get assignment and peer review settings
            assignment = Assignment.query.get(submission.assignment_id)
            assignment_settings = json.loads(assignment.ai_generated_content or '{}')
            peer_review_data = assignment_settings.get('peer_review_data', {})
            
            # Validate reviewer is assigned to this submission
            assigned_reviewers = []
            for pa in peer_review_data.get('assignments', []):
                if pa['submission_id'] == submission_id:
                    assigned_reviewers = pa['reviewers']
                    break
            
            if reviewer_id not in assigned_reviewers:
                return {'error': 'You are not assigned to review this submission'}
            
            # Create peer review record
            peer_review = {
                'submission_id': submission_id,
                'reviewer_id': reviewer_id,
                'scores': scores,
                'comments': comments,
                'suggestions': suggestions,
                'submitted_at': datetime.utcnow().isoformat(),
                'anonymous': assignment_settings.get('peer_review_settings', {}).get('anonymous_reviews', True)
            }
            
            # Store review in assignment metadata
            if 'peer_reviews' not in assignment_settings:
                assignment_settings['peer_reviews'] = []
            
            # Remove any existing review from this reviewer for this submission
            assignment_settings['peer_reviews'] = [
                r for r in assignment_settings['peer_reviews']
                if not (r['submission_id'] == submission_id and r['reviewer_id'] == reviewer_id)
            ]
            
            assignment_settings['peer_reviews'].append(peer_review)
            assignment.ai_generated_content = json.dumps(assignment_settings)
            db.session.commit()
            
            # Calculate review summary
            submission_reviews = [
                r for r in assignment_settings['peer_reviews']
                if r['submission_id'] == submission_id
            ]
            
            return {
                'review_submitted': True,
                'submission_id': submission_id,
                'reviews_completed': len(submission_reviews),
                'average_scores': AdvancedAssignmentService._calculate_average_scores(submission_reviews),
                'submitted_at': peer_review['submitted_at']
            }
            
        except Exception as e:
            current_app.logger.error(f"Error submitting peer review: {str(e)}")
            db.session.rollback()
            return {'error': 'Failed to submit peer review'}
    
    @staticmethod
    def get_assignment_analytics(assignment_id: int) -> Dict[str, Any]:
        """Get comprehensive analytics for an assignment"""
        try:
            assignment = Assignment.query.get(assignment_id)
            if not assignment:
                return {'error': 'Assignment not found'}
            
            submissions = Submission.query.filter_by(assignment_id=assignment_id).all()
            assignment_settings = json.loads(assignment.ai_generated_content or '{}')
            
            # Basic statistics
            total_submissions = len(submissions)
            graded_submissions = [s for s in submissions if s.grade is not None]
            submitted_count = len([s for s in submissions if s.status == 'submitted'])
            draft_count = len([s for s in submissions if s.status == 'draft'])
            
            # Grade statistics
            grade_stats = {}
            if graded_submissions:
                grades = [s.grade for s in graded_submissions]
                grade_stats = {
                    'average': round(statistics.mean(grades), 2),
                    'median': round(statistics.median(grades), 2),
                    'highest': max(grades),
                    'lowest': min(grades),
                    'std_deviation': round(statistics.stdev(grades) if len(grades) > 1 else 0, 2)
                }
            
            # Submission timeline
            submission_timeline = []
            for submission in submissions:
                if submission.submitted_at:
                    submission_timeline.append({
                        'date': submission.submitted_at.strftime('%Y-%m-%d'),
                        'count': 1
                    })
            
            # Group by date
            timeline_grouped = defaultdict(int)
            for entry in submission_timeline:
                timeline_grouped[entry['date']] += entry['count']
            
            submission_timeline = [
                {'date': date, 'count': count}
                for date, count in sorted(timeline_grouped.items())
            ]
            
            # Collaboration analysis
            collaboration_stats = {
                'collaborative_submissions': 0,
                'individual_submissions': 0,
                'average_collaborators': 0
            }
            
            if assignment_settings.get('collaboration_settings', {}).get('allow_collaboration'):
                collab_submissions = []
                for submission in submissions:
                    if submission.attachment_url:
                        try:
                            metadata = json.loads(submission.attachment_url)
                            if metadata.get('is_collaborative'):
                                collab_submissions.append(len(metadata.get('collaborators', [])))
                                collaboration_stats['collaborative_submissions'] += 1
                            else:
                                collaboration_stats['individual_submissions'] += 1
                        except:
                            collaboration_stats['individual_submissions'] += 1
                    else:
                        collaboration_stats['individual_submissions'] += 1
                
                if collab_submissions:
                    collaboration_stats['average_collaborators'] = round(
                        statistics.mean(collab_submissions), 2
                    )
            
            # Peer review analysis
            peer_review_stats = {}
            if assignment_settings.get('peer_review_settings', {}).get('enable_peer_review'):
                peer_reviews = assignment_settings.get('peer_reviews', [])
                peer_review_stats = {
                    'total_reviews': len(peer_reviews),
                    'unique_reviewers': len(set(r['reviewer_id'] for r in peer_reviews)),
                    'average_review_scores': AdvancedAssignmentService._calculate_average_scores(peer_reviews),
                    'reviews_per_submission': round(
                        len(peer_reviews) / max(submitted_count, 1), 2
                    )
                }
            
            # Plagiarism summary
            plagiarism_stats = {
                'checks_performed': 0,
                'flagged_submissions': 0,
                'average_similarity': 0
            }
            
            if assignment_settings.get('plagiarism_detection', {}).get('enabled'):
                # This would be populated from stored plagiarism check results
                # For now, return placeholder data
                plagiarism_stats['checks_performed'] = submitted_count
            
            return {
                'assignment_info': {
                    'id': assignment.id,
                    'title': assignment.title,
                    'subject': assignment.subject,
                    'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                    'max_score': assignment.max_score
                },
                'submission_stats': {
                    'total_submissions': total_submissions,
                    'submitted': submitted_count,
                    'graded': len(graded_submissions),
                    'drafts': draft_count,
                    'completion_rate': round(submitted_count / max(total_submissions, 1) * 100, 2)
                },
                'grade_statistics': grade_stats,
                'submission_timeline': submission_timeline,
                'collaboration_analytics': collaboration_stats,
                'peer_review_analytics': peer_review_stats,
                'plagiarism_analytics': plagiarism_stats,
                'features_enabled': {
                    'multimedia': len(assignment_settings.get('attachments', [])) > 0,
                    'collaboration': assignment_settings.get('collaboration_settings', {}).get('allow_collaboration', False),
                    'peer_review': assignment_settings.get('peer_review_settings', {}).get('enable_peer_review', False),
                    'plagiarism_detection': assignment_settings.get('plagiarism_detection', {}).get('enabled', False)
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting assignment analytics: {str(e)}")
            return {'error': 'Failed to get assignment analytics'}
    
    # Helper methods for plagiarism detection
    @staticmethod
    def _preprocess_text(text: str) -> str:
        """Preprocess text for plagiarism analysis"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip().lower())
        # Remove common punctuation
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    @staticmethod
    def _calculate_character_similarity(text1: str, text2: str) -> float:
        """Calculate character-level similarity"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    @staticmethod
    def _calculate_word_similarity(text1: str, text2: str) -> float:
        """Calculate word-level similarity"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def _calculate_phrase_similarity(text1: str, text2: str, phrase_length: int = 5) -> float:
        """Calculate similarity based on common phrases"""
        words1 = text1.split()
        words2 = text2.split()
        
        if len(words1) < phrase_length or len(words2) < phrase_length:
            return 0.0
        
        phrases1 = set()
        phrases2 = set()
        
        for i in range(len(words1) - phrase_length + 1):
            phrases1.add(' '.join(words1[i:i + phrase_length]))
        
        for i in range(len(words2) - phrase_length + 1):
            phrases2.add(' '.join(words2[i:i + phrase_length]))
        
        if not phrases1 and not phrases2:
            return 1.0
        if not phrases1 or not phrases2:
            return 0.0
        
        intersection = len(phrases1.intersection(phrases2))
        union = len(phrases1.union(phrases2))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def _find_matching_phrases(text1: str, text2: str, min_length: int = 10) -> List[str]:
        """Find matching phrases between texts"""
        words1 = text1.split()
        words2 = text2.split()
        
        matching_phrases = []
        
        for length in range(min_length, min(len(words1), len(words2)) + 1):
            for i in range(len(words1) - length + 1):
                phrase = ' '.join(words1[i:i + length])
                if phrase in text2:
                    matching_phrases.append(phrase)
        
        return list(set(matching_phrases))
    
    @staticmethod
    def _calculate_readability(text: str) -> float:
        """Simple readability score calculation"""
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum(AdvancedAssignmentService._count_syllables(word) for word in text.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simplified Flesch Reading Ease score
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0, min(100, score))
    
    @staticmethod
    def _count_syllables(word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    @staticmethod
    def _analyze_writing_patterns(text: str) -> Dict[str, Any]:
        """Analyze writing patterns for plagiarism detection"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words:
            return {}
        
        return {
            'average_word_length': round(sum(len(word) for word in words) / len(words), 2),
            'average_sentence_length': round(len(words) / max(len(sentences), 1), 2),
            'vocabulary_diversity': round(len(set(words)) / len(words), 2),
            'complex_words': len([word for word in words if len(word) > 6]) / len(words)
        }
    
    @staticmethod
    def _calculate_average_scores(reviews: List[Dict]) -> Dict[str, float]:
        """Calculate average scores from peer reviews"""
        if not reviews:
            return {}
        
        all_scores = defaultdict(list)
        for review in reviews:
            scores = review.get('scores', {})
            for criterion, score in scores.items():
                all_scores[criterion].append(score)
        
        return {
            criterion: round(statistics.mean(scores), 2)
            for criterion, scores in all_scores.items()
        }


# Global service instance
advanced_assignment_service = AdvancedAssignmentService()