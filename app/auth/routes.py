from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
from app.auth import bp
from app.models import User
from app.extensions import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.home'))
    
    if request.method == 'POST':
        try:
            current_app.logger.info("Login POST request received")
            email = request.form.get('email')
            password = request.form.get('password')
            remember = bool(request.form.get('remember'))
            
            current_app.logger.info(f"Login attempt for email: {email}")
            
            if not email or not password:
                flash('Email and password are required.', 'error')
                return redirect(url_for('auth.login'))
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Your account has been deactivated. Please contact support.', 'error')
                    return redirect(url_for('auth.login'))
                
                login_user(user, remember=remember)
                
                # Check if user must change password
                if user.must_change_password:
                    flash('You must change your password before continuing.', 'warning')
                    return redirect(url_for('auth.change_password'))
                
                # Redirect to home page for now (dashboards not implemented yet)
                flash(f'Welcome back, {user.first_name}!', 'success')
                return redirect(url_for('public.home'))
            else:
                flash('Invalid email or password.', 'error')
                
        except Exception as e:
            current_app.logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public.home'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('public.home'))
    
    if request.method == 'POST':
        # Basic registration - mainly for parents/guardians
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not all([first_name, last_name, email, password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'error')
            return render_template('auth/register.html')
        
        # Create new user
        from app.models import UserRole
        user = User()
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone
        user.role = UserRole.PARENT
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('auth/change_password.html')
        
        current_user.set_password(new_password)
        current_user.must_change_password = False
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('public.home'))
    
    return render_template('auth/change_password.html')