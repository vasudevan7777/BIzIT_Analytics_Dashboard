"""
BizIT Analytics - Main Flask Application
Secure Business Revenue & Profitability Analytics System
"""
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from models import db, init_db
from auth import auth_bp, is_token_revoked
from api import api_bp

def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_token_revoked(jwt_header, jwt_payload)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please log in again'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Token verification failed'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'Authorization required',
            'message': 'Please provide a valid access token'
        }), 401
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Serve frontend
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'BizIT Analytics API is running'})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


# Create application instance
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    BizIT Analytics                          ║
    ║     Secure Business Revenue & Profitability Analytics        ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Server starting...                                          ║
    ║  API:       http://localhost:5000/api                        ║
    ║  Frontend:  http://localhost:5000                            ║
    ║                                                              ║
    ║  Default Admin Login:                                        ║
    ║  Email:    admin@bizitanalytics.com                          ║
    ║  Password: Admin@123                                         ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)
