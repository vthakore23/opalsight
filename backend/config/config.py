"""Configuration module for OpalSight"""
import os
from datetime import timedelta
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""
    # Application settings
    APP_NAME = "OpalSight"
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database - Default to SQLite for easy deployment
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///instance/opalsight.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }
    
    # FMP API Configuration
    FMP_API_KEY = os.getenv('FMP_API_KEY', '9a835ed8bbff501bf036a6f843d5a6fe')
    FMP_BASE_URL = 'https://financialmodelingprep.com/api'
    FMP_RATE_LIMIT_DELAY = 0.25  # 250ms between calls for free tier
    FMP_TIMEOUT = 30  # seconds
    
    # Earnings Call API Configuration
    EARNINGS_CALL_API_KEY = os.getenv('EARNINGS_CALL_API_KEY', 'premium_44REQ4tOEr0T7ADdkEogjw')
    
    # OpenAI Configuration (optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    USE_GPT_ENHANCEMENT = os.getenv('USE_GPT_ENHANCEMENT', 'false').lower() == 'true'
    
    # Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'noreply@opalsight.com')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Frontend URL for email links
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # Redis Configuration - Default to simple cache for deployment
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Celery Configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = 'US/Eastern'
    CELERY_ENABLE_UTC = True
    
    # Analysis Configuration
    MIN_MARKET_CAP = 50_000_000  # $50M minimum
    LOOKBACK_QUARTERS = 4  # Number of quarters to analyze for trends
    CONFIDENCE_THRESHOLD = 0.2  # Threshold for significant changes
    
    # Scheduler Configuration
    WEEKLY_COLLECTION_DAY = 'friday'
    WEEKLY_COLLECTION_TIME = '18:00'  # 6 PM EST
    
    # API Rate Limiting
    API_RATE_LIMIT = '100 per hour'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Sentry Configuration (for error tracking)
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    
    # Report Generation
    REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    
    # Cache Configuration - Default to simple cache for deployment
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    # Use environment SECRET_KEY in production, but have fallback
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-production-secret-key-change-me')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default']) 