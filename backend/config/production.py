#!/usr/bin/env python3
"""
Production Configuration for OpalSight
Handles environment variables for cloud deployment
"""
import os
from datetime import timedelta
from urllib.parse import urlparse


class ProductionConfig:
    """Production configuration class"""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-key-change-this-in-production'
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///production.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 20,
    }
    
    # Redis/Cache configuration
    REDIS_URL = os.environ.get('REDIS_URL', '')
    CACHE_TYPE = 'redis' if REDIS_URL else 'simple'
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # API Keys
    FMP_API_KEY = os.environ.get('FMP_API_KEY')
    EARNINGS_CALL_API_KEY = os.environ.get('EARNINGS_CALL_API_KEY')
    
    # API Configuration
    FMP_BASE_URL = 'https://financialmodelingprep.com/'
    FMP_RATE_LIMIT_DELAY = 0.5  # 500ms between requests
    FMP_TIMEOUT = 30
    
    # CORS settings for production
    CORS_ORIGINS = [
        'https://opalsight.vercel.app',
        'https://opalsight-frontend.vercel.app', 
        'https://www.opalsight.com',
        'https://opalsight.com'
    ]
    
    # Production-specific settings
    PORT = int(os.environ.get('PORT', 8000))
    HOST = '0.0.0.0'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File upload limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = REDIS_URL if REDIS_URL else 'memory://'
    RATELIMIT_DEFAULT = "1000 per hour"
    
    # Email configuration (if needed for alerts)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Scheduled tasks configuration
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'UTC'
    
    # Data collection settings
    AUTO_COLLECTION_ENABLED = os.environ.get('AUTO_COLLECTION_ENABLED', 'true').lower() == 'true'
    COLLECTION_HOUR = int(os.environ.get('COLLECTION_HOUR', 2))  # 2 AM UTC
    COLLECTION_DAY_OF_MONTH = int(os.environ.get('COLLECTION_DAY_OF_MONTH', 1))  # 1st of month
    
    # Minimum requirements for analysis
    MIN_MARKET_CAP = 100_000_000  # $100M minimum market cap
    MIN_TRANSCRIPT_LENGTH = 1000  # Minimum 1000 characters
    
    # Sentiment analysis thresholds
    SENTIMENT_THRESHOLD_HIGH = 0.5
    SENTIMENT_THRESHOLD_MEDIUM = 0.2
    ALERT_THRESHOLD_DEFAULT = 0.3
    
    @classmethod
    def validate_config(cls):
        """Validate that required environment variables are set"""
        required_vars = []
        missing_vars = []
        
        # Check critical environment variables
        if not cls.FMP_API_KEY:
            missing_vars.append('FMP_API_KEY')
        
        if not cls.EARNINGS_CALL_API_KEY:
            missing_vars.append('EARNINGS_CALL_API_KEY')
        
        if not cls.DATABASE_URL:
            missing_vars.append('DATABASE_URL')
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_database_url(cls):
        """Get properly formatted database URL"""
        if cls.DATABASE_URL:
            # Handle Railway/Heroku Postgres URL format
            url = urlparse(cls.DATABASE_URL)
            if url.scheme == 'postgres':
                # Replace postgres:// with postgresql://
                return cls.DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        return cls.DATABASE_URL
    
    @classmethod
    def is_redis_available(cls):
        """Check if Redis is available"""
        return bool(cls.REDIS_URL and cls.REDIS_URL.strip())


# Configuration validation on import
try:
    ProductionConfig.validate_config()
except ValueError as e:
    print(f"Configuration validation warning: {e}")
    print("Some features may not work properly without required environment variables.") 