#!/usr/bin/env python3
"""Add sample assignments data to test the assignments page."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, UserRole, Assignment, School
from app.extensions import db
from datetime import datetime, timedelta

def add_sample_assignments():
    """Add sample assignments to the database."""
    
    print("Creating Flask app...")
    app = create_app()
    
    with app.app_context():
        try:
            # Get a school and teacher
            school = School.query.first()
            teacher = User.query.filter_by(role=UserRole.TEACHER).first()
            
            if not school or not teacher:
                print("❌ Need at least one school and one teacher in database")
                return
            
            print(f"Using school: {school.name}")
            print(f"Using teacher: {teacher.first_name} {teacher.last_name}")
            
            # Check if assignments already exist
            existing_count = Assignment.query.count()
            print(f"Existing assignments: {existing_count}")
            
            if existing_count == 0:
                # Create sample assignments
                sample_assignments = [
                    {
                        'title': 'Mathematics Quiz - Algebra',
                        'description': 'Complete the algebra problems focusing on linear equations and systems.',
                        'subject': 'Mathematics',
                        'grade_level': 10,
                        'due_date': datetime.now() + timedelta(days=7),
                        'is_published': True,
                        'max_score': 100
                    },
                    {
                        'title': 'English Essay - Shakespeare',
                        'description': 'Write a 500-word essay on themes in Romeo and Juliet.',
                        'subject': 'English',
                        'grade_level': 10,
                        'due_date': datetime.now() + timedelta(days=14),
                        'is_published': True,
                        'max_score': 100
                    },
                    {
                        'title': 'Science Project - Photosynthesis',
                        'description': 'Create a presentation explaining the process of photosynthesis.',
                        'subject': 'Life Sciences',
                        'grade_level': 10,
                        'due_date': datetime.now() + timedelta(days=21),
                        'is_published': True,
                        'max_score': 150
                    },
                    {
                        'title': 'History Research - Apartheid',
                        'description': 'Research project on the impact of apartheid in South Africa.',
                        'subject': 'History',
                        'grade_level': 10,
                        'due_date': datetime.now() + timedelta(days=28),
                        'is_published': False,  # Not yet published
                        'max_score': 200
                    }
                ]
                
                for assignment_data in sample_assignments:
                    assignment = Assignment(
                        title=assignment_data['title'],
                        description=assignment_data['description'],
                        subject=assignment_data['subject'],
                        grade_level=assignment_data['grade_level'],
                        school_id=school.id,
                        teacher_id=teacher.id,
                        due_date=assignment_data['due_date'],
                        is_published=assignment_data['is_published'],
                        max_score=assignment_data['max_score'],
                        is_active=True
                    )
                    db.session.add(assignment)
                
                db.session.commit()
                print(f"✅ Created {len(sample_assignments)} sample assignments")
                
            else:
                # Update existing assignments to have school_id and is_published
                assignments_to_update = Assignment.query.filter(
                    (Assignment.school_id == None) | (Assignment.is_published == None)
                ).all()
                
                updated_count = 0
                for assignment in assignments_to_update:
                    if assignment.school_id is None:
                        assignment.school_id = school.id
                        updated_count += 1
                    if not hasattr(assignment, 'is_published') or assignment.is_published is None:
                        assignment.is_published = True
                        updated_count += 1
                
                if updated_count > 0:
                    db.session.commit()
                    print(f"✅ Updated {updated_count} existing assignments")
                else:
                    print("✅ All assignments already have required fields")
            
            # Verify assignments
            all_assignments = Assignment.query.filter_by(school_id=school.id).all()
            published_assignments = Assignment.query.filter_by(school_id=school.id, is_published=True).all()
            
            print(f"\nFinal state:")
            print(f"  Total assignments for school: {len(all_assignments)}")
            print(f"  Published assignments: {len(published_assignments)}")
            
            for assignment in published_assignments[:3]:
                print(f"    - {assignment.title} (Due: {assignment.due_date.strftime('%Y-%m-%d')})")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_sample_assignments()