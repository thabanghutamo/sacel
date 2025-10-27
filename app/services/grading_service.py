"""
Advanced Grading Service for SACEL Platform
Provides sophisticated grading capabilities including rubric-based assessment,
automated scoring, peer review, and detailed feedback mechanisms
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import current_app
from sqlalchemy import func, and_
from app.extensions import db
from app.models import User, Assignment, Submission, UserRole
from app.services.redis_service import redis_service
from app.services.ai_service import AIService
import json
import statistics
import re


class RubricCriteria:
    """Represents a single criteria in a grading rubric"""
    
    def __init__(self, name: str, description: str, points: int, 
                 performance_levels: Dict[str, Dict]):
        self.name = name
        self.description = description
        self.points = points
        self.performance_levels = performance_levels  # excellent, good, satisfactory, needs_improvement
    
    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'points': self.points,
            'performance_levels': self.performance_levels
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            name=data['name'],
            description=data['description'],
            points=data['points'],
            performance_levels=data['performance_levels']
        )


class GradingRubric:
    """Represents a complete grading rubric with multiple criteria"""
    
    def __init__(self, title: str, description: str, criteria: List[RubricCriteria]):
        self.title = title
        self.description = description
        self.criteria = criteria
        self.total_points = sum(c.points for c in criteria)
    
    def to_dict(self):
        return {
            'title': self.title,
            'description': self.description,
            'criteria': [c.to_dict() for c in self.criteria],
            'total_points': self.total_points
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        criteria = [RubricCriteria.from_dict(c) for c in data['criteria']]
        return cls(
            title=data['title'],
            description=data['description'],
            criteria=criteria
        )


class GradingService:
    """Service for advanced grading functionality"""
    
    @staticmethod
    def create_default_rubrics():
        """Create default rubrics for common subjects"""
        
        # Essay Writing Rubric
        essay_criteria = [
            RubricCriteria(
                name="Content & Ideas",
                description="Quality and relevance of ideas presented",
                points=25,
                performance_levels={
                    "excellent": {
                        "description": "Exceptional insight and original thinking",
                        "points_range": [23, 25],
                        "keywords": ["original", "insightful", "comprehensive", "thorough"]
                    },
                    "good": {
                        "description": "Clear ideas with good support",
                        "points_range": [20, 22],
                        "keywords": ["clear", "supported", "relevant", "adequate"]
                    },
                    "satisfactory": {
                        "description": "Basic ideas with minimal support",
                        "points_range": [15, 19],
                        "keywords": ["basic", "simple", "unclear", "minimal"]
                    },
                    "needs_improvement": {
                        "description": "Lacks clarity and support",
                        "points_range": [0, 14],
                        "keywords": ["confused", "irrelevant", "unclear", "insufficient"]
                    }
                }
            ),
            RubricCriteria(
                name="Organization & Structure",
                description="Logical flow and organization of content",
                points=20,
                performance_levels={
                    "excellent": {
                        "description": "Clear, logical progression with smooth transitions",
                        "points_range": [18, 20],
                        "keywords": ["logical", "smooth", "coherent", "well-organized"]
                    },
                    "good": {
                        "description": "Generally well-organized with clear structure",
                        "points_range": [16, 17],
                        "keywords": ["organized", "structured", "clear progression"]
                    },
                    "satisfactory": {
                        "description": "Basic organization with some confusion",
                        "points_range": [12, 15],
                        "keywords": ["basic", "somewhat confused", "unclear structure"]
                    },
                    "needs_improvement": {
                        "description": "Poor organization, difficult to follow",
                        "points_range": [0, 11],
                        "keywords": ["disorganized", "confusing", "no clear structure"]
                    }
                }
            ),
            RubricCriteria(
                name="Language & Grammar",
                description="Proper use of language, grammar, and mechanics",
                points=20,
                performance_levels={
                    "excellent": {
                        "description": "Excellent grammar with varied sentence structure",
                        "points_range": [18, 20],
                        "keywords": ["excellent grammar", "varied sentences", "fluent"]
                    },
                    "good": {
                        "description": "Good grammar with minor errors",
                        "points_range": [16, 17],
                        "keywords": ["good grammar", "minor errors", "clear language"]
                    },
                    "satisfactory": {
                        "description": "Adequate grammar with some errors",
                        "points_range": [12, 15],
                        "keywords": ["adequate", "some errors", "basic language"]
                    },
                    "needs_improvement": {
                        "description": "Poor grammar interferes with understanding",
                        "points_range": [0, 11],
                        "keywords": ["poor grammar", "many errors", "unclear"]
                    }
                }
            ),
            RubricCriteria(
                name="Critical Thinking",
                description="Analysis, evaluation, and synthesis of information",
                points=25,
                performance_levels={
                    "excellent": {
                        "description": "Sophisticated analysis with original insights",
                        "points_range": [23, 25],
                        "keywords": ["sophisticated", "analytical", "synthesis", "evaluation"]
                    },
                    "good": {
                        "description": "Good analysis with some evaluation",
                        "points_range": [20, 22],
                        "keywords": ["analytical", "evaluative", "thoughtful"]
                    },
                    "satisfactory": {
                        "description": "Basic analysis with limited evaluation",
                        "points_range": [15, 19],
                        "keywords": ["basic analysis", "limited thinking", "surface level"]
                    },
                    "needs_improvement": {
                        "description": "Little evidence of critical thinking",
                        "points_range": [0, 14],
                        "keywords": ["no analysis", "superficial", "limited thinking"]
                    }
                }
            ),
            RubricCriteria(
                name="Use of Evidence",
                description="Quality and integration of supporting evidence",
                points=10,
                performance_levels={
                    "excellent": {
                        "description": "Strong, relevant evidence well-integrated",
                        "points_range": [9, 10],
                        "keywords": ["strong evidence", "well-integrated", "relevant sources"]
                    },
                    "good": {
                        "description": "Good evidence with adequate integration",
                        "points_range": [8, 8],
                        "keywords": ["good evidence", "adequate support"]
                    },
                    "satisfactory": {
                        "description": "Some evidence but poorly integrated",
                        "points_range": [6, 7],
                        "keywords": ["some evidence", "poorly integrated", "weak support"]
                    },
                    "needs_improvement": {
                        "description": "Little or no supporting evidence",
                        "points_range": [0, 5],
                        "keywords": ["no evidence", "unsupported", "lacking sources"]
                    }
                }
            )
        ]
        
        essay_rubric = GradingRubric(
            title="Essay Writing Rubric",
            description="Comprehensive rubric for evaluating essay assignments",
            criteria=essay_criteria
        )
        
        # Math Problem Solving Rubric
        math_criteria = [
            RubricCriteria(
                name="Problem Understanding",
                description="Demonstrates understanding of the problem",
                points=20,
                performance_levels={
                    "excellent": {
                        "description": "Complete understanding with clear problem identification",
                        "points_range": [18, 20],
                        "keywords": ["complete understanding", "identifies key elements"]
                    },
                    "good": {
                        "description": "Good understanding with minor gaps",
                        "points_range": [15, 17],
                        "keywords": ["good understanding", "mostly correct interpretation"]
                    },
                    "satisfactory": {
                        "description": "Basic understanding with some confusion",
                        "points_range": [10, 14],
                        "keywords": ["basic understanding", "some confusion"]
                    },
                    "needs_improvement": {
                        "description": "Little understanding of the problem",
                        "points_range": [0, 9],
                        "keywords": ["misunderstands", "incorrect interpretation"]
                    }
                }
            ),
            RubricCriteria(
                name="Mathematical Reasoning",
                description="Quality of mathematical thinking and logic",
                points=30,
                performance_levels={
                    "excellent": {
                        "description": "Sophisticated reasoning with clear logic",
                        "points_range": [27, 30],
                        "keywords": ["sophisticated reasoning", "clear logic", "mathematical insight"]
                    },
                    "good": {
                        "description": "Sound reasoning with minor gaps",
                        "points_range": [24, 26],
                        "keywords": ["sound reasoning", "logical approach"]
                    },
                    "satisfactory": {
                        "description": "Basic reasoning with some errors",
                        "points_range": [18, 23],
                        "keywords": ["basic reasoning", "some logical errors"]
                    },
                    "needs_improvement": {
                        "description": "Poor reasoning or major errors",
                        "points_range": [0, 17],
                        "keywords": ["poor reasoning", "major errors", "illogical"]
                    }
                }
            ),
            RubricCriteria(
                name="Solution Strategy",
                description="Appropriateness and efficiency of solution method",
                points=25,
                performance_levels={
                    "excellent": {
                        "description": "Efficient and elegant solution strategy",
                        "points_range": [23, 25],
                        "keywords": ["efficient", "elegant", "optimal strategy"]
                    },
                    "good": {
                        "description": "Appropriate strategy with good execution",
                        "points_range": [20, 22],
                        "keywords": ["appropriate strategy", "good method"]
                    },
                    "satisfactory": {
                        "description": "Workable strategy but inefficient",
                        "points_range": [15, 19],
                        "keywords": ["workable", "inefficient", "basic method"]
                    },
                    "needs_improvement": {
                        "description": "Inappropriate or no clear strategy",
                        "points_range": [0, 14],
                        "keywords": ["inappropriate", "no strategy", "random approach"]
                    }
                }
            ),
            RubricCriteria(
                name="Accuracy",
                description="Correctness of calculations and final answer",
                points=25,
                performance_levels={
                    "excellent": {
                        "description": "All calculations correct with accurate answer",
                        "points_range": [23, 25],
                        "keywords": ["accurate", "correct calculations", "right answer"]
                    },
                    "good": {
                        "description": "Mostly correct with minor calculation errors",
                        "points_range": [20, 22],
                        "keywords": ["mostly correct", "minor errors"]
                    },
                    "satisfactory": {
                        "description": "Some correct work but major errors",
                        "points_range": [12, 19],
                        "keywords": ["some correct", "major errors", "wrong answer"]
                    },
                    "needs_improvement": {
                        "description": "Mostly incorrect calculations",
                        "points_range": [0, 11],
                        "keywords": ["incorrect", "major calculation errors"]
                    }
                }
            )
        ]
        
        math_rubric = GradingRubric(
            title="Mathematics Problem Solving Rubric",
            description="Comprehensive rubric for evaluating math problem-solving assignments",
            criteria=math_criteria
        )
        
        return {
            'essay': essay_rubric,
            'mathematics': math_rubric
        }
    
    @staticmethod
    def auto_grade_submission(submission_id: int, rubric: GradingRubric) -> Dict:
        """Automatically grade a submission using AI and rubric criteria"""
        submission = Submission.query.get(submission_id)
        if not submission:
            return {'error': 'Submission not found'}
        
        # Get submission content
        content = submission.content or ""
        if not content.strip():
            return {'error': 'No content to grade'}
        
        # Use AI to analyze content against rubric criteria
        ai_service = AIService()
        
        grade_results = {}
        total_score = 0
        feedback_parts = []
        
        for criteria in rubric.criteria:
            # Create AI prompt for this criteria
            prompt = f"""
            Evaluate the following student work based on this criteria:
            
            Criteria: {criteria.name}
            Description: {criteria.description}
            Maximum Points: {criteria.points}
            
            Performance Levels:
            {json.dumps(criteria.performance_levels, indent=2)}
            
            Student Work:
            {content}
            
            Please evaluate and respond with:
            1. Performance level (excellent/good/satisfactory/needs_improvement)
            2. Score within the appropriate range
            3. Specific feedback explaining the score
            4. Suggestions for improvement
            
            Format your response as JSON with keys: level, score, feedback, suggestions
            """
            
            try:
                # Get AI evaluation
                ai_response = ai_service.generate_content(
                    prompt=prompt,
                    max_tokens=500,
                    temperature=0.3
                )
                
                # Parse AI response
                ai_evaluation = GradingService._parse_ai_evaluation(
                    ai_response, criteria
                )
                
                grade_results[criteria.name] = ai_evaluation
                total_score += ai_evaluation['score']
                
                feedback_parts.append(
                    f"{criteria.name}: {ai_evaluation['feedback']}"
                )
                
            except Exception as e:
                # Fallback to basic scoring if AI fails
                fallback_score = criteria.points * 0.7  # Default to 70%
                grade_results[criteria.name] = {
                    'level': 'satisfactory',
                    'score': fallback_score,
                    'feedback': f"Automatic evaluation unavailable. Score based on completion.",
                    'suggestions': "Please review this work manually for detailed feedback."
                }
                total_score += fallback_score
        
        # Calculate percentage
        percentage = (total_score / rubric.total_points) * 100
        
        # Generate overall feedback
        overall_feedback = GradingService._generate_overall_feedback(
            grade_results, percentage, rubric
        )
        
        # Update submission with results
        submission.grade = round(percentage, 2)
        submission.feedback = overall_feedback
        submission.status = 'graded'
        submission.graded_at = datetime.utcnow()
        
        # Store detailed rubric results
        rubric_data = {
            'rubric_title': rubric.title,
            'criteria_scores': grade_results,
            'total_score': total_score,
            'max_score': rubric.total_points,
            'percentage': percentage,
            'auto_graded': True,
            'graded_at': datetime.utcnow().isoformat()
        }
        
        # Cache detailed results
        cache_key = f"rubric_results:{submission_id}"
        redis_service.cache_data(cache_key, rubric_data, timeout=86400)  # 24 hours
        
        db.session.commit()
        
        return {
            'success': True,
            'grade': percentage,
            'feedback': overall_feedback,
            'rubric_results': rubric_data
        }
    
    @staticmethod
    def _parse_ai_evaluation(ai_response: str, criteria: RubricCriteria) -> Dict:
        """Parse AI evaluation response"""
        try:
            # Try to extract JSON from AI response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
            else:
                # Fallback parsing
                evaluation = GradingService._fallback_parse_evaluation(
                    ai_response, criteria
                )
            
            # Validate and normalize
            level = evaluation.get('level', 'satisfactory')
            if level not in criteria.performance_levels:
                level = 'satisfactory'
            
            # Get score range for this level
            score_range = criteria.performance_levels[level]['points_range']
            suggested_score = evaluation.get('score', score_range[1])
            
            # Ensure score is within valid range
            score = max(score_range[0], min(score_range[1], suggested_score))
            
            return {
                'level': level,
                'score': score,
                'feedback': evaluation.get('feedback', 'Good work overall.'),
                'suggestions': evaluation.get('suggestions', 'Keep up the good work!')
            }
            
        except Exception as e:
            # Fallback to middle performance level
            level = 'satisfactory'
            score_range = criteria.performance_levels[level]['points_range']
            return {
                'level': level,
                'score': score_range[1],
                'feedback': f"Evaluation completed. Consider reviewing {criteria.name}.",
                'suggestions': f"Focus on improving {criteria.description.lower()}."
            }
    
    @staticmethod
    def _fallback_parse_evaluation(response: str, criteria: RubricCriteria) -> Dict:
        """Fallback method to parse evaluation when JSON parsing fails"""
        response_lower = response.lower()
        
        # Determine performance level based on keywords
        level = 'satisfactory'
        for perf_level, data in criteria.performance_levels.items():
            keywords = data.get('keywords', [])
            if any(keyword.lower() in response_lower for keyword in keywords):
                level = perf_level
                break
        
        # Extract score if mentioned
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:points?|/)', response)
        if score_match:
            score = float(score_match.group(1))
        else:
            # Use middle of range for determined level
            score_range = criteria.performance_levels[level]['points_range']
            score = (score_range[0] + score_range[1]) / 2
        
        return {
            'level': level,
            'score': score,
            'feedback': response[:200] + '...' if len(response) > 200 else response,
            'suggestions': 'Continue to develop your skills in this area.'
        }
    
    @staticmethod
    def _generate_overall_feedback(grade_results: Dict, percentage: float, 
                                 rubric: GradingRubric) -> str:
        """Generate comprehensive overall feedback"""
        feedback_parts = ["=== GRADING FEEDBACK ===\n"]
        
        # Overall performance
        if percentage >= 90:
            feedback_parts.append("🌟 Excellent work! You've demonstrated mastery of the material.")
        elif percentage >= 80:
            feedback_parts.append("👍 Good work! You show strong understanding with room for refinement.")
        elif percentage >= 70:
            feedback_parts.append("✓ Satisfactory work. You meet basic requirements but can improve further.")
        else:
            feedback_parts.append("⚠️ This work needs improvement. Please review the feedback below.")
        
        feedback_parts.append(f"\nOverall Score: {percentage:.1f}%\n")
        
        # Criteria-specific feedback
        feedback_parts.append("=== DETAILED FEEDBACK BY CRITERIA ===\n")
        
        strengths = []
        improvements = []
        
        for criteria_name, results in grade_results.items():
            criteria_feedback = f"{criteria_name}: {results['score']:.1f} points"
            feedback_parts.append(criteria_feedback)
            feedback_parts.append(f"  {results['feedback']}")
            
            if results['level'] in ['excellent', 'good']:
                strengths.append(criteria_name)
            elif results['level'] == 'needs_improvement':
                improvements.append(criteria_name)
            
            feedback_parts.append(f"  💡 Suggestion: {results['suggestions']}\n")
        
        # Summary of strengths and areas for improvement
        if strengths:
            feedback_parts.append(f"🎯 STRENGTHS: {', '.join(strengths)}")
        
        if improvements:
            feedback_parts.append(f"📈 FOCUS AREAS: {', '.join(improvements)}")
        
        feedback_parts.append("\n=== NEXT STEPS ===")
        feedback_parts.append("Review the specific feedback for each criteria above.")
        feedback_parts.append("Focus on the areas marked for improvement.")
        feedback_parts.append("Don't hesitate to ask your teacher for clarification or additional help.")
        
        return "\n".join(feedback_parts)
    
    @staticmethod
    def get_rubric_results(submission_id: int) -> Optional[Dict]:
        """Get detailed rubric results for a submission"""
        cache_key = f"rubric_results:{submission_id}"
        return redis_service.get_cached_data(cache_key)
    
    @staticmethod
    def create_peer_review_assignment(assignment_id: int, review_criteria: List[str],
                                    reviews_per_student: int = 2) -> Dict:
        """Create peer review assignments for students"""
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return {'error': 'Assignment not found'}
        
        # Get all submissions for this assignment
        submissions = Submission.query.filter_by(
            assignment_id=assignment_id,
            status='submitted'
        ).all()
        
        if len(submissions) < 2:
            return {'error': 'Need at least 2 submissions for peer review'}
        
        # Create peer review pairings
        pairings = GradingService._create_peer_review_pairings(
            submissions, reviews_per_student
        )
        
        # Store peer review data
        peer_review_data = {
            'assignment_id': assignment_id,
            'criteria': review_criteria,
            'pairings': pairings,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        cache_key = f"peer_review:{assignment_id}"
        redis_service.cache_data(cache_key, peer_review_data, timeout=604800)  # 1 week
        
        return {
            'success': True,
            'peer_review_id': assignment_id,
            'pairings_count': len(pairings),
            'criteria': review_criteria
        }
    
    @staticmethod
    def _create_peer_review_pairings(submissions: List[Submission], 
                                   reviews_per_student: int) -> List[Dict]:
        """Create balanced peer review pairings"""
        import random
        
        student_ids = [s.student_id for s in submissions]
        submission_map = {s.student_id: s.id for s in submissions}
        
        pairings = []
        
        for student_id in student_ids:
            # Get other students (exclude self)
            other_students = [sid for sid in student_ids if sid != student_id]
            
            # Randomly select students to review
            reviewees = random.sample(
                other_students, 
                min(reviews_per_student, len(other_students))
            )
            
            for reviewee_id in reviewees:
                pairings.append({
                    'reviewer_id': student_id,
                    'reviewee_id': reviewee_id,
                    'submission_id': submission_map[reviewee_id],
                    'status': 'pending',
                    'assigned_at': datetime.utcnow().isoformat()
                })
        
        return pairings
    
    @staticmethod
    def submit_peer_review(reviewer_id: int, submission_id: int, 
                          review_data: Dict) -> Dict:
        """Submit a peer review"""
        # Validate review data
        required_fields = ['ratings', 'comments', 'overall_score']
        if not all(field in review_data for field in required_fields):
            return {'error': 'Missing required review fields'}
        
        # Store peer review
        peer_review = {
            'reviewer_id': reviewer_id,
            'submission_id': submission_id,
            'ratings': review_data['ratings'],
            'comments': review_data['comments'],
            'overall_score': review_data['overall_score'],
            'submitted_at': datetime.utcnow().isoformat(),
            'status': 'completed'
        }
        
        cache_key = f"peer_review_submission:{reviewer_id}:{submission_id}"
        redis_service.cache_data(cache_key, peer_review, timeout=604800)  # 1 week
        
        return {
            'success': True,
            'message': 'Peer review submitted successfully'
        }
    
    @staticmethod
    def calculate_final_grade(submission_id: int, include_peer_reviews: bool = True) -> Dict:
        """Calculate final grade incorporating peer reviews and rubric scores"""
        submission = Submission.query.get(submission_id)
        if not submission:
            return {'error': 'Submission not found'}
        
        # Get rubric results
        rubric_results = GradingService.get_rubric_results(submission_id)
        
        if not rubric_results:
            return {'error': 'No grading data available'}
        
        base_score = rubric_results['percentage']
        final_score = base_score
        
        if include_peer_reviews:
            # Get peer review scores
            peer_scores = GradingService._get_peer_review_scores(submission_id)
            
            if peer_scores:
                # Weight: 80% rubric, 20% peer reviews
                peer_average = statistics.mean(peer_scores)
                final_score = (base_score * 0.8) + (peer_average * 0.2)
        
        # Update submission with final grade
        submission.grade = round(final_score, 2)
        db.session.commit()
        
        return {
            'success': True,
            'base_score': base_score,
            'peer_scores': peer_scores if include_peer_reviews else [],
            'final_score': final_score,
            'grade_breakdown': {
                'rubric_weight': 0.8 if include_peer_reviews else 1.0,
                'peer_review_weight': 0.2 if include_peer_reviews else 0.0
            }
        }
    
    @staticmethod
    def _get_peer_review_scores(submission_id: int) -> List[float]:
        """Get peer review scores for a submission"""
        # This would typically query a peer_reviews table
        # For now, simulate getting cached peer review data
        scores = []
        
        # Try to find peer reviews in cache
        for i in range(10):  # Check up to 10 possible reviewers
            cache_key = f"peer_review_submission:{i}:{submission_id}"
            review_data = redis_service.get_cached_data(cache_key)
            if review_data:
                scores.append(review_data.get('overall_score', 0))
        
        return scores
    
    @staticmethod
    def generate_grade_report(submission_id: int) -> Dict:
        """Generate comprehensive grade report"""
        submission = Submission.query.get(submission_id)
        if not submission:
            return {'error': 'Submission not found'}
        
        # Get all grading data
        rubric_results = GradingService.get_rubric_results(submission_id)
        final_grade_data = GradingService.calculate_final_grade(submission_id)
        
        # Get student and assignment info
        student = User.query.get(submission.student_id)
        assignment = submission.assignment
        
        report = {
            'student_name': student.full_name,
            'assignment_title': assignment.title,
            'subject': assignment.subject,
            'submission_date': submission.submitted_at.isoformat() if submission.submitted_at else None,
            'graded_date': submission.graded_at.isoformat() if submission.graded_at else None,
            'final_grade': submission.grade,
            'grade_letter': GradingService._get_letter_grade(submission.grade),
            'rubric_results': rubric_results,
            'final_grade_breakdown': final_grade_data,
            'feedback': submission.feedback,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    @staticmethod
    def _get_letter_grade(percentage: float) -> str:
        """Convert percentage to letter grade"""
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'


# Utility functions for grading system
def invalidate_grading_cache(submission_id: int = None, assignment_id: int = None):
    """Invalidate grading-related cache"""
    patterns = []
    
    if submission_id:
        patterns.extend([
            f"rubric_results:{submission_id}",
            f"peer_review_submission:*:{submission_id}"
        ])
    
    if assignment_id:
        patterns.append(f"peer_review:{assignment_id}")
    
    for pattern in patterns:
        redis_service.delete_pattern(pattern)


def export_grades_to_csv(assignment_id: int) -> str:
    """Export assignment grades to CSV format"""
    assignment = Assignment.query.get(assignment_id)
    if not assignment:
        return "Assignment not found"
    
    submissions = Submission.query.filter_by(
        assignment_id=assignment_id,
        status='graded'
    ).all()
    
    csv_lines = ["Student Name,Email,Grade,Letter Grade,Submission Date,Graded Date"]
    
    for submission in submissions:
        student = User.query.get(submission.student_id)
        letter_grade = GradingService._get_letter_grade(submission.grade)
        
        csv_lines.append(
            f'"{student.full_name}",{student.email},{submission.grade},'
            f'{letter_grade},{submission.submitted_at},{submission.graded_at}'
        )
    
    return "\n".join(csv_lines)


# Global instance
grading_service = GradingService()