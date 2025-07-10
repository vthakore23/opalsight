"""Scheduler for automated data collection"""
import os
import sys
import logging
import schedule
import time
from datetime import datetime, date, timedelta
import calendar

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.data_collector import DataCollector
from app.services.earnings_call_client import EarningsCallClient
from config.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scheduler.log')
    ]
)

logger = logging.getLogger(__name__)


def get_last_friday_of_month(year, month):
    """Get the date of the last Friday of a given month"""
    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]
    last_date = date(year, month, last_day)
    
    # Find the last Friday
    while last_date.weekday() != 4:  # 4 is Friday
        last_date -= timedelta(days=1)
    
    return last_date


def is_last_friday_of_month():
    """Check if today is the last Friday of the month"""
    today = date.today()
    if today.weekday() != 4:  # Not Friday
        return False
    
    # Check if next Friday is in the next month
    next_friday = today + timedelta(days=7)
    return today.month != next_friday.month


def run_monthly_job():
    """Run the monthly collection job"""
    logger.info("="*50)
    logger.info(f"Starting monthly collection job at {datetime.now()}")
    
    try:
        # Create Flask app context
        app = create_app(os.environ.get('FLASK_ENV'))
        
        with app.app_context():
            # Initialize services
            config = get_config()
            earnings_client = EarningsCallClient(config=config)
            collector = DataCollector(earnings_client=earnings_client, config=config)
            
            # Run collection
            results = collector.run_monthly_collection()
            
            # Log results
            logger.info(f"Collection completed: {results}")
            
            if results['status'] == 'completed':
                logger.info(f"Successfully processed {results['new_transcripts']} new transcripts")
                logger.info(f"Generated {results['trends_analyzed']} trend analyses")
                if results.get('monthly_report'):
                    logger.info(f"Generated monthly report ID: {results['monthly_report']}")
            else:
                logger.error(f"Collection failed: {results.get('errors', [])}")
    
    except Exception as e:
        logger.error(f"Monthly job failed: {str(e)}", exc_info=True)
    
    logger.info(f"Monthly collection job finished at {datetime.now()}")
    logger.info("="*50)


def test_connection():
    """Test Earnings Call API connection"""
    logger.info("Testing Earnings Call API connection...")
    
    try:
        app = create_app(os.environ.get('FLASK_ENV'))
        
        with app.app_context():
            config = get_config()
            earnings_client = EarningsCallClient(config=config)
            
            if earnings_client.test_connection():
                logger.info("Earnings Call API connection successful")
                return True
            else:
                logger.error("Earnings Call API connection failed")
                return False
    
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False


def check_and_run_monthly():
    """Check if it's the last Friday of the month and run if so"""
    if is_last_friday_of_month():
        logger.info("Today is the last Friday of the month - running collection")
        run_monthly_job()
    else:
        logger.debug("Not the last Friday of the month - skipping collection")


def main():
    """Main scheduler function"""
    logger.info("Starting OpalSight scheduler")
    
    # Test connection first
    if not test_connection():
        logger.error("Cannot start scheduler - API connection failed")
        sys.exit(1)
    
    # Get configuration
    config = get_config()
    
    # Schedule the monthly job
    schedule_time = config.WEEKLY_COLLECTION_TIME  # Keep same time config
    logger.info(f"Scheduling monthly collection for last Friday of each month at {schedule_time}")
    
    # Check every Friday at the configured time
    schedule.every().friday.at(schedule_time).do(check_and_run_monthly)
    
    # Also schedule a daily health check
    schedule.every().day.at("09:00").do(test_connection)
    
    # Optional: Run immediately on startup (for testing)
    if os.environ.get('RUN_ON_STARTUP', '').lower() == 'true':
        logger.info("Running collection on startup")
        run_monthly_job()
    
    # Keep the scheduler running
    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main() 