#!/usr/bin/env python3
"""
Automated Scheduler for OpalSight
Handles monthly data collection and report generation
"""
import logging
import schedule
import time
import asyncio
from datetime import datetime, date, timedelta
from threading import Thread
import atexit

from app.services.real_data_collector import collect_q1_2025_data_sync
from app.services.monthly_report_generator import generate_monthly_summary_report
from app.services.email_notification_service import send_notification_email
from app.models import db, MonthlyReport
from config.config import get_config

logger = logging.getLogger(__name__)


class OpalSightScheduler:
    """Automated scheduler for OpalSight tasks"""
    
    def __init__(self, config=None):
        """Initialize the scheduler"""
        self.config = config or get_config()
        self.running = False
        self.scheduler_thread = None
        
        # Schedule monthly data collection (1st of every month at 2 AM UTC)
        schedule.every().month.at("02:00").do(self.run_monthly_collection)
        
        # Schedule weekly data updates (every Friday at 6 AM UTC)
        schedule.every().friday.at("06:00").do(self.run_weekly_update)
        
        # Schedule daily health checks (every day at 12 PM UTC)
        schedule.every().day.at("12:00").do(self.run_health_check)
        
        logger.info("OpalSight scheduler initialized")
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.scheduler_thread = Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Register cleanup on exit
        atexit.register(self.stop)
        
        logger.info("OpalSight scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("OpalSight scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def run_monthly_collection(self):
        """Run monthly data collection and report generation"""
        logger.info("Starting monthly data collection...")
        
        try:
            # 1. Run Q1 2025 data collection
            collection_results = collect_q1_2025_data_sync()
            
            # 2. Generate monthly report
            current_date = date.today()
            report_date = date(current_date.year, current_date.month, 1)  # First of current month
            
            monthly_report = generate_monthly_summary_report(report_date)
            
            # 3. Send notification email
            if monthly_report:
                self._send_monthly_report_notification(monthly_report, collection_results)
            
            logger.info(f"Monthly collection completed successfully: {collection_results}")
            
        except Exception as e:
            logger.error(f"Monthly collection failed: {str(e)}")
            self._send_error_notification("Monthly Collection Failed", str(e))
    
    def run_weekly_update(self):
        """Run weekly data updates"""
        logger.info("Starting weekly data update...")
        
        try:
            # Run a lighter version of data collection
            collection_results = collect_q1_2025_data_sync()
            
            # Log results
            logger.info(f"Weekly update completed: {collection_results}")
            
            # Send summary if significant updates
            if collection_results.get('transcripts_analyzed', 0) > 0:
                self._send_weekly_update_notification(collection_results)
            
        except Exception as e:
            logger.error(f"Weekly update failed: {str(e)}")
    
    def run_health_check(self):
        """Run daily health check"""
        logger.info("Running daily health check...")
        
        try:
            # Check database connectivity
            db_healthy = self._check_database_health()
            
            # Check API endpoints
            api_healthy = self._check_api_health()
            
            # Check recent data freshness
            data_fresh = self._check_data_freshness()
            
            health_status = {
                'database': db_healthy,
                'api': api_healthy,
                'data_freshness': data_fresh,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Health check completed: {health_status}")
            
            # Send alert if any issues
            if not all([db_healthy, api_healthy, data_fresh]):
                self._send_health_alert(health_status)
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def _check_database_health(self):
        """Check database connectivity"""
        try:
            # Simple query to check database
            result = db.session.execute("SELECT 1").fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def _check_api_health(self):
        """Check external API connectivity"""
        try:
            from app.services.earnings_call_client import EarningsCallClient
            from app.services.fmp_client import FMPClient
            
            # Test API connections
            earnings_client = EarningsCallClient(config=self.config)
            fmp_client = FMPClient(config=self.config)
            
            earnings_healthy = earnings_client.test_connection()
            fmp_healthy = fmp_client.test_connection()
            
            return earnings_healthy and fmp_healthy
        except Exception as e:
            logger.error(f"API health check failed: {str(e)}")
            return False
    
    def _check_data_freshness(self):
        """Check if data is fresh (updated within last 7 days)"""
        try:
            from app.models import Transcript
            
            # Check for recent transcripts
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = Transcript.query.filter(Transcript.created_at >= week_ago).count()
            
            return recent_count > 0
        except Exception as e:
            logger.error(f"Data freshness check failed: {str(e)}")
            return False
    
    def _send_monthly_report_notification(self, monthly_report, collection_results):
        """Send monthly report notification email"""
        try:
            subject = f"OpalSight Monthly Report - {monthly_report.report_date.strftime('%B %Y')}"
            
            message = f"""
            OpalSight Monthly Report Generated Successfully
            
            Report Date: {monthly_report.report_date.strftime('%B %Y')}
            Companies Analyzed: {monthly_report.companies_analyzed}
            
            Trend Summary:
            - Improving: {monthly_report.improving_count} companies
            - Stable: {monthly_report.stable_count} companies  
            - Declining: {monthly_report.declining_count} companies
            
            Collection Results:
            - Transcripts Fetched: {collection_results.get('transcripts_fetched', 0)}
            - Transcripts Analyzed: {collection_results.get('transcripts_analyzed', 0)}
            - Trends Generated: {collection_results.get('trends_generated', 0)}
            - Alerts Created: {collection_results.get('alerts_created', 0)}
            
            View the full report at: https://opalsight.com/reports
            
            Generated automatically by OpalSight Scheduler
            """
            
            send_notification_email(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send monthly report notification: {str(e)}")
    
    def _send_weekly_update_notification(self, collection_results):
        """Send weekly update notification"""
        try:
            subject = "OpalSight Weekly Update"
            
            message = f"""
            OpalSight Weekly Data Update Completed
            
            Update Summary:
            - Transcripts Analyzed: {collection_results.get('transcripts_analyzed', 0)}
            - New Trends: {collection_results.get('trends_generated', 0)}
            - New Alerts: {collection_results.get('alerts_created', 0)}
            
            View latest insights at: https://opalsight.com/q1-analytics
            
            Generated automatically by OpalSight Scheduler
            """
            
            send_notification_email(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send weekly update notification: {str(e)}")
    
    def _send_health_alert(self, health_status):
        """Send health alert notification"""
        try:
            subject = "OpalSight Health Alert"
            
            issues = []
            if not health_status['database']:
                issues.append("Database connectivity issues")
            if not health_status['api']:
                issues.append("External API connectivity issues")
            if not health_status['data_freshness']:
                issues.append("Data not updated recently (>7 days)")
            
            message = f"""
            OpalSight Health Check Alert
            
            Issues Detected:
            {chr(10).join(f"- {issue}" for issue in issues)}
            
            Timestamp: {health_status['timestamp']}
            
            Please check the system status and logs.
            
            Generated automatically by OpalSight Scheduler
            """
            
            send_notification_email(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send health alert: {str(e)}")
    
    def _send_error_notification(self, task_name, error_message):
        """Send error notification"""
        try:
            subject = f"OpalSight Error: {task_name}"
            
            message = f"""
            OpalSight Scheduler Error
            
            Task: {task_name}
            Error: {error_message}
            Timestamp: {datetime.utcnow().isoformat()}
            
            Please check the system logs for more details.
            
            Generated automatically by OpalSight Scheduler
            """
            
            send_notification_email(subject, message)
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
    
    def force_run_task(self, task_name):
        """Manually trigger a scheduled task"""
        try:
            if task_name == 'monthly_collection':
                self.run_monthly_collection()
            elif task_name == 'weekly_update':
                self.run_weekly_update()
            elif task_name == 'health_check':
                self.run_health_check()
            else:
                raise ValueError(f"Unknown task: {task_name}")
            
            logger.info(f"Manually triggered task: {task_name}")
            
        except Exception as e:
            logger.error(f"Failed to run task {task_name}: {str(e)}")
            raise
    
    def get_schedule_info(self):
        """Get information about scheduled jobs"""
        jobs_info = []
        
        for job in schedule.jobs:
            next_run = job.next_run.isoformat() if job.next_run else 'Not scheduled'
            jobs_info.append({
                'job': str(job.job_func.__name__),
                'interval': str(job.interval),
                'unit': job.unit,
                'next_run': next_run
            })
        
        return {
            'running': self.running,
            'jobs': jobs_info
        }


# Global scheduler instance
_scheduler = None


def get_scheduler():
    """Get the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = OpalSightScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None 