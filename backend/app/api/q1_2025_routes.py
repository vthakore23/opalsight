#!/usr/bin/env python3
"""
Q1 2025 Real Data Collection and PDF Report API Routes
"""
import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, jsonify, request, send_file, current_app
from io import BytesIO
import asyncio
import traceback

from app.services.real_data_collector import collect_q1_2025_data_sync, RealDataCollector
from app.services.pdf_report_generator import generate_company_pdf_report, generate_monthly_pdf_report
from app.models import db, Company, MonthlyReport, Transcript, SentimentAnalysis, TrendAnalysis, Alert
from config.config import get_config

logger = logging.getLogger(__name__)

q1_2025_bp = Blueprint('q1_2025', __name__, url_prefix='/api/q1-2025')


@q1_2025_bp.route('/collect', methods=['POST'])
def collect_real_data():
    """Trigger Q1 2025 real data collection"""
    try:
        logger.info("Starting Q1 2025 real data collection...")
        
        # Get parameters
        data = request.get_json() or {}
        force_refresh = data.get('force_refresh', False)
        
        # Run the collection
        results = collect_q1_2025_data_sync()
        
        return jsonify({
            'success': True,
            'message': 'Q1 2025 data collection completed successfully',
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Q1 2025 data collection failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Q1 2025 data collection failed',
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@q1_2025_bp.route('/status', methods=['GET'])
def get_collection_status():
    """Get status of Q1 2025 data collection"""
    try:
        # Get collection statistics
        from app.models import Transcript, SentimentAnalysis, TrendAnalysis
        
        # Count Q1 2025 transcripts
        q1_2025_transcripts = Transcript.query.filter_by(fiscal_year=2025, fiscal_quarter=1).count()
        
        # Count recent transcripts (last 7 days)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_transcripts = Transcript.query.filter(Transcript.created_at >= recent_date).count()
        
        # Count total companies with Q1 2025 data
        companies_with_q1_data = db.session.query(Company.id).join(Transcript).filter(
            Transcript.fiscal_year == 2025,
            Transcript.fiscal_quarter == 1
        ).distinct().count()
        
        # Get latest trend analysis
        latest_trends = TrendAnalysis.query.order_by(TrendAnalysis.created_at.desc()).limit(5).all()
        
        return jsonify({
            'q1_2025_transcripts': q1_2025_transcripts,
            'recent_transcripts': recent_transcripts,
            'companies_with_q1_data': companies_with_q1_data,
            'latest_trends': [trend.to_dict(include_company=True) for trend in latest_trends],
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting collection status: {str(e)}")
        return jsonify({'error': 'Failed to get collection status'}), 500


@q1_2025_bp.route('/companies', methods=['GET'])
def get_q1_2025_companies():
    """Get companies with Q1 2025 data"""
    try:
        # Get companies with Q1 2025 transcripts
        companies_query = db.session.query(Company).join(Transcript).filter(
            Transcript.fiscal_year == 2025,
            Transcript.fiscal_quarter == 1
        ).distinct()
        
        companies = companies_query.all()
        
        result = []
        for company in companies:
            # Get Q1 2025 transcript
            q1_transcript = Transcript.query.filter_by(
                company_id=company.id,
                fiscal_year=2025,
                fiscal_quarter=1
            ).first()
            
            company_data = company.to_dict(include_latest=True)
            
            if q1_transcript and q1_transcript.sentiment_analysis:
                company_data['q1_2025_sentiment'] = {
                    'overall_sentiment': q1_transcript.sentiment_analysis.overall_sentiment,
                    'management_confidence': q1_transcript.sentiment_analysis.management_confidence_score,
                    'sentiment_label': q1_transcript.sentiment_analysis.sentiment_label,
                    'has_quotes': len(q1_transcript.sentiment_analysis.get_key_quotes()) > 0,
                    'has_guidance': len(q1_transcript.sentiment_analysis.get_extracted_guidance()) > 0
                }
            
            result.append(company_data)
        
        return jsonify({
            'companies': result,
            'total_count': len(result)
        })
        
    except Exception as e:
        logger.error(f"Error getting Q1 2025 companies: {str(e)}")
        return jsonify({'error': 'Failed to get Q1 2025 companies'}), 500


@q1_2025_bp.route('/report/company/<ticker>', methods=['GET'])
def generate_company_report(ticker):
    """Generate comprehensive PDF report for a company"""
    try:
        # Verify company exists
        company = Company.find_by_ticker(ticker)
        if not company:
            return jsonify({'error': f'Company {ticker} not found'}), 404
        
        # Get parameters
        include_quotes = request.args.get('include_quotes', 'true').lower() == 'true'
        
        # Generate PDF report
        pdf_bytes = generate_company_pdf_report(ticker, include_quotes)
        
        # Create response
        pdf_buffer = BytesIO(pdf_bytes)
        filename = f"OpalSight_{ticker}_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating company report for {ticker}: {str(e)}")
        return jsonify({'error': f'Failed to generate report for {ticker}'}), 500


@q1_2025_bp.route('/report/monthly/<report_date>', methods=['GET'])
def generate_monthly_report_pdf(report_date):
    """Generate monthly industry PDF report"""
    try:
        # Parse date
        try:
            report_date_obj = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Check if monthly report exists
        monthly_report = MonthlyReport.query.filter_by(report_date=report_date_obj).first()
        if not monthly_report:
            return jsonify({'error': f'Monthly report for {report_date} not found'}), 404
        
        # Generate PDF report
        pdf_bytes = generate_monthly_pdf_report(report_date_obj)
        
        # Create response
        pdf_buffer = BytesIO(pdf_bytes)
        filename = f"OpalSight_Monthly_Report_{report_date}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating monthly report for {report_date}: {str(e)}")
        return jsonify({'error': f'Failed to generate monthly report for {report_date}'}), 500


@q1_2025_bp.route('/insights', methods=['GET'])
def get_q1_2025_insights():
    """Get comprehensive Q1 2025 insights and analysis"""
    try:
        # Get Q1 2025 data summary
        from app.models import Transcript, SentimentAnalysis, TrendAnalysis, Alert
        
        # Q1 2025 transcripts with sentiment
        q1_transcripts = db.session.query(Transcript).join(SentimentAnalysis).filter(
            Transcript.fiscal_year == 2025,
            Transcript.fiscal_quarter == 1
        ).all()
        
        if not q1_transcripts:
            return jsonify({
                'message': 'No Q1 2025 data available yet',
                'insights': {}
            })
        
        # Calculate insights
        sentiments = [t.sentiment_analysis.overall_sentiment for t in q1_transcripts if t.sentiment_analysis.overall_sentiment is not None]
        confidences = [t.sentiment_analysis.management_confidence_score for t in q1_transcripts if t.sentiment_analysis.management_confidence_score is not None]
        
        # Aggregate quotes and guidance
        all_quotes = []
        all_guidance = []
        
        for transcript in q1_transcripts:
            if transcript.sentiment_analysis:
                all_quotes.extend(transcript.sentiment_analysis.get_key_quotes())
                all_guidance.extend(transcript.sentiment_analysis.get_extracted_guidance())
        
        # Calculate trend distribution
        trends = TrendAnalysis.query.filter(TrendAnalysis.analysis_date >= date(2025, 4, 1)).all()
        trend_distribution = {}
        for trend in trends:
            category = trend.trend_category
            trend_distribution[category] = trend_distribution.get(category, 0) + 1
        
        # Recent alerts
        recent_alerts = Alert.query.filter(Alert.created_at >= datetime(2025, 4, 1)).order_by(Alert.created_at.desc()).limit(10).all()
        
        insights = {
            'summary': {
                'total_companies': len(q1_transcripts),
                'avg_sentiment': round(sum(sentiments) / len(sentiments), 3) if sentiments else 0,
                'avg_confidence': round(sum(confidences) / len(confidences), 3) if confidences else 0,
                'total_quotes': len(all_quotes),
                'total_guidance_items': len(all_guidance)
            },
            'sentiment_distribution': {
                'positive': len([s for s in sentiments if s > 0.1]),
                'neutral': len([s for s in sentiments if -0.1 <= s <= 0.1]),
                'negative': len([s for s in sentiments if s < -0.1])
            },
            'trend_distribution': trend_distribution,
            'top_quotes': all_quotes[:10],  # Top 10 quotes
            'guidance_summary': all_guidance[:10],  # Top 10 guidance items
            'recent_alerts': [alert.to_dict(include_company=True) for alert in recent_alerts],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error getting Q1 2025 insights: {str(e)}")
        return jsonify({'error': 'Failed to get Q1 2025 insights'}), 500


@q1_2025_bp.route('/quotes', methods=['GET'])
def get_key_quotes():
    """Get key quotes from Q1 2025 earnings calls"""
    try:
        # Get parameters
        limit = request.args.get('limit', 50, type=int)
        company_ticker = request.args.get('company', None)
        sentiment_filter = request.args.get('sentiment', None)  # positive, negative, neutral
        
        # Build query
        query = db.session.query(Transcript, SentimentAnalysis, Company).join(SentimentAnalysis).join(Company).filter(
            Transcript.fiscal_year == 2025,
            Transcript.fiscal_quarter == 1
        )
        
        if company_ticker:
            query = query.filter(Company.ticker == company_ticker.upper())
        
        transcripts = query.all()
        
        # Extract and filter quotes
        all_quotes = []
        for transcript, sentiment, company in transcripts:
            quotes = sentiment.get_key_quotes()
            for quote in quotes:
                quote_data = quote.copy() if isinstance(quote, dict) else {}
                quote_data['company'] = {
                    'ticker': company.ticker,
                    'name': company.name
                }
                quote_data['fiscal_period'] = f"{transcript.fiscal_year} Q{transcript.fiscal_quarter}"
                
                # Apply sentiment filter
                if sentiment_filter:
                    quote_sentiment = quote_data.get('sentiment_score', 0)
                    if sentiment_filter == 'positive' and quote_sentiment <= 0.1:
                        continue
                    elif sentiment_filter == 'negative' and quote_sentiment >= -0.1:
                        continue
                    elif sentiment_filter == 'neutral' and (quote_sentiment > 0.1 or quote_sentiment < -0.1):
                        continue
                
                all_quotes.append(quote_data)
        
        # Sort by sentiment score (most extreme first)
        all_quotes.sort(key=lambda x: abs(x.get('sentiment_score', 0)), reverse=True)
        
        return jsonify({
            'quotes': all_quotes[:limit],
            'total_available': len(all_quotes),
            'filters_applied': {
                'company': company_ticker,
                'sentiment': sentiment_filter,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting key quotes: {str(e)}")
        return jsonify({'error': 'Failed to get key quotes'}), 500


@q1_2025_bp.route('/guidance', methods=['GET'])
def get_guidance_summary():
    """Get guidance and forward-looking statements from Q1 2025"""
    try:
        # Get parameters
        limit = request.args.get('limit', 50, type=int)
        company_ticker = request.args.get('company', None)
        metric_type = request.args.get('metric', None)  # revenue, earnings, etc.
        
        # Build query
        query = db.session.query(Transcript, SentimentAnalysis, Company).join(SentimentAnalysis).join(Company).filter(
            Transcript.fiscal_year == 2025,
            Transcript.fiscal_quarter == 1
        )
        
        if company_ticker:
            query = query.filter(Company.ticker == company_ticker.upper())
        
        transcripts = query.all()
        
        # Extract and filter guidance
        all_guidance = []
        for transcript, sentiment, company in transcripts:
            guidance_items = sentiment.get_extracted_guidance()
            for guidance in guidance_items:
                guidance_data = guidance.copy() if isinstance(guidance, dict) else {}
                guidance_data['company'] = {
                    'ticker': company.ticker,
                    'name': company.name
                }
                guidance_data['fiscal_period'] = f"{transcript.fiscal_year} Q{transcript.fiscal_quarter}"
                
                # Apply metric filter
                if metric_type:
                    guidance_metric = guidance_data.get('metric', '').lower()
                    if metric_type.lower() not in guidance_metric:
                        continue
                
                all_guidance.append(guidance_data)
        
        # Sort by confidence level and metric importance
        confidence_order = {'high': 3, 'medium': 2, 'low': 1, 'unknown': 0}
        all_guidance.sort(key=lambda x: confidence_order.get(x.get('confidence', 'unknown'), 0), reverse=True)
        
        return jsonify({
            'guidance': all_guidance[:limit],
            'total_available': len(all_guidance),
            'filters_applied': {
                'company': company_ticker,
                'metric': metric_type,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting guidance summary: {str(e)}")
        return jsonify({'error': 'Failed to get guidance summary'}), 500 