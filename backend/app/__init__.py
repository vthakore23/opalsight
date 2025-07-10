"""OpalSight Flask Application"""
import logging
import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate

from app.models import db, migrate
from config.config import get_config


def create_app(config_name=None):
    """Create Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure CORS
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register performance blueprint
    from app.api.performance import performance_bp
    app.register_blueprint(performance_bp)
    
    # Register export blueprint
    from app.api.export_routes import export_bp
    app.register_blueprint(export_bp)
    
    # Register Q1 2025 blueprint
    from app.api.q1_2025_routes import q1_2025_bp
    app.register_blueprint(q1_2025_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables (with error handling)
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.warning(f"Could not create database tables: {str(e)}")
            app.logger.info("Application will continue without database for now")
    
    return app


def configure_logging(app):
    """Configure application logging"""
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=app.config['LOG_FORMAT'],
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('opalsight.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    app.logger.info(f"OpalSight application initialized with {os.getenv('FLASK_ENV', 'development')} configuration")


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except:
            pass  # If database isn't available, just continue
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}")
        return {'error': 'An unexpected error occurred'}, 500 