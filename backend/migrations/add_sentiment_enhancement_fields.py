#!/usr/bin/env python3
"""
Database Migration: Add Enhanced Sentiment Analysis Fields
Adds key_quotes and extracted_guidance JSON fields to sentiment_analysis table
"""
import os
import sys
import logging
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db
from sqlalchemy import text

logger = logging.getLogger(__name__)


def run_migration():
    """Run the sentiment enhancement migration"""
    logger.info("Starting sentiment enhancement migration...")
    
    # Set environment variables
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///instance/opalsight.db')
    os.environ['FLASK_ENV'] = 'development'
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('sentiment_analysis')]
            
            migrations_run = []
            
            # Add key_quotes column if it doesn't exist
            if 'key_quotes' not in columns:
                logger.info("Adding key_quotes column...")
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE sentiment_analysis ADD COLUMN key_quotes JSON'))
                    conn.commit()
                migrations_run.append('key_quotes column added')
            else:
                logger.info("key_quotes column already exists")
            
            # Add extracted_guidance column if it doesn't exist
            if 'extracted_guidance' not in columns:
                logger.info("Adding extracted_guidance column...")
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE sentiment_analysis ADD COLUMN extracted_guidance JSON'))
                    conn.commit()
                migrations_run.append('extracted_guidance column added')
            else:
                logger.info("extracted_guidance column already exists")
            
            # Update existing records with empty arrays for new fields
            if migrations_run:
                logger.info("Updating existing records with default values...")
                
                # Set default values for new columns
                if 'key_quotes column added' in migrations_run:
                    with db.engine.connect() as conn:
                        conn.execute(text("UPDATE sentiment_analysis SET key_quotes = '[]' WHERE key_quotes IS NULL"))
                        conn.commit()
                
                if 'extracted_guidance column added' in migrations_run:
                    with db.engine.connect() as conn:
                        conn.execute(text("UPDATE sentiment_analysis SET extracted_guidance = '[]' WHERE extracted_guidance IS NULL"))
                        conn.commit()
                
                logger.info("Updated existing records with default values")
            
            logger.info("=" * 50)
            logger.info("SENTIMENT ENHANCEMENT MIGRATION COMPLETE!")
            logger.info("=" * 50)
            
            if migrations_run:
                logger.info("Changes made:")
                for change in migrations_run:
                    logger.info(f"  - {change}")
            else:
                logger.info("No changes needed - all columns already exist")
            
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_migration() 