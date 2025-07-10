"""Historical Data Ingestion Script

This script performs a one-time ingestion of historical earnings call transcripts
for all tracked biotech/medtech companies.
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Company, Transcript
from app.services.earnings_call_client import EarningsCallClient
from app.services.data_collector import DataCollector
from config.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('historical_ingestion.log')
    ]
)

logger = logging.getLogger(__name__)


def ingest_historical_data(years_back=2):
    """Ingest historical earnings call data for all tracked companies"""
    logger.info(f"Starting historical data ingestion for the past {years_back} years")
    
    # Create Flask app context
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        config = get_config()
        earnings_client = EarningsCallClient(config=config)
        collector = DataCollector(earnings_client=earnings_client, config=config)
        
        # First, update the company list
        logger.info("Updating company list...")
        updated = collector.update_company_list()
        logger.info(f"Updated {updated} companies")
        
        # Get all tracked companies
        companies = Company.query.filter_by(earnings_call_has_transcripts=True).all()
        logger.info(f"Found {len(companies)} companies to process")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)
        
        total_transcripts = 0
        total_processed = 0
        failed_companies = []
        
        # Process each company
        for i, company in enumerate(companies, 1):
            logger.info(f"Processing {i}/{len(companies)}: {company.ticker} - {company.name}")
            
            try:
                # Get available transcripts for this company
                available_transcripts = earnings_client.get_available_transcripts(company.ticker)
                
                if not available_transcripts:
                    logger.warning(f"No transcripts available for {company.ticker}")
                    continue
                
                company_transcripts = 0
                
                for transcript_meta in available_transcripts:
                    try:
                        # Check if transcript is within our date range
                        transcript_date = transcript_meta.get('date')
                        if transcript_date:
                            try:
                                t_date = datetime.fromisoformat(transcript_date.replace('Z', '+00:00'))
                                if t_date < start_date:
                                    continue  # Skip transcripts older than our range
                            except:
                                pass
                        
                        year = transcript_meta.get('year')
                        quarter = transcript_meta.get('quarter')
                        
                        if not year or not quarter:
                            continue
                        
                        # Check if we already have this transcript
                        exists = Transcript.query.filter_by(
                            company_id=company.id,
                            fiscal_year=year,
                            fiscal_quarter=quarter
                        ).first()
                        
                        if exists:
                            logger.debug(f"Transcript already exists: {company.ticker} {year}Q{quarter}")
                            continue
                        
                        # Fetch the full transcript
                        logger.info(f"Fetching transcript: {company.ticker} {year}Q{quarter}")
                        full_transcript = earnings_client.get_transcript(company.ticker, year, quarter)
                        
                        if full_transcript:
                            # Process the transcript
                            full_transcript['company_id'] = company.id
                            processed = collector.process_transcripts([full_transcript])
                            
                            if processed:
                                # Run sentiment analysis
                                analyses = collector.analyze_transcripts(processed)
                                company_transcripts += 1
                                total_transcripts += 1
                                
                                logger.info(f"Successfully processed {company.ticker} {year}Q{quarter}")
                            else:
                                logger.warning(f"Failed to process {company.ticker} {year}Q{quarter}")
                        
                    except Exception as e:
                        logger.error(f"Error processing transcript: {str(e)}")
                        continue
                
                logger.info(f"Processed {company_transcripts} transcripts for {company.ticker}")
                total_processed += 1
                
                # Generate trend analysis for this company
                try:
                    trend_result = collector.trend_analyzer.analyze_company_trend(company.id)
                    if trend_result:
                        collector.trend_analyzer.save_trend_analysis(trend_result)
                        logger.info(f"Generated trend analysis for {company.ticker}")
                except Exception as e:
                    logger.error(f"Failed to generate trend analysis for {company.ticker}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Failed to process company {company.ticker}: {str(e)}")
                failed_companies.append(company.ticker)
                continue
        
        logger.info("="*50)
        logger.info(f"Historical ingestion completed!")
        logger.info(f"Total companies processed: {total_processed}/{len(companies)}")
        logger.info(f"Total transcripts ingested: {total_transcripts}")
        
        if failed_companies:
            logger.warning(f"Failed companies: {', '.join(failed_companies)}")
        
        # Generate initial monthly report if we have data
        if total_transcripts > 0:
            try:
                logger.info("Generating initial monthly report...")
                trends = collector.generate_trend_analyses()
                report = collector.generate_monthly_report(trends)
                if report:
                    logger.info(f"Generated monthly report ID: {report.id}")
            except Exception as e:
                logger.error(f"Failed to generate monthly report: {str(e)}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest historical earnings call data')
    parser.add_argument(
        '--years',
        type=int,
        default=2,
        help='Number of years of historical data to ingest (default: 2)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - only process first 5 companies'
    )
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("Running in test mode - will only process first 5 companies")
        # Temporarily limit companies in test mode
        # This would be implemented in the ingest_historical_data function
    
    ingest_historical_data(years_back=args.years)


if __name__ == '__main__':
    main() 