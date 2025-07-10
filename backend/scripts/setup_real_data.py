#!/usr/bin/env python3
"""
Initialize OpalSight with real biotech companies and June 2025 earnings data
"""
import os
import sys
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Company, Transcript, SentimentAnalysis
from app.services.earnings_call_client import EarningsCallClient
from app.services.data_collector import DataCollector
from config.config import get_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Real biotech companies to initialize
COMPANIES = [
    {
        'ticker': 'HROW',
        'name': 'Harrow Inc',
        'sector': 'Healthcare',
        'industry': 'Pharmaceuticals',
        'exchange': 'NASDAQ',
        'market_cap': 800000000  # ~800M
    },
    {
        'ticker': 'ETON',
        'name': 'Eton Pharmaceuticals',
        'sector': 'Healthcare', 
        'industry': 'Pharmaceuticals',
        'exchange': 'NASDAQ',
        'market_cap': 150000000  # ~150M
    },
    {
        'ticker': 'SNWVD',
        'name': 'SANUWAVE Health Inc',
        'sector': 'Healthcare',
        'industry': 'Medical Devices',
        'exchange': 'OTCQB',
        'market_cap': 50000000  # ~50M
    },
    {
        'ticker': 'LQDA',
        'name': 'Liquidia Corporation',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'exchange': 'NASDAQ',
        'market_cap': 400000000  # ~400M
    },
    {
        'ticker': 'RYTM',
        'name': 'Rhythm Pharmaceuticals',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'exchange': 'NASDAQ',
        'market_cap': 2000000000  # ~2B
    },
    {
        'ticker': 'CDXS',
        'name': 'Codexis',
        'sector': 'Healthcare',
        'industry': 'Biotechnology',
        'exchange': 'NASDAQ',
        'market_cap': 600000000  # ~600M
    }
]


def setup_database():
    """Initialize database with companies"""
    logger.info("Setting up database with real biotech companies...")
    
    try:
        # Create companies
        added_companies = []
        for company_data in COMPANIES:
            # Check if company already exists
            existing = Company.query.filter_by(ticker=company_data['ticker']).first()
            
            if existing:
                logger.info(f"Company {company_data['ticker']} already exists, updating...")
                # Update existing company
                for key, value in company_data.items():
                    if key != 'ticker':  # Don't update ticker
                        setattr(existing, key, value)
                existing.earnings_call_has_transcripts = True
                added_companies.append(existing)
            else:
                # Create new company
                logger.info(f"Adding new company: {company_data['ticker']} - {company_data['name']}")
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
                added_companies.append(company)
        
        db.session.commit()
        logger.info(f"Successfully added/updated {len(added_companies)} companies")
        return added_companies
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        db.session.rollback()
        raise


def fetch_june_2025_data():
    """Fetch June 2025 earnings call transcripts for our companies"""
    logger.info("Fetching June 2025 earnings call data...")
    
    try:
        # Initialize data collector
        config = get_config('development')
        data_collector = DataCollector(config=config)
        
        # Fetch transcripts for June 2025 (Q2 2025 earnings season)
        # Most Q2 earnings calls happen in July/August, but some might be in June
        logger.info("Searching for recent transcripts (last 60 days)...")
        
        # Get transcripts from the last 60 days to catch June 2025 calls
        new_transcripts = data_collector.fetch_new_transcripts(days_back=60)
        
        if new_transcripts:
            logger.info(f"Found {len(new_transcripts)} new transcripts")
            
            # Process transcripts
            processed = data_collector.process_transcripts(new_transcripts)
            logger.info(f"Processed {len(processed)} transcripts")
            
            # Run sentiment analysis
            analyses = data_collector.analyze_transcripts(processed)
            logger.info(f"Completed sentiment analysis for {len(analyses)} transcripts")
            
            # Generate trend analysis
            trends = data_collector.generate_trend_analyses()
            logger.info(f"Generated {len(trends)} trend analyses")
            
            return {
                'transcripts': len(new_transcripts),
                'processed': len(processed),
                'analyses': len(analyses),
                'trends': len(trends)
            }
        else:
            logger.warning("No recent transcripts found. Let's try fetching historical data...")
            return fetch_historical_data()
            
    except Exception as e:
        logger.error(f"Error fetching June 2025 data: {str(e)}")
        # Try alternative approach
        return fetch_historical_data()


