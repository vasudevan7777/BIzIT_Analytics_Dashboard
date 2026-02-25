"""
BizIT Analytics - Configuration Settings
"""
import os
from datetime import timedelta

class Config:
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bizit-analytics-secret-key-2024'
    
    # JWT Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-bizit-analytics'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database Settings (MySQL)
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'bizit_analytics'
    
    # SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # For SQLite fallback (development)
    SQLITE_DATABASE_URI = 'sqlite:///bizit_analytics.db'
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    
    # Alert Thresholds
    REVENUE_DROP_THRESHOLD = 10  # Percentage
    PROFIT_MARGIN_THRESHOLD = 10  # Percentage
    
    # Pagination
    ITEMS_PER_PAGE = 50


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.SQLITE_DATABASE_URI


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_bizit_analytics.db'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
