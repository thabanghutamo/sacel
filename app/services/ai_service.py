import openai
from flask import current_app
import json
from typing import List, Dict, Any

class AIService:
    """Service for AI-powered features using OpenAI API"""
    
    def __init__(self):
        self.client = None
        
    def init_app(self, app):
        """Initialize with Flask app"""
        openai.api_key = app.config.get('OPENAI_API_KEY')
        self.client = openai
    
    def generate_assignment(self, subject: str, grade: int, topic: str, 
                          assignment_type: str, difficulty: str = 'medium') -> Dict[str, Any]:
        """Generate an assignment using AI"""
        try:
            prompt = f"""
            Create a {assignment_type} assignment for {subject} for grade {grade} students.
            Topic: {topic}
            Difficulty: {difficulty}
            
            Please provide:
            1. Assignment title
            2. Instructions for students
            3. 5-10 questions with varying difficulty
            4. Marking rubric
            5. Suggested time to complete
            
            Format the response as JSON with the following structure:
            {{
                "title": "Assignment title",
                "instructions": "Clear instructions for students",
                "questions": [
                    {{
                        "question": "Question text",
                        "type": "mcq|essay|short_answer|true_false",
                        "marks": 5,
                        "options": ["A", "B", "C", "D"] // for MCQ only
                    }}
                ],
                "rubric": "Marking guidelines",
                "estimated_time_minutes": 45
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            current_app.logger.error(f"AI assignment generation failed: {str(e)}")
            return None
    
    def grade_assignment(self, questions: List[Dict], answers: Dict[str, str], 
                        max_score: int) -> Dict[str, Any]:
        """Grade an assignment using AI assistance"""
        try:
            prompt = f"""
            Grade this assignment submission. 
            
            Questions: {json.dumps(questions, indent=2)}
            Student Answers: {json.dumps(answers, indent=2)}
            Maximum Possible Score: {max_score}
            
            Please provide:
            1. Suggested grade out of {max_score}
            2. Breakdown by question with points earned
            3. Overall feedback for the student
            4. Confidence level (0.0 to 1.0)
            
            Format as JSON:
            {{
                "suggested_grade": 85,
                "breakdown": [
                    {{"question": 1, "earned": 10, "max": 10, "feedback": "Correct!"}},
                    {{"question": 2, "earned": 8, "max": 10, "feedback": "Good but missing details"}}
                ],
                "feedback": "Overall good work. Focus on providing more detailed explanations.",
                "confidence": 0.8
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return {
                'success': True,
                **result
            }
            
        except Exception as e:
            current_app.logger.error(f"AI grading failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def grade_short_answer(self, question: str, correct_answer: str, 
                          student_answer: str, max_points: int) -> Dict[str, Any]:
        """Grade a short answer question using AI"""
        try:
            prompt = f"""
            Grade this short answer question:
            
            Question: {question}
            Correct Answer: {correct_answer}
            Student Answer: {student_answer}
            Maximum Points: {max_points}
            
            Evaluate based on:
            1. Accuracy of key concepts
            2. Completeness of answer
            3. Understanding demonstrated
            
            Return JSON:
            {{
                "earned_points": 8,
                "is_correct": true,
                "feedback": "Good answer, covers main points",
                "confidence": 0.9
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return {
                'success': True,
                **result
            }
            
        except Exception as e:
            current_app.logger.error(f"AI short answer grading failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def grade_essay(self, question: str, rubric: str, student_answer: str, 
                   max_points: int) -> Dict[str, Any]:
        """Grade an essay question using AI"""
        try:
            prompt = f"""
            Grade this essay question:
            
            Question: {question}
            Grading Rubric: {rubric}
            Student Essay: {student_answer}
            Maximum Points: {max_points}
            
            Evaluate based on:
            1. Content accuracy and depth
            2. Organization and structure
            3. Writing clarity
            4. Use of examples/evidence
            
            Return JSON:
            {{
                "earned_points": 24,
                "feedback": "Well structured essay with good examples...",
                "rubric_scores": {{
                    "content": 8,
                    "organization": 7,
                    "clarity": 6,
                    "evidence": 3
                }},
                "confidence": 0.7
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return {
                'success': True,
                **result
            }
            
        except Exception as e:
            current_app.logger.error(f"AI essay grading failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_plagiarism(self, student_text: str, reference_texts: List[str]) -> Dict[str, Any]:
        """Detect potential plagiarism using AI analysis"""
        try:
            prompt = f"""
            Analyze this student submission for potential plagiarism against the reference texts.
            
            Student text: {student_text}
            
            Reference texts: {reference_texts}
            
            Provide analysis as JSON:
            {{
                "plagiarism_score": 0.2,  // 0-1 scale
                "matches_found": [
                    {{
                        "text": "matching text",
                        "source": "reference text index",
                        "confidence": 0.9
                    }}
                ],
                "recommendation": "No plagiarism detected|Possible plagiarism|Likely plagiarism"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            current_app.logger.error(f"Plagiarism detection failed: {str(e)}")
            return None
    
    def search_library(self, query: str, library_content: List[Dict]) -> List[Dict]:
        """Search library content using AI semantic search"""
        try:
            prompt = f"""
            Search through this educational library content for information related to: {query}
            
            Library content: {json.dumps(library_content, indent=2)}
            
            Return the most relevant results with page numbers and citations as JSON:
            {{
                "results": [
                    {{
                        "title": "Document title",
                        "page": 45,
                        "excerpt": "Relevant text excerpt",
                        "relevance_score": 0.9
                    }}
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            return result.get('results', [])
            
        except Exception as e:
            current_app.logger.error(f"Library search failed: {str(e)}")
            return []
    
    def translate_content(self, text: str, target_language: str) -> str:
        """Translate content to South African official languages"""
        language_map = {
            'af': 'Afrikaans',
            'en': 'English',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'st': 'Sesotho',
            'tn': 'Setswana',
            've': 'Tshivenda',
            'ts': 'Xitsonga',
            'ss': 'Siswati',
            'nr': 'isiNdebele',
            'nso': 'Sepedi'
        }
        
        if target_language not in language_map:
            return text
        
        try:
            target_lang_name = language_map[target_language]
            prompt = f"Translate this educational content to {target_lang_name}: {text}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=len(text) * 2,  # Allow for expansion
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            current_app.logger.error(f"Translation failed: {str(e)}")
            return text

# Initialize service instance
ai_service = AIService()