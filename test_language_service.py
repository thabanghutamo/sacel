from app import create_app
from app.services.language_service import LanguageService

app = create_app()
with app.app_context():
    supported = LanguageService.get_supported_languages()
    print("Supported languages:", supported)
    print("Current language:", LanguageService.get_current_language())