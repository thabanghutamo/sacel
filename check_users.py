#!/usr/bin/env python3
"""
Check user authentication and roles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, UserRole
from app.extensions import db

def check_users():
    """Check user accounts and their roles"""
    app = create_app()
    
    with app.app_context():
        print("🔍 USER ACCOUNT ANALYSIS")
        print("=" * 40)
        
        # Get all users
        users = User.query.all()
        
        print(f"📊 Total users in database: {len(users)}")
        
        if not users:
            print("❌ No users found in database!")
            print("🔧 SOLUTION: Create test users for each role")
            return
        
        print(f"\n👥 USER ACCOUNTS:")
        print("-" * 20)
        
        role_counts = {}
        
        for user in users:
            role_name = user.role.value if user.role else "Unknown"
            role_counts[role_name] = role_counts.get(role_name, 0) + 1
            
            status = "✅ Active" if user.is_active else "❌ Inactive"
            school = f" (School: {user.school.name})" if user.school else " (No school)"
            
            print(f"  {user.id:2d}. {user.first_name} {user.last_name}")
            print(f"      Email: {user.email}")
            print(f"      Role: {role_name}")
            print(f"      Status: {status}{school}")
            print()
        
        print(f"📈 ROLE DISTRIBUTION:")
        print("-" * 20)
        for role, count in role_counts.items():
            print(f"  {role}: {count} users")
        
        # Check if we have users for each main role
        required_roles = [UserRole.STUDENT, UserRole.TEACHER, UserRole.SYSTEM_ADMIN]
        missing_roles = []
        
        for role in required_roles:
            if role.value not in role_counts:
                missing_roles.append(role.value)
        
        if missing_roles:
            print(f"\n⚠️  MISSING ROLES: {', '.join(missing_roles)}")
            print("🔧 SOLUTION: Create users with missing roles")
        
        return users, role_counts

def create_test_users():
    """Create test users for each role"""
    app = create_app()
    
    with app.app_context():
        print(f"\n🔧 CREATING TEST USERS")
        print("-" * 25)
        
        test_users = [
            {
                'email': 'student@test.com',
                'password': 'password123',
                'first_name': 'Test',
                'last_name': 'Student',
                'role': UserRole.STUDENT,
                'id_number': '0000000001'
            },
            {
                'email': 'teacher@test.com', 
                'password': 'password123',
                'first_name': 'Test',
                'last_name': 'Teacher',
                'role': UserRole.TEACHER,
                'id_number': '0000000002'
            },
            {
                'email': 'admin@test.com',
                'password': 'password123', 
                'first_name': 'Test',
                'last_name': 'Admin',
                'role': UserRole.SYSTEM_ADMIN,
                'id_number': '0000000003'
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"  ⚠️  User already exists: {user_data['email']}")
                continue
            
            try:
                from werkzeug.security import generate_password_hash
                
                user = User(
                    email=user_data['email'],
                    password_hash=generate_password_hash(user_data['password']),
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    id_number=user_data['id_number'],
                    is_active=True
                )
                
                db.session.add(user)
                db.session.commit()
                
                print(f"  ✅ Created user: {user_data['email']} ({user_data['role'].value})")
                created_users.append(user)
                
            except Exception as e:
                print(f"  ❌ Failed to create {user_data['email']}: {str(e)}")
                db.session.rollback()
        
        return created_users

if __name__ == '__main__':
    print("🚀 Starting user analysis...")
    
    users, role_counts = check_users()
    
    # Check if we need to create test users
    if not users or len(role_counts) < 3:
        print(f"\n🔧 Creating test users to enable proper testing...")
        created = create_test_users()
        
        if created:
            print(f"\n✅ Test users created successfully!")
            print(f"📝 Login credentials:")
            print(f"   Student: student@test.com / password123")
            print(f"   Teacher: teacher@test.com / password123") 
            print(f"   Admin: admin@test.com / password123")
    
    print(f"\n✅ Analysis complete!")