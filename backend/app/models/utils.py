"""Database utilities for cross-database compatibility"""
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from flask import current_app
import os


def get_json_type():
    """Return appropriate JSON type based on database being used"""
    database_url = os.getenv('DATABASE_URL', current_app.config.get('SQLALCHEMY_DATABASE_URI', ''))
    
    # Use JSONB for PostgreSQL, JSON for SQLite and others
    if 'postgresql' in database_url or 'postgres' in database_url:
        return JSONB
    else:
        return JSON 