#!/usr/bin/env python3
"""
Simple database initialization script for OpalSight
"""
import os
import sys
import logging
from datetime import datetime, date
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables before importing Flask app
os.environ['DATABASE_URL'] = f'sqlite:///{os.path.abspath("instance/opalsight.db")}'
os.environ['FLASK_ENV'] = 'development' 
os.environ['CACHE_TYPE'] = 'simple'
os.environ['REDIS_URL'] = ''

from app import create_app
from app.models import db, Company, Transcript, SentimentAnalysis, TrendAnalysis, MonthlyReport, Alert, Watchlist

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample companies data
COMPANIES = [
    {
        'ticker': 'HROW',
        'name': 'Harrow Inc',
        'sector': 'Healthcare',
        'industry': 'Pharmaceuticals',
        'exchange': 'NASDAQ',
        'market_cap': 800000000
    },
    {
        'ticker': 'ETON',
        'name': 'Eton Pharmaceuticals',
        'sector': 'Healthcare', 
        'industry': 'Pharmaceuticals',
        'exchange': 'NASDAQ',
        'market_cap': 150000000
    },
    {
        'ticker': 'LQDA',
        'name': 'Liquidia Corporation',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'exchange': 'NASDAQ',
        'market_cap': 400000000
    },
    {
        'ticker': 'RYTM',
        'name': 'Rhythm Pharmaceuticals',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'exchange': 'NASDAQ',
        'market_cap': 2000000000
    },
    {
        'ticker': 'CDXS',
        'name': 'Codexis',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'exchange': 'NASDAQ',
        'market_cap': 600000000
    },
    {
        'ticker': 'SNWVD',
        'name': 'SANUWAVE Health Inc',
        'sector': 'Healthcare',
        'industry': 'Medical Devices',
        'exchange': 'OTCQB',
        'market_cap': 50000000
    }
]

