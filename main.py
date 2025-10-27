from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Disable reloader in development to avoid Redis connection issues
    use_reloader = os.environ.get('FLASK_USE_RELOADER', 'false').lower() == 'true'
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=use_reloader)