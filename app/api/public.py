from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import os

bp = Blueprint('public', __name__)

@bp.route('/')
def home():
    """Homepage"""
    return render_template('public/home.html')

@bp.route('/schools')
def schools():
    """School directory"""
    return render_template('public/schools.html')

@bp.route('/schools/<int:school_id>')
def school_detail(school_id):
    """Individual school details"""
    return render_template('public/school_detail.html', school_id=school_id)

@bp.route('/language-demo')
def language_demo():
    """Language demonstration page"""
    return render_template('public/language_demo.html')

@bp.route('/upload')
@login_required
def upload():
    """File upload page"""
    return render_template('files/upload.html')

@bp.route('/test-dashboard')
def test_dashboard():
    """Dashboard visibility test page"""
    return render_template('test/dashboard_test.html')

@bp.route('/about')
def about():
    """About page"""
    return render_template('public/about.html')

@bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('public/contact.html')

@bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('public/privacy.html')