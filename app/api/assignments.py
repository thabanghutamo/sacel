from flask import Blueprint, render_template

bp = Blueprint('assignments', __name__)

@bp.route('/')
def index():
    """Assignments index"""
    return render_template('assignments/index.html')