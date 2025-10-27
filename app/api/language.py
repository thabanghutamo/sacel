"""
Language API endpoints for SACEL Platform
Handles language switching and localization preferences
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import current_user
from app.services.language_service import LanguageService
from app.extensions import db
from app.models import User

bp = Blueprint('language', __name__, url_prefix='/api/language')


@bp.route('/switch', methods=['POST'])
def switch_language():
    """Switch user's language preference"""
    try:
        # Debug logging
        print(f"Language switch request - Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Is JSON: {request.is_json}")
        print(f"Raw data: {request.data}")
        print(f"Form data: {dict(request.form)}")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        print(f"Parsed data: {data}")
        
        if not data:
            print("Error: No data provided")
            return jsonify({'error': 'No data provided'}), 400
        
        language_code = data.get('language')
        
        if not language_code:
            return jsonify({'error': 'Language code is required'}), 400
        
        # Validate language code
        supported_languages = LanguageService.get_supported_languages()
        if language_code not in supported_languages:
            return jsonify({
                'error': 'Unsupported language',
                'supported': list(supported_languages.keys())
            }), 400
        
        # Set language in session
        success = LanguageService.set_language(language_code)
        if not success:
            return jsonify({'error': 'Failed to set language'}), 500
        
        # Update user preference if logged in
        if current_user.is_authenticated:
            try:
                current_user.preferred_language = language_code
                db.session.commit()
            except Exception as e:
                # Don't fail if user table doesn't have language field yet
                db.session.rollback()
                pass
        
        return jsonify({
            'success': True,
            'language': language_code,
            'language_name': LanguageService.get_language_name(language_code),
            'message': f'Language switched to {LanguageService.get_language_name(language_code)}'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to switch language: {str(e)}'}), 500


@bp.route('/current')
def get_current_language():
    """Get current user's language preference"""
    try:
        current_lang = LanguageService.get_current_language()
        return jsonify({
            'language': current_lang,
            'language_name': LanguageService.get_language_name(current_lang),
            'supported_languages': LanguageService.get_supported_languages()
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get current language: {str(e)}'}), 500


@bp.route('/detect')
def detect_language():
    """Detect user's preferred language from browser"""
    try:
        detected_lang = LanguageService.detect_language()
        return jsonify({
            'detected_language': detected_lang,
            'language_name': LanguageService.get_language_name(detected_lang),
            'supported_languages': LanguageService.get_supported_languages()
        })
    except Exception as e:
        return jsonify({'error': f'Failed to detect language: {str(e)}'}), 500


@bp.route('/available')
def get_available_languages():
    """Get all available languages"""
    try:
        languages = LanguageService.get_supported_languages()
        current_lang = LanguageService.get_current_language()
        
        language_list = []
        for code, name in languages.items():
            language_list.append({
                'code': code,
                'name': name,
                'current': code == current_lang,
                'rtl': LanguageService.is_rtl_language(code)
            })
        
        return jsonify({
            'languages': language_list,
            'current_language': current_lang,
            'total_count': len(languages)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get available languages: {str(e)}'}), 500


@bp.route('/terms/<term>')
def translate_term(term):
    """Translate a specific educational term"""
    try:
        from app.services.language_service import get_translated_term
        
        language_code = request.args.get('lang', LanguageService.get_current_language())
        translated = get_translated_term(term, language_code)
        
        return jsonify({
            'term': term,
            'language': language_code,
            'translation': translated
        })
    except Exception as e:
        return jsonify({'error': f'Failed to translate term: {str(e)}'}), 500


# Language switching redirect endpoint for forms
@bp.route('/switch-redirect', methods=['POST'])
def switch_language_redirect():
    """Switch language and redirect back to referring page"""
    try:
        language_code = request.form.get('language')
        
        if language_code:
            LanguageService.set_language(language_code)
            
            # Update user preference if logged in
            if current_user.is_authenticated:
                try:
                    current_user.preferred_language = language_code
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    pass
        
        # Redirect back to referring page or home
        next_page = request.form.get('next') or request.referrer or url_for('public.home')
        return redirect(next_page)
        
    except Exception as e:
        # If error, redirect to home
        return redirect(url_for('public.home'))