"""API Routes"""
from flask import jsonify, request, current_app
from datetime import datetime, date, timedelta
import logging

from app.api import api_bp
from app.models import db, Company, Transcript, SentimentAnalysis, TrendAnalysis, MonthlyReport, Alert, Watchlist
from app.services.data_collector import DataCollector
from app.services.trend_analyzer import TrendAnalyzer
from app.services.cache_service import get_cache_service
from sqlalchemy import text

logger = logging.getLogger(__name__)
cache = get_cache_service()


# Health check endpoint

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    # Check cache connection
    if cache.enabled:
        try:
            cache.redis_client.ping()
            cache_status = 'healthy'
        except:
            cache_status = 'unhealthy'
    else:
        cache_status = 'disabled'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': db_status,
            'cache': cache_status
        }
    })


# Dashboard endpoints

@api_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Main dashboard data"""
    try:
        # Try to get from cache first
        cache_key = cache.dashboard_key()
        cached_data = cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Get latest trend summary
        trends = TrendAnalysis.get_summary_stats()
        
        # Get recent notable companies
        # First get the latest analysis date
        latest_date = db.session.query(db.func.max(TrendAnalysis.analysis_date)).scalar()
        
        notable = (
            db.session.query(Company, TrendAnalysis)
            .join(TrendAnalysis)
            .filter(TrendAnalysis.analysis_date == latest_date)
            .filter(db.func.abs(TrendAnalysis.sentiment_change) > 0.2)
            .order_by(db.func.abs(TrendAnalysis.sentiment_change).desc())
            .limit(10)
            .all()
        ) if latest_date else []
        
        notable_companies = []
        for company, trend in notable:
            notable_companies.append({
                'ticker': company.ticker,
                'name': company.name,
                'trend_category': trend.trend_category,
                'sentiment_change': float(trend.sentiment_change) if trend.sentiment_change else 0,
                'confidence_change': float(trend.confidence_change) if trend.confidence_change else 0
            })
        
        # Get recent alerts
        recent_alerts = Alert.get_recent_high_severity(days=7)
        
        response_data = {
            'summary': trends,
            'notable_companies': notable_companies,
            'recent_alerts': [alert.to_dict(include_company=True) for alert in recent_alerts[:5]],
            'last_update': datetime.utcnow().isoformat()
        }
        
        # Cache the response for 5 minutes
        cache.set(cache_key, response_data, ttl=300)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500


@api_bp.route('/market-overview', methods=['GET'])
def market_overview():
    """Get market-wide overview"""
    try:
        analyzer = TrendAnalyzer()
        overview = analyzer.get_market_overview()
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Market overview error: {str(e)}")
        return jsonify({'error': 'Failed to load market overview'}), 500


# Company endpoints

@api_bp.route('/companies', methods=['GET'])
def list_companies():
    """List all tracked companies"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        sector = request.args.get('sector', '')
        trend = request.args.get('trend', '')
        
        # Build query
        query = Company.query
        
        if search:
            query = query.filter(
                db.or_(
                    Company.ticker.ilike(f'%{search}%'),
                    Company.name.ilike(f'%{search}%')
                )
            )
        
        if sector:
            query = query.filter(Company.sector == sector)
        
        if trend:
            query = query.join(TrendAnalysis).filter(TrendAnalysis.trend_category == trend)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'companies': [company.to_dict(include_latest=True) for company in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        logger.error(f"List companies error: {str(e)}")
        return jsonify({'error': 'Failed to list companies'}), 500


@api_bp.route('/company/<ticker>', methods=['GET'])
def get_company(ticker):
    """Get detailed company analysis"""
    try:
        # Try to get from cache first
        cache_key = cache.company_key(ticker)
        cached_data = cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Get company info
        company = Company.find_by_ticker(ticker)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get transcript history
        transcripts = (
            Transcript.query
            .filter_by(company_id=company.id)
            .order_by(Transcript.fiscal_year.desc(), Transcript.fiscal_quarter.desc())
            .limit(8)
            .all()
        )
        
        # Get latest trend analysis
        trend = company.latest_trend
        
        # Get recent alerts
        alerts = Alert.get_unresolved(company_id=company.id)
        
        response_data = {
            'company': company.to_dict(),
            'transcripts': [t.to_dict(include_sentiment=True) for t in transcripts],
            'trend': trend.to_dict() if trend else None,
            'alerts': [alert.to_dict() for alert in alerts],
            'sentiment_timeline': _create_sentiment_timeline(transcripts)
        }
        
        # Cache the response for 10 minutes
        cache.set(cache_key, response_data, ttl=600)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Get company error: {str(e)}")
        return jsonify({'error': 'Failed to get company data'}), 500


@api_bp.route('/company/<ticker>/sentiment-timeline', methods=['GET'])
def sentiment_timeline(ticker):
    """Get sentiment evolution over time"""
    try:
        company = Company.find_by_ticker(ticker)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        # Get historical sentiment data
        data = (
            db.session.query(
                Transcript.fiscal_year,
                Transcript.fiscal_quarter,
                Transcript.call_date,
                SentimentAnalysis.overall_sentiment,
                SentimentAnalysis.management_confidence_score,
                SentimentAnalysis.guidance_sentiment,
                SentimentAnalysis.confidence_indicators,
                SentimentAnalysis.product_mentions
            )
            .join(SentimentAnalysis)
            .filter(Transcript.company_id == company.id)
            .order_by(Transcript.fiscal_year.desc(), Transcript.fiscal_quarter.desc())
            .limit(12)
            .all()
        )
        
        timeline = []
        for row in data:
            timeline.append({
                'date': f"{row[0]} Q{row[1]}",
                'call_date': row[2].isoformat() if row[2] else None,
                'sentiment': float(row[3]) if row[3] else 0,
                'confidence': float(row[4]) if row[4] else 0,
                'guidance': float(row[5]) if row[5] else 0,
                'confidence_indicators': row[6] or {},
                'products': row[7] or []
            })
        
        return jsonify({
            'ticker': ticker,
            'company_name': company.name,
            'timeline': timeline
        })
        
    except Exception as e:
        logger.error(f"Sentiment timeline error: {str(e)}")
        return jsonify({'error': 'Failed to get sentiment timeline'}), 500


# Search endpoints

@api_bp.route('/search', methods=['GET'])
def search_companies():
    """Search for companies"""
    try:
        query = request.args.get('q', '')
        if not query or len(query) < 2:
            return jsonify({'results': []})
        
        results = Company.query.filter(
            db.or_(
                Company.ticker.ilike(f'%{query}%'),
                Company.name.ilike(f'%{query}%')
            )
        ).limit(20).all()
        
        return jsonify({
            'results': [
                {
                    'ticker': c.ticker,
                    'name': c.name,
                    'market_cap': float(c.market_cap) if c.market_cap else None,
                    'sector': c.sector
                }
                for c in results
            ]
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500


# Reports endpoints

@api_bp.route('/reports', methods=['GET'])
def list_reports():
    """List monthly reports"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        reports_query = MonthlyReport.query\
            .order_by(MonthlyReport.report_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        reports = []
        for report in reports_query.items:
            reports.append({
                'id': report.id,
                'report_date': report.report_date.isoformat(),
                'companies_analyzed': report.companies_analyzed,
                'improving_count': report.improving_count,
                'stable_count': report.stable_count,
                'declining_count': report.declining_count,
                'created_at': report.created_at.isoformat() if hasattr(report, 'created_at') else None
            })
        
        return jsonify({
            'reports': reports,
            'total': reports_query.total,
            'page': page,
            'per_page': per_page,
            'pages': reports_query.pages
        })
        
    except Exception as e:
        logger.error(f"List reports error: {str(e)}")
        return jsonify({'error': 'Failed to list reports'}), 500


@api_bp.route('/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Get specific monthly report"""
    try:
        report = MonthlyReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Calculate percentages
        total = report.companies_analyzed
        improving_pct = round(report.improving_count / total * 100, 1) if total > 0 else 0
        stable_pct = round(report.stable_count / total * 100, 1) if total > 0 else 0
        declining_pct = round(report.declining_count / total * 100, 1) if total > 0 else 0
        
        return jsonify({
            'report': {
                'id': report.id,
                'report_date': report.report_date.isoformat(),
                'companies_analyzed': report.companies_analyzed,
                'improving_count': report.improving_count,
                'improving_percentage': improving_pct,
                'stable_count': report.stable_count,
                'stable_percentage': stable_pct,
                'declining_count': report.declining_count,
                'declining_percentage': declining_pct,
                'report_data': report.report_data,
                'created_at': report.created_at.isoformat() if hasattr(report, 'created_at') else None
            }
        })
        
    except Exception as e:
        logger.error(f"Get report error: {str(e)}")
        return jsonify({'error': 'Failed to get report'}), 500


# Alerts endpoints

@api_bp.route('/alerts', methods=['GET'])
def list_alerts():
    """List unresolved alerts"""
    try:
        company_id = request.args.get('company_id', type=int)
        alerts = Alert.get_unresolved(company_id=company_id)
        
        return jsonify({
            'alerts': [alert.to_dict(include_company=True) for alert in alerts]
        })
        
    except Exception as e:
        logger.error(f"List alerts error: {str(e)}")
        return jsonify({'error': 'Failed to list alerts'}), 500


@api_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Mark alert as resolved"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        alert.resolve()
        
        return jsonify({
            'message': 'Alert resolved',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Resolve alert error: {str(e)}")
        return jsonify({'error': 'Failed to resolve alert'}), 500


# Watchlist endpoints

@api_bp.route('/watchlist', methods=['GET'])
def get_watchlist():
    """Get user watchlist"""
    try:
        # For now, use a default user ID
        user_id = request.args.get('user_id', 'default_user')
        watchlist = Watchlist.get_user_watchlist(user_id)
        
        return jsonify({
            'watchlist': [item.to_dict() for item in watchlist]
        })
        
    except Exception as e:
        logger.error(f"Get watchlist error: {str(e)}")
        return jsonify({'error': 'Failed to get watchlist'}), 500


@api_bp.route('/watchlist', methods=['POST'])
def add_to_watchlist():
    """Add company to watchlist"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        ticker = data.get('ticker')
        threshold = data.get('alert_threshold', 0.2)
        
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
        
        company = Company.find_by_ticker(ticker)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        watchlist_item = Watchlist.add_to_watchlist(user_id, company.id, threshold)
        
        return jsonify({
            'message': 'Added to watchlist',
            'watchlist_item': watchlist_item.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Add to watchlist error: {str(e)}")
        return jsonify({'error': 'Failed to add to watchlist'}), 500


@api_bp.route('/watchlist/<ticker>', methods=['DELETE'])
def remove_from_watchlist(ticker):
    """Remove company from watchlist"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        company = Company.find_by_ticker(ticker)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        removed = Watchlist.remove_from_watchlist(user_id, company.id)
        
        if removed:
            return jsonify({'message': 'Removed from watchlist'})
        else:
            return jsonify({'error': 'Company not in watchlist'}), 404
            
    except Exception as e:
        logger.error(f"Remove from watchlist error: {str(e)}")
        return jsonify({'error': 'Failed to remove from watchlist'}), 500


# Collection endpoints

@api_bp.route('/collection/run', methods=['POST'])
def run_collection():
    """Manually trigger data collection"""
    try:
        # Check if authorized (implement proper auth)
        # For now, just run it
        
        collector = DataCollector()
        results = collector.run_weekly_collection()
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Run collection error: {str(e)}")
        return jsonify({'error': 'Failed to run collection'}), 500


@api_bp.route('/collection/status', methods=['GET'])
def collection_status():
    """Get collection status"""
    try:
        # Get recent transcript fetch dates
        recent_transcripts = Transcript.get_recent(days=1, limit=10)
        
        # Get API usage stats
        from app.models import APIUsage
        usage_stats = APIUsage.get_usage_summary(days=7)
        
        return jsonify({
            'recent_transcripts': len(recent_transcripts),
            'last_collection': recent_transcripts[0].fmp_fetch_date.isoformat() if recent_transcripts else None,
            'api_usage': usage_stats
        })
        
    except Exception as e:
        logger.error(f"Collection status error: {str(e)}")
        return jsonify({'error': 'Failed to get collection status'}), 500


# Utility functions

def _create_sentiment_timeline(transcripts):
    """Create sentiment timeline data from transcripts"""
    timeline = []
    
    for transcript in transcripts:
        if transcript.sentiment_analysis:
            timeline.append({
                'date': f"{transcript.fiscal_year} Q{transcript.fiscal_quarter}",
                'sentiment': transcript.sentiment_score,
                'confidence': transcript.confidence_score,
                'word_count': transcript.word_count
            })
    
    return timeline 