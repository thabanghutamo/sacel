#!/usr/bin/env python3
"""
SACEL Database Seeding Script
Creates initial admin users and demo data for development/testing
"""

import os
import sys
from datetime import datetime, date
import json

# Add the parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import User, School, Student, Teacher, UserRole

def create_admin_user():
    """Create system admin user"""
    admin = User.query.filter_by(email='admin@sacel.co.za').first()
    if admin:
        print("✓ Admin user already exists")
        return admin
    
    admin = User(
        first_name='System',
        last_name='Administrator',
        email='admin@sacel.co.za',
        role=UserRole.SYSTEM_ADMIN,
        is_active=True,
        preferred_language='en'
    )
    admin.set_password('admin123')  # Change in production
    db.session.add(admin)
    db.session.commit()
    print("✓ Created system admin user: admin@sacel.co.za (password: admin123)")
    return admin

def create_demo_schools():
    """Create demo schools"""
    schools_data = [
        {
            'name': 'Johannesburg Primary School',
            'school_type': 'public',
            'address': '123 Main Street, Johannesburg',
            'city': 'Johannesburg',
            'province': 'Gauteng',
            'postal_code': '2001',
            'phone': '+27 11 123 4567',
            'email': 'info@jhbprimary.edu.za',
            'latitude': -26.2041,
            'longitude': 28.0473,
            'established_year': 1995,
            'student_capacity': 800,
            'current_enrollment': 650,
            'languages_offered': json.dumps(['English', 'Afrikaans', 'Zulu']),
            'admission_open': True,
            'pass_rate': 85.5,
            'average_score': 78.2,
            'is_active': True
        },
        {
            'name': 'Cape Town High School',
            'school_type': 'private',
            'address': '456 Oak Avenue, Cape Town',
            'city': 'Cape Town',
            'province': 'Western Cape',
            'postal_code': '8001',
            'phone': '+27 21 987 6543',
            'email': 'admissions@ctprivate.edu.za',
            'latitude': -33.9249,
            'longitude': 18.4241,
            'established_year': 1980,
            'student_capacity': 1200,
            'current_enrollment': 1100,
            'languages_offered': json.dumps(['English', 'Afrikaans', 'Xhosa']),
            'admission_open': True,
            'pass_rate': 92.8,
            'average_score': 84.6,
            'is_active': True
        },
        {
            'name': 'Durban Combined School',
            'school_type': 'public',
            'address': '789 Beach Road, Durban',
            'city': 'Durban',
            'province': 'KwaZulu-Natal',
            'postal_code': '4001',
            'phone': '+27 31 555 0123',
            'email': 'principal@durbanschool.edu.za',
            'latitude': -29.8587,
            'longitude': 31.0218,
            'established_year': 1988,
            'student_capacity': 950,
            'current_enrollment': 820,
            'languages_offered': json.dumps(['English', 'Zulu', 'Hindi']),
            'admission_open': True,
            'pass_rate': 79.3,
            'average_score': 72.8,
            'is_active': True
        }
    ]
    
    created_schools = []
    for school_data in schools_data:
        existing = School.query.filter_by(name=school_data['name']).first()
        if existing:
            print(f"✓ School '{school_data['name']}' already exists")
            created_schools.append(existing)
            continue
        
        school = School(**school_data)
        school.created_at = datetime.utcnow()
        db.session.add(school)
        created_schools.append(school)
        print(f"✓ Created school: {school_data['name']}")
    
    db.session.commit()
    return created_schools

