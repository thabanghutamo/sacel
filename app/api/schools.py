from flask import Blueprint, render_template

bp = Blueprint('schools', __name__)

@bp.route('/dashboard')
def dashboard():
    """School admin dashboard"""
    return render_template('schools/dashboard.html')