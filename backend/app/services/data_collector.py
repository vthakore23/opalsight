"""Data Collection Service"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import json

from sqlalchemy import and_

from app.models import db, Company, Transcript, SentimentAnalysis, TrendAnalysis, MonthlyReport
from app.services.earnings_call_client import EarningsCallClient
from app.services.transcript_processor import TranscriptProcessor
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.trend_analyzer import TrendAnalyzer
from app.services.email_service import EmailService
from app.services.pdf_service import PDFService
from config.config import Config

logger = logging.getLogger(__name__)


class DataCollector:
    """Service for automated data collection and analysis"""
    
    def __init__(self, earnings_client: Optional[EarningsCallClient] = None, config: Optional[Config] = None):
        self.config = config or Config()
        self.earnings_client = earnings_client or EarningsCallClient(config=self.config)
        self.transcript_processor = TranscriptProcessor()
        self.sentiment_analyzer = SentimentAnalyzer(config=self.config)
        self.trend_analyzer = TrendAnalyzer()
        self.email_service = EmailService(config=self.config)
        self.pdf_service = PDFService()
        
    def run_monthly_collection(self) -> Dict[str, Any]:
        """Main monthly collection process - runs last Friday of each month"""
        logger.info("Starting monthly transcript collection")
        
        start_time = datetime.utcnow()
        results = {
            'status': 'started',
            'start_time': start_time.isoformat(),
            'companies_updated': 0,
            'new_transcripts': 0,
            'analyses_performed': 0,
            'trends_analyzed': 0,
            'errors': []
        }
        
        try:
            # Step 1: Update company list
            logger.info("Step 1: Updating company list")
            updated_companies = self.update_company_list()
            results['companies_updated'] = updated_companies
            
            # Step 2: Fetch new transcripts (last 30 days)
            logger.info("Step 2: Fetching new transcripts")
            new_transcripts = self.fetch_new_transcripts(days_back=30)
            results['new_transcripts'] = len(new_transcripts)
            
            # Step 3: Process transcripts
            logger.info("Step 3: Processing transcripts")
            processed = self.process_transcripts(new_transcripts)
            
            # Step 4: Run sentiment analysis
            logger.info("Step 4: Running sentiment analysis")
            analyses = self.analyze_transcripts(processed)
            results['analyses_performed'] = len(analyses)
            
            # Step 5: Generate trend analysis
            logger.info("Step 5: Generating trend analyses")
            trends = self.generate_trend_analyses()
            results['trends_analyzed'] = len(trends)
            
            # Step 6: Generate monthly report
            logger.info("Step 6: Generating monthly report")
            report = self.generate_monthly_report(trends)
            results['monthly_report'] = report.id if report else None
            
            results['status'] = 'completed'
            results['end_time'] = datetime.utcnow().isoformat()
            results['duration_seconds'] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Monthly collection complete. Processed {len(new_transcripts)} new transcripts")
            
        except Exception as e:
            logger.error(f"Monthly collection failed: {str(e)}")
            results['status'] = 'failed'
            results['errors'].append(str(e))
            
        return results
    
    def update_company_list(self) -> int:
        """Update list of companies with available transcripts"""
        updated_count = 0
        
        try:
            # Get all companies from Earnings Call API
            companies = self.earnings_client.get_companies_list(
                sector='Healthcare',
                min_market_cap=self.config.MIN_MARKET_CAP
            )
            
            logger.info(f"Found {len(companies)} biotech/medtech companies")
            
            for company_data in companies:
                try:
                    ticker = company_data.get('ticker')
                    if not ticker:
                        continue
                    
                    # Update or create company
                    company = Company.query.filter_by(ticker=ticker).first()
                    
                    if company:
                        # Update existing
                        company.name = company_data.get('name', company.name)
                        company.market_cap = company_data.get('market_cap', company.market_cap)
                        company.sector = company_data.get('sector', company.sector)
                        company.industry = company_data.get('industry', company.industry)
                        company.exchange = company_data.get('exchange', company.exchange)
                        company.earnings_call_has_transcripts = True
                    else:
                        # Create new
                        company = Company(
                            ticker=ticker,
                            name=company_data.get('name'),
                            market_cap=company_data.get('market_cap'),
                            sector=company_data.get('sector'),
                            industry=company_data.get('industry'),
                            exchange=company_data.get('exchange'),
                            earnings_call_has_transcripts=True
                        )
                        db.session.add(company)
                    
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating company {ticker}: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"Updated {updated_count} companies")
            
        except Exception as e:
            logger.error(f"Error updating company list: {str(e)}")
            db.session.rollback()
            
        return updated_count
    
    def fetch_new_transcripts(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch transcripts released in the past month"""
        new_transcripts = []
        
        try:
            # Get recent transcripts from API
            recent_transcripts = self.earnings_client.get_recent_transcripts(days_back=days_back)
            logger.info(f"Found {len(recent_transcripts)} recent transcripts")
            
            for transcript_meta in recent_transcripts:
                try:
                    ticker = transcript_meta.get('ticker')
                    year = transcript_meta.get('year')
                    quarter = transcript_meta.get('quarter')
                    
                    if not all([ticker, year, quarter]):
                        continue
                    
                    # Get company
                    company = Company.query.filter_by(ticker=ticker).first()
                    if not company:
                        logger.warning(f"Company {ticker} not found in database")
                        continue
                    
                    # Check if we already have this transcript
                    exists = Transcript.query.filter_by(
                        company_id=company.id,
                        fiscal_year=year,
                        fiscal_quarter=quarter
                    ).first()
                    
                    if exists:
                        logger.debug(f"Transcript already exists: {ticker} {year}Q{quarter}")
                        continue
                    
                    # Fetch full transcript
                    full_transcript = self.earnings_client.get_transcript(ticker, year, quarter)
                    
                    if full_transcript:
                        full_transcript['company_id'] = company.id
                        new_transcripts.append(full_transcript)
                        logger.info(f"New transcript: {ticker} {year}Q{quarter}")
                    
                except Exception as e:
                    logger.error(f"Error processing transcript: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching new transcripts: {str(e)}")
            
        return new_transcripts
    
    def process_transcripts(self, transcripts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and store transcripts"""
        processed = []
        
        for transcript_data in transcripts:
            try:
                # Process the transcript
                processed_data = self.transcript_processor.process_transcript(transcript_data)
                
                # Create database record
                transcript = Transcript()
                transcript.company_id = transcript_data['company_id']
                transcript.call_date = processed_data.date
                transcript.fiscal_year = processed_data.year
                transcript.fiscal_quarter = processed_data.quarter
                transcript.raw_text = transcript_data.get('content', '')
                transcript.cleaned_text = processed_data.cleaned_text
                transcript.word_count = processed_data.word_count
                
                db.session.add(transcript)
                db.session.flush()  # Get the ID
                
                # Add processing results
                processed_result = {
                    'transcript_id': transcript.id,
                    'company_id': transcript_data['company_id'],
                    'ticker': transcript_data.get('company_ticker'),
                    'processed_data': processed_data
                }
                
                processed.append(processed_result)
                
            except Exception as e:
                logger.error(f"Error processing transcript: {str(e)}")
                continue
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error saving transcripts: {str(e)}")
            db.session.rollback()
            
        return processed
    
    def analyze_transcripts(self, processed_transcripts: List[Dict[str, Any]]) -> List[SentimentAnalysis]:
        """Run sentiment analysis on processed transcripts"""
        analyses = []
        
        for transcript_data in processed_transcripts:
            try:
                # Run sentiment analysis
                analysis_result = self.sentiment_analyzer.analyze_transcript(
                    transcript_data['processed_data']
                )
                
                # Create database record
                sentiment = SentimentAnalysis.create_from_analysis(
                    transcript_data['transcript_id'],
                    analysis_result
                )
                
                db.session.add(sentiment)
                analyses.append(sentiment)
                
                logger.info(f"Analyzed transcript for {transcript_data['ticker']}: "
                          f"sentiment={analysis_result['overall_sentiment']:.2f}, "
                          f"confidence={analysis_result['management_confidence_score']:.2f}")
                
            except Exception as e:
                logger.error(f"Error analyzing transcript {transcript_data['transcript_id']}: {str(e)}")
                continue
        
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Error saving sentiment analyses: {str(e)}")
            db.session.rollback()
            
        return analyses
    
    def generate_trend_analyses(self) -> List[TrendAnalysis]:
        """Generate trend analysis for all companies with new transcripts"""
        trends = []
        
        try:
            # Get companies with recent transcripts
            recent_companies = Company.get_with_recent_transcripts(days=7)
            logger.info(f"Generating trends for {len(recent_companies)} companies")
            
            for company in recent_companies:
                try:
                    # Analyze trend
                    trend_result = self.trend_analyzer.analyze_company_trend(company.id)
                    
                    if trend_result:
                        # Save to database
                        trend_analysis = self.trend_analyzer.save_trend_analysis(trend_result)
                        trends.append(trend_analysis)
                        
                        logger.info(f"Generated trend for {company.ticker}: {trend_result.trend_category}")
                    
                except Exception as e:
                    logger.error(f"Error generating trend for {company.ticker}: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"Error generating trend analyses: {str(e)}")
            
        return trends
    
    def is_month_end(self) -> bool:
        """Check if it's the last Friday of the month"""
        today = date.today()
        # Find next Friday
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:  # Today is Friday
            next_friday = today + timedelta(days=7)
        else:
            next_friday = today + timedelta(days=days_until_friday)
        
        # Check if next Friday is in a different month
        return today.month != next_friday.month
    
    def generate_monthly_report(self, recent_trends: List[TrendAnalysis]) -> Optional[MonthlyReport]:
        """Generate monthly summary report"""
        try:
            # Get market overview
            overview = self.trend_analyzer.get_market_overview()
            
            # Compile report data
            report_data = {
                'overview': overview,
                'report_date': date.today().isoformat(),
                'trends_by_category': {
                    'improving': [],
                    'stable': [],
                    'declining': []
                },
                'significant_changes': [],
                'top_performers': [],
                'worst_performers': []
            }
            
            # Get all trends for the month
            month_start = date.today().replace(day=1)
            all_trends = TrendAnalysis.query.filter(
                TrendAnalysis.analysis_date >= month_start
            ).all()
            
            # Categorize trends
            for trend in all_trends:
                company_data = {
                    'ticker': trend.company.ticker,
                    'name': trend.company.name,
                    'sentiment_change': trend.sentiment_change,
                    'confidence_change': trend.confidence_change
                }
                report_data['trends_by_category'][trend.trend_category].append(company_data)
            
            # Find top performers
            improving_trends = sorted(
                [t for t in all_trends if t.trend_category == 'improving'],
                key=lambda x: x.sentiment_change,
                reverse=True
            )[:5]
            
            report_data['top_performers'] = [
                {
                    'ticker': t.company.ticker,
                    'name': t.company.name,
                    'sentiment_change': t.sentiment_change,
                    'confidence_change': t.confidence_change
                }
                for t in improving_trends
            ]
            
            # Find worst performers
            declining_trends = sorted(
                [t for t in all_trends if t.trend_category == 'declining'],
                key=lambda x: x.sentiment_change
            )[:5]
            
            report_data['worst_performers'] = [
                {
                    'ticker': t.company.ticker,
                    'name': t.company.name,
                    'sentiment_change': t.sentiment_change,
                    'confidence_change': t.confidence_change
                }
                for t in declining_trends
            ]
            
            # Create report record
            report = MonthlyReport(
                report_date=date.today(),
                companies_analyzed=len(all_trends),
                improving_count=len(report_data['trends_by_category']['improving']),
                stable_count=len(report_data['trends_by_category']['stable']),
                declining_count=len(report_data['trends_by_category']['declining']),
                report_data=report_data
            )
            
            db.session.add(report)
            db.session.commit()
            
            logger.info(f"Generated monthly report with {report.companies_analyzed} companies")
            
            # Generate and send PDF report via email
            try:
                # Generate PDF
                pdf_data = self.pdf_service.generate_monthly_report_pdf(report)
                
                # Prepare email data
                email_data = {
                    'report_date': report.report_date.strftime('%B %Y'),
                    'companies_analyzed': report.companies_analyzed,
                    'improving_count': report.improving_count,
                    'improving_percentage': round(report.improving_count / report.companies_analyzed * 100, 1),
                    'stable_count': report.stable_count,
                    'stable_percentage': round(report.stable_count / report.companies_analyzed * 100, 1),
                    'declining_count': report.declining_count,
                    'declining_percentage': round(report.declining_count / report.companies_analyzed * 100, 1),
                    'top_performers': report_data['top_performers'],
                    'worst_performers': report_data['worst_performers'],
                    'report_id': report.id
                }
                
                # Get email recipients (you can customize this)
                recipients = self._get_report_recipients()
                
                if recipients:
                    self.email_service.send_monthly_report(email_data, pdf_data, recipients)
                    logger.info(f"Monthly report email sent to {len(recipients)} recipients")
                
            except Exception as e:
                logger.error(f"Failed to send monthly report email: {str(e)}")
                # Don't fail the whole process if email fails
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating monthly report: {str(e)}")
            db.session.rollback()
            return None
    
    def _get_report_recipients(self) -> List[str]:
        """Get list of email recipients for monthly reports"""
        # TODO: This should be configurable or pulled from a database
        # For now, return a default list or empty list
        recipients = []
        
        # Check environment variable for recipients
        import os
        env_recipients = os.getenv('MONTHLY_REPORT_RECIPIENTS', '')
        if env_recipients:
            recipients = [email.strip() for email in env_recipients.split(',')]
        
        return recipients 