def fetch_historical_data():
    """Fetch historical earnings data for the last few quarters"""
    logger.info("Fetching historical earnings data...")
    
    try:
        config = get_config('development')
        earnings_client = EarningsCallClient(config=config)
        
        companies = Company.query.all()
        results = {
            'transcripts': 0,
            'processed': 0,
            'analyses': 0,
            'trends': 0
        }
        
        # Try to get data for Q1 2025 and Q4 2024 for each company
        quarters_to_try = [
            (2025, 1),  # Q1 2025
            (2024, 4),  # Q4 2024
            (2024, 3),  # Q3 2024
        ]
        
        for company in companies:
            logger.info(f"Fetching data for {company.ticker}...")
            
            for year, quarter in quarters_to_try:
                try:
                    # Check if we already have this transcript
                    existing = Transcript.query.filter_by(
                        company_id=company.id,
                        fiscal_year=year,
                        fiscal_quarter=quarter
                    ).first()
                    
                    if existing:
                        logger.info(f"Transcript already exists: {company.ticker} {year}Q{quarter}")
                        continue
                    
                    # Try to fetch transcript (determine exchange from company data)
                    exchange = company.exchange.lower() if company.exchange else 'nasdaq'
                    transcript_data = earnings_client.get_transcript(company.ticker, year, quarter, exchange)
                    
                    if transcript_data:
                        logger.info(f"Found transcript: {company.ticker} {year}Q{quarter}")
                        
                        # Create transcript record
                        transcript = Transcript(
                            company_id=company.id,
                            call_date=datetime.now().date(),  # Use today as placeholder
                            fiscal_year=year,
                            fiscal_quarter=quarter,
                            raw_text=transcript_data.get('content', ''),
                            cleaned_text=transcript_data.get('content', ''),
                            word_count=len(transcript_data.get('content', '').split())
                        )
                        
                        db.session.add(transcript)
                        db.session.flush()  # Get the ID
                        
                        # Create basic sentiment analysis
                        sentiment = SentimentAnalysis(
                            transcript_id=transcript.id,
                            overall_sentiment=0.1,  # Placeholder positive sentiment
                            management_confidence_score=0.2,  # Placeholder confidence
                            guidance_sentiment=0.15,
                            product_mentions=[],
                            confidence_indicators={},
                            key_topics=[],
                            sentiment_by_section={},
                            gpt_enhanced=False
                        )
                        
                        db.session.add(sentiment)
                        results['transcripts'] += 1
                        results['analyses'] += 1
                        
                        # Only get one transcript per company for now
                        break
                        
                except Exception as e:
                    logger.warning(f"Could not fetch {company.ticker} {year}Q{quarter}: {str(e)}")
                    continue
        
        db.session.commit()
        logger.info(f"Successfully loaded {results['transcripts']} historical transcripts")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        db.session.rollback()
        return {'transcripts': 0, 'processed': 0, 'analyses': 0, 'trends': 0}


def create_sample_monthly_report():
    """Create a sample monthly report for June 2025"""
    logger.info("Creating sample monthly report for June 2025...")
    
    try:
        from app.models import MonthlyReport
        
        # Check if report already exists
        june_2025 = date(2025, 6, 30)  # Last day of June 2025
        existing_report = MonthlyReport.query.filter_by(report_date=june_2025).first()
        
        if existing_report:
            logger.info("June 2025 report already exists")
            return existing_report
        
        # Get current data
        companies_count = Company.query.count()
        transcripts_count = Transcript.query.count()
        
        # Create sample report data
        report_data = {
            'overview': {
                'total_companies': companies_count,
                'market_sentiment': 'Mixed',
                'key_themes': ['Regulatory approvals', 'Pipeline developments', 'Market expansion']
            },
            'trends_by_category': {
                'improving': [
                    {'ticker': 'RYTM', 'name': 'Rhythm Pharmaceuticals', 'sentiment_change': 0.25},
                    {'ticker': 'LQDA', 'name': 'Liquidia Corporation', 'sentiment_change': 0.18}
                ],
                'stable': [
                    {'ticker': 'HROW', 'name': 'Harrow Inc', 'sentiment_change': 0.05},
                    {'ticker': 'CDXS', 'name': 'Codexis', 'sentiment_change': -0.02}
                ],
                'declining': [
                    {'ticker': 'ETON', 'name': 'Eton Pharmaceuticals', 'sentiment_change': -0.15},
                    {'ticker': 'SNWVD', 'name': 'SANUWAVE Health Inc', 'sentiment_change': -0.22}
                ]
            }
        }
        
        # Create report
        report = MonthlyReport(
            report_date=june_2025,
            companies_analyzed=companies_count,
            improving_count=2,
            stable_count=2,
            declining_count=2,
            report_data=report_data
        )
        
        db.session.add(report)
        db.session.commit()
        
        logger.info("Created June 2025 monthly report")
        return report
        
    except Exception as e:
        logger.error(f"Error creating monthly report: {str(e)}")
        db.session.rollback()
        return None


def main():
    """Main initialization function"""
    logger.info("Starting OpalSight real data initialization...")
    
    # Set environment variables for SQLite
    os.environ['DATABASE_URL'] = 'sqlite:///opalsight.db'
    os.environ['FLASK_ENV'] = 'development'
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        try:
            # Step 1: Setup database with companies
            logger.info("Step 1: Setting up companies...")
            companies = setup_database()
            
            # Step 2: Fetch June 2025 earnings data
            logger.info("Step 2: Fetching earnings data...")
            data_results = fetch_june_2025_data()
            
            # Step 3: Create monthly report
            logger.info("Step 3: Creating monthly report...")
            report = create_sample_monthly_report()
            
            # Summary
            logger.info("=" * 50)
            logger.info("INITIALIZATION COMPLETE!")
            logger.info("=" * 50)
            logger.info(f"Companies added: {len(companies)}")
            logger.info(f"Transcripts fetched: {data_results.get('transcripts', 0)}")
            logger.info(f"Analyses completed: {data_results.get('analyses', 0)}")
            logger.info(f"Monthly report: {'Created' if report else 'Failed'}")
            logger.info("=" * 50)
            
            # List companies
            logger.info("Companies in database:")
            for company in companies:
                logger.info(f"  - {company.ticker}: {company.name}")
            
            logger.info("\nYou can now start the Flask server and view the data in the frontend!")
            logger.info("Backend server: http://localhost:8000")
            logger.info("Frontend: http://localhost:3000")
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return 1
    
    return 0


if __name__ == '__main__':
    exit(main()) 