def create_demo_users_and_staff(schools):
    """Create demo school admins, teachers, and students"""
    created_users = []
    
    for i, school in enumerate(schools):
        # Create school admin
        admin_email = f"admin@{school.name.lower().replace(' ', '').replace('school', '')}.edu.za"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                first_name='School',
                last_name='Administrator',
                email=admin_email,
                role=UserRole.SCHOOL_ADMIN,
                school_id=school.id,
                is_active=True,
                preferred_language='en'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            created_users.append(admin)
            print(f"✓ Created school admin: {admin_email}")
        
        # Create a principal
        principal_email = f"principal@{school.name.lower().replace(' ', '').replace('school', '')}.edu.za"
        principal = User.query.filter_by(email=principal_email).first()
        if not principal:
            principal = User(
                first_name='John' if i % 2 == 0 else 'Sarah',
                last_name='Principal',
                email=principal_email,
                role=UserRole.PRINCIPAL,
                school_id=school.id,
                is_active=True,
                preferred_language='en'
            )
            principal.set_password('principal123')
            db.session.add(principal)
            created_users.append(principal)
            print(f"✓ Created principal: {principal_email}")
        
        # Create teachers
        teacher_names = [
            ('Mary', 'Johnson', 'Mathematics'),
            ('David', 'Smith', 'English'),
            ('Lisa', 'Williams', 'Science'),
            ('Michael', 'Brown', 'History')
        ]
        
        for j, (first_name, last_name, subject) in enumerate(teacher_names):
            teacher_email = f"{first_name.lower()}.{last_name.lower()}@{school.name.lower().replace(' ', '').replace('school', '')}.edu.za"
            teacher_user = User.query.filter_by(email=teacher_email).first()
            if not teacher_user:
                teacher_user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=teacher_email,
                    role=UserRole.TEACHER,
                    school_id=school.id,
                    is_active=True,
                    preferred_language='en'
                )
                teacher_user.set_password('teacher123')
                db.session.add(teacher_user)
                db.session.flush()  # Flush to get the user ID
                created_users.append(teacher_user)
                
                # Create teacher profile
                teacher = Teacher(
                    user_id=teacher_user.id,
                    employee_number=f"T{school.id:03d}{j+1:02d}",
                    subjects=json.dumps([subject]),
                    grades=json.dumps(['8', '9', '10', '11', '12']),
                    qualifications=json.dumps(['B.Ed', 'Honours in ' + subject]),
                    hire_date=date(2020 + j, 1, 1),
                    status='active'
                )
                db.session.add(teacher)
                print(f"✓ Created teacher: {teacher_email} ({subject})")
        
        # Create students
        student_names = [
            ('Thabo', 'Mthembu'),
            ('Nomsa', 'Ngcobo'),
            ('Pieter', 'Van Der Merwe'),
            ('Amahle', 'Dlamini'),
            ('Connor', 'O\'Brien')
        ]
        
        for j, (first_name, last_name) in enumerate(student_names):
            # Clean up email format
            clean_last_name = last_name.lower().replace(' ', '').replace("'", '')
            school_name_clean = school.name.lower().replace(' ', '').replace('school', '')
            student_email = f"{first_name.lower()}.{clean_last_name}@student.{school_name_clean}.edu.za"
            student_user = User.query.filter_by(email=student_email).first()
            if not student_user:
                student_user = User(
                    first_name=first_name,
                    last_name=last_name,
                    email=student_email,
                    role=UserRole.STUDENT,
                    school_id=school.id,
                    is_active=True,
                    preferred_language='en'
                )
                student_user.set_password('student123')
                db.session.add(student_user)
                db.session.flush()  # Flush to get the user ID
                created_users.append(student_user)
                
                # Create student profile
                student = Student(
                    user_id=student_user.id,
                    learner_number=f"L{school.id:03d}{j+1:04d}",
                    grade=9 + (j % 4),  # Grades 9-12
                    subjects=json.dumps(['Mathematics', 'English', 'Science', 'History']),
                    enrollment_date=date(2023, 1, 15),
                    status='active'
                )
                db.session.add(student)
                print(f"✓ Created student: {student_email} (Grade {student.grade})")
    
    db.session.commit()
    return created_users

def main():
    """Run the seeding process"""
    print("🌱 Starting SACEL database seeding...")
    
    app = create_app()
    with app.app_context():
        # Create all tables (in case migrations weren't run)
        db.create_all()
        
        # Create admin user
        admin = create_admin_user()
        
        # Create demo schools
        schools = create_demo_schools()
        
        # Create demo users and staff
        users = create_demo_users_and_staff(schools)
        
        print(f"\n🎉 Seeding completed successfully!")
        print(f"Created {len(schools)} schools and {len(users) + 1} users")
        print("\n📊 Summary:")
        print("- System Admin: admin@sacel.co.za (password: admin123)")
        for school in schools:
            print(f"- {school.name}: admin@{school.name.lower().replace(' ', '').replace('school', '')}.edu.za")
        print("\n🔑 Default passwords: admin123, principal123, teacher123, student123")
        print("⚠️  Change these passwords in production!")

if __name__ == '__main__':
    main()