def init_database():
    """Initialize the database with tables and sample data"""
    logger.info("Initializing database...")
    
    # Create the instance directory if it doesn't exist
    instance_dir = Path('instance')
    instance_dir.mkdir(exist_ok=True)
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        # Create all tables
        logger.info("Creating database tables...")
        db.create_all()
        
        # Add sample companies
        logger.info("Adding sample companies...")
        for company_data in COMPANIES:
            existing = Company.query.filter_by(ticker=company_data['ticker']).first()
            if not existing:
                company = Company(
                    ticker=company_data['ticker'],
                    name=company_data['name'],
                    sector=company_data['sector'],
                    industry=company_data['industry'],
                    exchange=company_data['exchange'],
                    market_cap=company_data['market_cap'],
                    earnings_call_has_transcripts=True
                )
                db.session.add(company)
                logger.info(f"Added company: {company_data['ticker']}")
        
        # Commit companies
        db.session.commit()
        
        # Add sample transcripts and sentiment data
        logger.info("Adding sample transcripts and sentiment data...")
        companies = Company.query.all()
        
        for company in companies:
            # Add a sample transcript for Q1 2025
            existing_transcript = Transcript.query.filter_by(
                company_id=company.id,
                fiscal_year=2025,
                fiscal_quarter=1
            ).first()
            
            if not existing_transcript:
                transcript = Transcript(
                    company_id=company.id,
                    call_date=date(2025, 4, 15),  # Q1 2025 earnings call
                    fiscal_year=2025,
                    fiscal_quarter=1,
                    raw_text=f"Sample earnings call transcript for {company.name} Q1 2025. The company showed strong performance with positive outlook for the remainder of the year. Management expressed confidence in their product pipeline and market position.",
                    cleaned_text=f"Sample earnings call transcript for {company.name} Q1 2025. The company showed strong performance with positive outlook for the remainder of the year. Management expressed confidence in their product pipeline and market position.",
                    word_count=35
                )
                db.session.add(transcript)
                db.session.flush()  # Get the ID
                
                # Add sentiment analysis
                sentiment_score = 0.2 if company.ticker in ['HROW', 'RYTM'] else 0.1 if company.ticker in ['LQDA', 'CDXS'] else -0.1
                sentiment = SentimentAnalysis(
                    transcript_id=transcript.id,
                    overall_sentiment=sentiment_score,
                    management_confidence_score=0.15,
                    guidance_sentiment=sentiment_score * 0.8,
                    product_mentions=[],
                    confidence_indicators={},
                    key_topics=['earnings', 'guidance', 'performance'],
                    sentiment_by_section={'overview': sentiment_score, 'outlook': sentiment_score * 1.2},
                    gpt_enhanced=False
                )
                db.session.add(sentiment)
                
                # Add trend analysis
                trend_category = 'improving' if sentiment_score > 0.15 else 'stable' if sentiment_score > -0.05 else 'declining'
                trend = TrendAnalysis(
                    company_id=company.id,
                    analysis_date=date(2025, 4, 20),
                    trend_category=trend_category,
                    sentiment_change=sentiment_score,
                    confidence_change=0.1,
                    key_changes=[{'factor': f'{company.name} performance indicators', 'impact': 'positive' if sentiment_score > 0 else 'negative'}]
                )
                db.session.add(trend)
                
                logger.info(f"Added sample data for {company.ticker}")
        
        # Add sample alerts
        logger.info("Adding sample alerts...")
        for i, company in enumerate(companies[:3]):  # Only first 3 companies
            alert = Alert(
                company_id=company.id,
                alert_type='sentiment_change',
                severity='medium' if i % 2 == 0 else 'high',
                message=f"Sentiment change detected for {company.name}",
                resolved=False
            )
            db.session.add(alert)
        
        # Add sample watchlist entries
        logger.info("Adding sample watchlist entries...")
        for company in companies[:2]:  # First 2 companies
            watchlist_entry = Watchlist(
                user_id='default_user',
                company_id=company.id,
                alert_threshold=0.2
            )
            db.session.add(watchlist_entry)
        
        # Add sample monthly report
        logger.info("Adding sample monthly report...")
        report = MonthlyReport(
            report_date=date(2025, 4, 30),
            companies_analyzed=len(companies),
            improving_count=2,
            stable_count=2,
            declining_count=2,
            report_data={
                'overview': {
                    'total_companies': len(companies),
                    'market_sentiment': 'Mixed',
                    'key_themes': ['Regulatory approvals', 'Pipeline developments', 'Market expansion']
                },
                'trends_by_category': {
                    'improving': [
                        {'ticker': 'HROW', 'name': 'Harrow Inc', 'sentiment_change': 0.25},
                        {'ticker': 'RYTM', 'name': 'Rhythm Pharmaceuticals', 'sentiment_change': 0.18}
                    ],
                    'stable': [
                        {'ticker': 'LQDA', 'name': 'Liquidia Corporation', 'sentiment_change': 0.05},
                        {'ticker': 'CDXS', 'name': 'Codexis', 'sentiment_change': -0.02}
                    ],
                    'declining': [
                        {'ticker': 'ETON', 'name': 'Eton Pharmaceuticals', 'sentiment_change': -0.15},
                        {'ticker': 'SNWVD', 'name': 'SANUWAVE Health Inc', 'sentiment_change': -0.22}
                    ]
                }
            }
        )
        db.session.add(report)
        
        # Commit all changes
        db.session.commit()
        
        logger.info("Database initialization completed successfully!")
        logger.info(f"Created {len(companies)} companies")
        logger.info(f"Created {len(companies)} transcripts with sentiment analysis")
        logger.info(f"Created {len(companies)} trend analyses")
        logger.info(f"Created 3 sample alerts")
        logger.info(f"Created 2 watchlist entries")
        logger.info(f"Created 1 monthly report")
        
        # List companies
        logger.info("Companies in database:")
        for company in companies:
            logger.info(f"  - {company.ticker}: {company.name}")


if __name__ == '__main__':
    init_database() 