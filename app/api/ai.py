"""
AI Service API endpoints for SACEL
Provides AI-powered educational features including assignment generation, grading, and content assistance
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.services.ai_service import ai_service
from app.models import User, UserRole
from app.extensions import db
import json

bp = Blueprint('ai', __name__)

def require_teacher_or_admin():
    """Decorator to require teacher, admin, or principal access"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    allowed_roles = [UserRole.TEACHER, UserRole.SCHOOL_ADMIN, UserRole.PRINCIPAL, UserRole.SYSTEM_ADMIN]
    if current_user.role not in allowed_roles:
        return jsonify({'error': 'Insufficient permissions'}), 403
    
    return None

@bp.route('/generate-assignment', methods=['POST'])
@login_required
def generate_assignment():
    """Generate an AI-powered assignment"""
    error = require_teacher_or_admin()
    if error:
        return error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['subject', 'grade', 'topic', 'assignment_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        subject = data['subject']
        grade = int(data['grade'])
        topic = data['topic']
        assignment_type = data['assignment_type']
        difficulty = data.get('difficulty', 'medium')
        
        # Validate inputs
        if grade < 1 or grade > 12:
            return jsonify({'error': 'Grade must be between 1 and 12'}), 400
        
        if assignment_type not in ['quiz', 'test', 'homework', 'project', 'exam']:
            return jsonify({'error': 'Invalid assignment type'}), 400
        
        # Generate assignment using AI
        current_app.logger.info(f"Generating {assignment_type} for {subject} Grade {grade}: {topic}")
        
        assignment = ai_service.generate_assignment(
            subject=subject,
            grade=grade,
            topic=topic,
            assignment_type=assignment_type,
            difficulty=difficulty
        )
        
        if not assignment:
            return jsonify({'error': 'Failed to generate assignment'}), 500
        
        # Add metadata
        assignment['metadata'] = {
            'created_by': current_user.id,
            'teacher_name': current_user.full_name,
            'subject': subject,
            'grade': grade,
            'topic': topic,
            'difficulty': difficulty,
            'assignment_type': assignment_type
        }
        
        return jsonify({
            'success': True,
            'assignment': assignment
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f"Assignment generation error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/grade-assignment', methods=['POST'])
@login_required
def grade_assignment():
    """Grade an assignment using AI assistance"""
    error = require_teacher_or_admin()
    if error:
        return error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['questions', 'answers', 'assignment_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        questions = data['questions']
        answers = data['answers']
        assignment_type = data['assignment_type']
        
        # Validate that questions and answers match
        if len(questions) != len(answers):
            return jsonify({'error': 'Number of questions and answers must match'}), 400
        
        # Grade using AI
        current_app.logger.info(f"Grading {assignment_type} with {len(questions)} questions")
        
        result = ai_service.grade_assignment(
            questions=questions,
            answers=answers,
            assignment_type=assignment_type
        )
        
        if not result:
            return jsonify({'error': 'Failed to grade assignment'}), 500
        
        # Add metadata
        result['metadata'] = {
            'graded_by': current_user.id,
            'teacher_name': current_user.full_name,
            'assignment_type': assignment_type,
            'num_questions': len(questions)
        }
        
        return jsonify({
            'success': True,
            'grading_result': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Assignment grading error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/check-plagiarism', methods=['POST'])
@login_required
def check_plagiarism():
    """Check for plagiarism in student submissions"""
    error = require_teacher_or_admin()
    if error:
        return error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'student_text' not in data:
            return jsonify({'error': 'Missing student_text field'}), 400
        
        student_text = data['student_text']
        reference_texts = data.get('reference_texts', [])
        
        if len(student_text.strip()) < 50:
            return jsonify({'error': 'Student text too short for plagiarism analysis'}), 400
        
        # Check plagiarism using AI
        current_app.logger.info(f"Checking plagiarism for text of length {len(student_text)}")
        
        result = ai_service.detect_plagiarism(
            student_text=student_text,
            reference_texts=reference_texts
        )
        
        if not result:
            return jsonify({'error': 'Failed to analyze plagiarism'}), 500
        
        return jsonify({
            'success': True,
            'plagiarism_analysis': result
        })
        
    except Exception as e:
        current_app.logger.error(f"Plagiarism check error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/search-library', methods=['POST'])
@login_required
def search_library():
    """Search library content using AI semantic search"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'query' not in data:
            return jsonify({'error': 'Missing query field'}), 400
        
        query = data['query']
        library_content = data.get('library_content', [])
        
        if len(query.strip()) < 3:
            return jsonify({'error': 'Search query too short'}), 400
        
        # Search using AI
        current_app.logger.info(f"Searching library for: {query}")
        
        results = ai_service.search_library(
            query=query,
            library_content=library_content
        )
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results
        })
        
    except Exception as e:
        current_app.logger.error(f"Library search error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/translate-content', methods=['POST'])
@login_required
def translate_content():
    """Translate content to South African official languages"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['text', 'target_language']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        text = data['text']
        target_language = data['target_language']
        
        if len(text.strip()) < 10:
            return jsonify({'error': 'Text too short for translation'}), 400
        
        # Translate using AI
        current_app.logger.info(f"Translating to {target_language}")
        
        translated_text = ai_service.translate_content(
            text=text,
            target_language=target_language
        )
        
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'target_language': target_language
        })
        
    except Exception as e:
        current_app.logger.error(f"Translation error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/generate-content', methods=['POST'])
@login_required
def generate_content():
    """Generate various types of educational content using AI"""
    error = require_teacher_or_admin()
    if error:
        return error
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content_type = data.get('content_type', 'instructions')
        subject = data.get('subject')
        grade = data.get('grade')
        topic = data.get('topic')
        title = data.get('title', '')
        existing_instructions = data.get('existing_instructions', '')
        assignment_type = data.get('assignment_type', 'homework')
        language = data.get('language', 'english')
        
        # Validate required fields
        if not all([subject, grade, topic]):
            return jsonify({'error': 'Subject, grade, and topic are required'}), 400
        
        current_app.logger.info(f"Generating {content_type} for {subject} Grade {grade}: {topic}")
        
        if content_type == 'rubric':
            result = generate_grading_rubric(subject, grade, topic, assignment_type, language)
        elif content_type == 'instructions':
            result = enhance_instructions(subject, grade, topic, title, existing_instructions, language)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        if not result:
            return jsonify({'error': f'Failed to generate {content_type}'}), 500
        
        response_data = {
            'success': True,
            'content_type': content_type,
            'metadata': {
                'created_by': current_user.id,
                'teacher_name': current_user.full_name,
                'subject': subject,
                'grade': grade,
                'topic': topic,
                'language': language
            }
        }
        
        # Add content based on type
        if content_type == 'rubric':
            response_data['rubric'] = result
        elif content_type == 'instructions':
            response_data['instructions'] = result
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Content generation error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500


def generate_grading_rubric(subject, grade, topic, assignment_type, language='english'):
    """Generate a comprehensive grading rubric"""
    language_names = {
        'english': 'English',
        'afrikaans': 'Afrikaans',
        'zulu': 'IsiZulu',
        'xhosa': 'IsiXhosa',
        'sotho': 'Sesotho'
    }
    
    lang_instruction = f" in {language_names.get(language, 'English')}" if language != 'english' else ""
    
    prompt = f"""
    Create a comprehensive grading rubric for a Grade {grade} {subject} {assignment_type} on the topic of "{topic}"{lang_instruction}.
    
    The rubric should include:
    1. Clear performance levels (Excellent, Good, Satisfactory, Needs Improvement)
    2. Specific criteria for each level
    3. Point values or percentage ranges
    4. Clear descriptions of what constitutes each performance level
    5. Assessment criteria appropriate for Grade {grade} students
    
    Make it practical for South African teachers to use in their classroom assessment.
    
    Format as a clear, structured rubric that can be easily shared with students.
    """
    
    try:
        response = ai_service.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        current_app.logger.error(f"Rubric generation error: {str(e)}")
        return None


def enhance_instructions(subject, grade, topic, title, existing_instructions, language='english'):
    """Enhance or generate comprehensive assignment instructions"""
    language_names = {
        'english': 'English',
        'afrikaans': 'Afrikaans',
        'zulu': 'IsiZulu',
        'xhosa': 'IsiXhosa',
        'sotho': 'Sesotho'
    }
    
    lang_instruction = f" in {language_names.get(language, 'English')}" if language != 'english' else ""
    
    if existing_instructions:
        prompt = f"""
        Enhance and improve these assignment instructions for a Grade {grade} {subject} assignment titled "{title}" on the topic of "{topic}"{lang_instruction}:
        
        Current Instructions:
        {existing_instructions}
        
        Please improve them by:
        1. Making them clearer and more specific
        2. Adding step-by-step guidance appropriate for Grade {grade} students
        3. Including assessment criteria
        4. Adding helpful tips and examples
        5. Ensuring they meet South African curriculum standards
        6. Making them engaging and motivational
        
        Keep the tone encouraging and supportive while being precise about expectations.
        """
    else:
        prompt = f"""
        Create comprehensive assignment instructions for a Grade {grade} {subject} assignment titled "{title}" on the topic of "{topic}"{lang_instruction}.
        
        The instructions should include:
        1. Clear learning objectives
        2. Step-by-step task breakdown appropriate for Grade {grade}
        3. Specific requirements and expectations
        4. Assessment criteria
        5. Helpful tips and examples
        6. Time management suggestions
        7. Resources students can use
        8. Submission guidelines
        
        Make them aligned with South African curriculum standards and culturally relevant.
        Use an encouraging, supportive tone that motivates students.
        """
    
    try:
        response = ai_service.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        current_app.logger.error(f"Instructions enhancement error: {str(e)}")
        return None
@login_required
def personalized_learning():
    """Generate personalized learning recommendations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get student performance data
        student_id = data.get('student_id')
        subject = data.get('subject')
        recent_scores = data.get('recent_scores', [])
        learning_goals = data.get('learning_goals', [])
        
        # Only students can request their own data, or teachers/admins can request any
        if current_user.role == UserRole.STUDENT and str(current_user.id) != str(student_id):
            return jsonify({'error': 'Students can only access their own learning data'}), 403
        
        # Generate personalized recommendations using AI
        prompt = f"""
        Generate personalized learning recommendations for a student in {subject}.
        
        Recent test scores: {recent_scores}
        Learning goals: {learning_goals}
        
        Provide recommendations as JSON:
        {{
            "strengths": ["area1", "area2"],
            "areas_for_improvement": ["area1", "area2"],
            "recommended_activities": [
                {{
                    "activity": "Practice fractions",
                    "difficulty": "medium",
                    "estimated_time": "30 minutes",
                    "resources": ["Khan Academy", "Workbook Ch 5"]
                }}
            ],
            "study_plan": {{
                "week_1": ["Activity 1", "Activity 2"],
                "week_2": ["Activity 3", "Activity 4"]
            }}
        }}
        """
        
        response = ai_service.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7
        )
        
        recommendations = json.loads(response.choices[0].message.content)
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'subject': subject,
            'recommendations': recommendations
        })
        
    except Exception as e:
        current_app.logger.error(f"Personalized learning error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@bp.route('/ai-tutor', methods=['POST'])
@login_required
def ai_tutor():
    """AI-powered tutoring chat interface"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question')
        subject = data.get('subject')
        grade_level = data.get('grade_level')
        context = data.get('context', '')
        
        if not question:
            return jsonify({'error': 'Missing question field'}), 400
        
        # Create tutoring prompt
        prompt = f"""
        You are an AI tutor for South African students. Answer this {subject} question for a Grade {grade_level} student.
        
        Question: {question}
        Context: {context}
        
        Provide a helpful, educational response that:
        1. Explains the concept clearly
        2. Shows step-by-step problem solving if applicable
        3. Provides examples
        4. Suggests further learning resources
        5. Is appropriate for the grade level
        
        Be encouraging and supportive in your tone.
        """
        
        response = ai_service.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'subject': subject,
            'grade_level': grade_level
        })
        
    except Exception as e:
        current_app.logger.error(f"AI tutor error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500