#!/usr/bin/env python3
"""
Script to add sample submission data with grades to the database.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import User, Assignment, Submission

def add_sample_submissions():
    """Add sample submissions with grades to the database."""
    app = create_app()
    
    with app.app_context():
        # Get student users (role = 'student')
        students = User.query.filter_by(role='student').all()
        print(f"Found {len(students)} students")
        
        # Get all assignments
        assignments = Assignment.query.all()
        print(f"Found {len(assignments)} assignments")
        
        if not students:
            print("No students found. Creating sample students...")
            # Create a few students if none exist
            for i in range(1, 4):
                student = User(
                    first_name=f"Student{i}",
                    last_name="Test",
                    email=f"student{i}@test.com",
                    phone=f"012345678{i}",
                    id_number=f"900101000{i}",
                    role="student",
                    school_id=1,
                    is_active=True,
                    preferred_language="en"
                )
                student.set_password("password123")
                db.session.add(student)
            
            db.session.commit()
            students = User.query.filter_by(role='student').all()
            print(f"Created {len(students)} students")
        
        if not assignments:
            print("No assignments found. Please run add_sample_assignments.py first.")
            return
        
        # Clear existing submissions to avoid duplicates
        Submission.query.delete()
        
        # Create submissions for students
        submission_count = 0
        
        for student in students:
            # Each student submits to 60-80% of assignments
            num_assignments_to_submit = random.randint(
                int(len(assignments) * 0.6), 
                int(len(assignments) * 0.8)
            )
            
            selected_assignments = random.sample(assignments, num_assignments_to_submit)
            
            for assignment in selected_assignments:
                # Random submission date between assignment creation and due date
                if assignment.due_date:
                    min_date = assignment.created_at
                    max_date = min(assignment.due_date, datetime.utcnow())
                    if min_date < max_date:
                        submission_date = min_date + timedelta(
                            seconds=random.randint(0, int((max_date - min_date).total_seconds()))
                        )
                    else:
                        submission_date = assignment.created_at
                else:
                    submission_date = assignment.created_at + timedelta(days=random.randint(1, 14))
                
                # Determine if submission is graded (80% chance)
                is_graded = random.random() < 0.8
                percentage = None
                grade_status = "submitted"
                
                if is_graded:
                    # Generate realistic grade distribution
                    rand = random.random()
                    if rand < 0.1:  # 10% fail (0-49%)
                        percentage = random.randint(0, 49)
                    elif rand < 0.3:  # 20% barely pass (50-59%)
                        percentage = random.randint(50, 59)
                    elif rand < 0.6:  # 30% good (60-74%)
                        percentage = random.randint(60, 74)
                    elif rand < 0.85:  # 25% very good (75-89%)
                        percentage = random.randint(75, 89)
                    else:  # 15% excellent (90-100%)
                        percentage = random.randint(90, 100)
                    
                    grade_status = "graded"
                
                submission = Submission(
                    assignment_id=assignment.id,
                    student_id=student.id,
                    content=f"Sample submission for {assignment.title} by {student.first_name}",
                    submitted_at=submission_date,
                    percentage=percentage,
                    status=grade_status
                )
                
                db.session.add(submission)
                submission_count += 1
        
        # Commit all submissions
        db.session.commit()
        
        print(f"\nSample data added successfully!")
        print(f"Created {submission_count} submissions")
        
        # Show some statistics
        total_submissions = Submission.query.count()
        graded_submissions = Submission.query.filter_by(status='graded').count()
        avg_grade = db.session.query(db.func.avg(Submission.percentage)).filter(
            Submission.percentage.isnot(None)
        ).scalar()
        
        print(f"\nStatistics:")
        print(f"Total submissions: {total_submissions}")
        print(f"Graded submissions: {graded_submissions}")
        print(f"Average grade: {avg_grade:.1f}%" if avg_grade else "No grades yet")
        
        # Show submissions per assignment
        print(f"\nSubmissions per assignment:")
        for assignment in assignments:
            count = Submission.query.filter_by(assignment_id=assignment.id).count()
            print(f"  {assignment.title}: {count} submissions")

if __name__ == "__main__":
    add_sample_submissions()