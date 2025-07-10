"""Data Export Service"""
import csv
import json
import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import xlsxwriter

from app.models import Company, Transcript, SentimentAnalysis, TrendAnalysis, db

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data in various formats"""
    
    def export_companies_data(self, format: str = 'csv', filters: Dict[str, Any] = None) -> bytes:
        """Export companies data with sentiment analysis"""
        try:
            # Build query
            query = db.session.query(
                Company,
                TrendAnalysis,
                SentimentAnalysis,
                Transcript
            ).join(
                TrendAnalysis, TrendAnalysis.company_id == Company.id, isouter=True
            ).join(
                Transcript, Transcript.company_id == Company.id, isouter=True
            ).join(
                SentimentAnalysis, SentimentAnalysis.transcript_id == Transcript.id, isouter=True
            )
            
            # Apply filters
            if filters:
                if filters.get('sector'):
                    query = query.filter(Company.sector == filters['sector'])
                if filters.get('trend'):
                    query = query.filter(TrendAnalysis.trend_category == filters['trend'])
                if filters.get('min_market_cap'):
                    query = query.filter(Company.market_cap >= filters['min_market_cap'])
            
            results = query.all()
            
            # Prepare data
            data_rows = []
            for company, trend, sentiment, transcript in results:
                row = {
                    'ticker': company.ticker,
                    'company_name': company.name,
                    'sector': company.sector,
                    'industry': company.industry,
                    'market_cap': company.market_cap,
                    'latest_trend': trend.trend_category if trend else None,
                    'sentiment_change': float(trend.sentiment_change) if trend and trend.sentiment_change else None,
                    'confidence_change': float(trend.confidence_change) if trend and trend.confidence_change else None,
                    'latest_sentiment': float(sentiment.overall_sentiment) if sentiment else None,
                    'latest_confidence': float(sentiment.management_confidence_score) if sentiment else None,
                    'last_earnings_date': transcript.call_date.isoformat() if transcript and transcript.call_date else None,
                    'data_export_date': datetime.utcnow().isoformat()
                }
                data_rows.append(row)
            
            # Export based on format
            if format == 'csv':
                return self._export_to_csv(data_rows)
            elif format == 'json':
                return self._export_to_json(data_rows)
            elif format == 'excel':
                return self._export_to_excel(data_rows)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise
    
    def export_company_timeline(self, ticker: str, format: str = 'csv') -> bytes:
        """Export sentiment timeline for a specific company"""
        try:
            company = Company.find_by_ticker(ticker)
            if not company:
                raise ValueError(f"Company not found: {ticker}")
            
            # Get sentiment history
            results = db.session.query(
                Transcript,
                SentimentAnalysis
            ).join(
                SentimentAnalysis
            ).filter(
                Transcript.company_id == company.id
            ).order_by(
                Transcript.fiscal_year.desc(),
                Transcript.fiscal_quarter.desc()
            ).all()
            
            # Prepare timeline data
            timeline_data = []
            for transcript, sentiment in results:
                row = {
                    'ticker': ticker,
                    'company_name': company.name,
                    'fiscal_period': f"{transcript.fiscal_year} Q{transcript.fiscal_quarter}",
                    'call_date': transcript.call_date.isoformat() if transcript.call_date else None,
                    'overall_sentiment': float(sentiment.overall_sentiment) if sentiment.overall_sentiment else None,
                    'management_confidence': float(sentiment.management_confidence_score) if sentiment.management_confidence_score else None,
                    'guidance_sentiment': float(sentiment.guidance_sentiment) if sentiment.guidance_sentiment else None,
                    'word_count': transcript.word_count,
                    'product_mentions': len(sentiment.product_mentions) if sentiment.product_mentions else 0,
                    'positive_indicators': sentiment.confidence_indicators.get('positive_count', 0) if sentiment.confidence_indicators else 0,
                    'negative_indicators': sentiment.confidence_indicators.get('negative_count', 0) if sentiment.confidence_indicators else 0
                }
                timeline_data.append(row)
            
            # Export based on format
            if format == 'csv':
                return self._export_to_csv(timeline_data)
            elif format == 'json':
                return self._export_to_json(timeline_data)
            elif format == 'excel':
                return self._export_to_excel(timeline_data, sheet_name=f"{ticker}_Timeline")
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Timeline export failed: {str(e)}")
            raise
    
    def export_market_summary(self, format: str = 'excel') -> bytes:
        """Export comprehensive market summary"""
        try:
            # Get trend distribution
            trend_stats = TrendAnalysis.get_summary_stats()
            
            # Get sector breakdown
            sector_query = db.session.query(
                Company.sector,
                db.func.count(Company.id).label('count'),
                db.func.avg(Company.market_cap).label('avg_market_cap')
            ).group_by(Company.sector).all()
            
            # Get top movers
            top_movers_query = db.session.query(
                Company,
                TrendAnalysis
            ).join(
                TrendAnalysis
            ).order_by(
                db.func.abs(TrendAnalysis.sentiment_change).desc()
            ).limit(20).all()
            
            if format == 'excel':
                # Create Excel workbook with multiple sheets
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                
                # Summary sheet
                summary_sheet = workbook.add_worksheet('Summary')
                summary_sheet.write(0, 0, 'Market Summary Report')
                summary_sheet.write(1, 0, f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}')
                
                row = 3
                summary_sheet.write(row, 0, 'Trend Distribution')
                row += 1
                for trend, stats in trend_stats.items():
                    summary_sheet.write(row, 0, trend.capitalize())
                    summary_sheet.write(row, 1, stats['count'])
                    summary_sheet.write(row, 2, f"{stats['percentage']:.1f}%")
                    row += 1
                
                # Sector breakdown sheet
                sector_sheet = workbook.add_worksheet('Sectors')
                sector_sheet.write(0, 0, 'Sector')
                sector_sheet.write(0, 1, 'Company Count')
                sector_sheet.write(0, 2, 'Avg Market Cap (M)')
                
                for idx, (sector, count, avg_cap) in enumerate(sector_query, 1):
                    sector_sheet.write(idx, 0, sector or 'Unknown')
                    sector_sheet.write(idx, 1, count)
                    sector_sheet.write(idx, 2, round(avg_cap / 1_000_000, 2) if avg_cap else 0)
                
                # Top movers sheet
                movers_sheet = workbook.add_worksheet('Top Movers')
                headers = ['Ticker', 'Company', 'Sector', 'Trend', 'Sentiment Change', 'Confidence Change']
                for col, header in enumerate(headers):
                    movers_sheet.write(0, col, header)
                
                for idx, (company, trend) in enumerate(top_movers_query, 1):
                    movers_sheet.write(idx, 0, company.ticker)
                    movers_sheet.write(idx, 1, company.name)
                    movers_sheet.write(idx, 2, company.sector or 'Unknown')
                    movers_sheet.write(idx, 3, trend.trend_category)
                    movers_sheet.write(idx, 4, float(trend.sentiment_change) if trend.sentiment_change else 0)
                    movers_sheet.write(idx, 5, float(trend.confidence_change) if trend.confidence_change else 0)
                
                workbook.close()
                output.seek(0)
                return output.getvalue()
                
            else:
                # For other formats, return summary data
                summary_data = {
                    'generated_at': datetime.utcnow().isoformat(),
                    'trend_distribution': trend_stats,
                    'sector_breakdown': [
                        {
                            'sector': sector or 'Unknown',
                            'count': count,
                            'avg_market_cap': float(avg_cap) if avg_cap else 0
                        }
                        for sector, count, avg_cap in sector_query
                    ],
                    'top_movers': [
                        {
                            'ticker': company.ticker,
                            'name': company.name,
                            'trend': trend.trend_category,
                            'sentiment_change': float(trend.sentiment_change) if trend.sentiment_change else 0
                        }
                        for company, trend in top_movers_query
                    ]
                }
                
                if format == 'json':
                    return json.dumps(summary_data, indent=2).encode('utf-8')
                else:
                    raise ValueError(f"Unsupported format for market summary: {format}")
                    
        except Exception as e:
            logger.error(f"Market summary export failed: {str(e)}")
            raise
    
    def _export_to_csv(self, data: List[Dict[str, Any]]) -> bytes:
        """Export data to CSV format"""
        if not data:
            return b''
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue().encode('utf-8')
    
    def _export_to_json(self, data: List[Dict[str, Any]]) -> bytes:
        """Export data to JSON format"""
        return json.dumps(data, indent=2).encode('utf-8')
    
    def _export_to_excel(self, data: List[Dict[str, Any]], sheet_name: str = 'Data') -> bytes:
        """Export data to Excel format"""
        output = io.BytesIO()
        
        if not data:
            # Create empty workbook
            workbook = xlsxwriter.Workbook(output)
            workbook.add_worksheet(sheet_name)
            workbook.close()
            output.seek(0)
            return output.getvalue()
        
        # Create DataFrame and write to Excel
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#1976d2',
                'font_color': 'white'
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-fit columns
            for idx, col in enumerate(df.columns):
                series = df[col]
                max_len = max(
                    series.astype(str).map(len).max(),
                    len(str(series.name))
                ) + 2
                worksheet.set_column(idx, idx, max_len)
        
        output.seek(0)
        return output.getvalue()
    
    def export_transcript(self, transcript_id: int, format: str = 'json') -> bytes:
        """Export a specific transcript with all analysis"""
        try:
            # Get transcript with related data
            transcript = Transcript.query.get(transcript_id)
            if not transcript:
                raise ValueError("Transcript not found")
            
            sentiment = transcript.sentiment_analysis
            company = transcript.company
            
            # Prepare comprehensive data
            export_data = {
                'company': {
                    'ticker': company.ticker,
                    'name': company.name,
                    'sector': company.sector,
                    'industry': company.industry
                },
                'transcript': {
                    'id': transcript.id,
                    'fiscal_period': f"{transcript.fiscal_year} Q{transcript.fiscal_quarter}",
                    'call_date': transcript.call_date.isoformat() if transcript.call_date else None,
                    'word_count': transcript.word_count,
                    'full_text': transcript.full_text
                },
                'analysis': {
                    'overall_sentiment': float(sentiment.overall_sentiment) if sentiment else None,
                    'management_confidence': float(sentiment.management_confidence_score) if sentiment else None,
                    'guidance_sentiment': float(sentiment.guidance_sentiment) if sentiment else None,
                    'sentiment_by_section': sentiment.sentiment_by_section if sentiment else {},
                    'confidence_indicators': sentiment.confidence_indicators if sentiment else {},
                    'product_mentions': sentiment.product_mentions if sentiment else [],
                    'key_topics': sentiment.key_topics if sentiment else {}
                },
                'export_metadata': {
                    'exported_at': datetime.utcnow().isoformat(),
                    'format': format
                }
            }
            
            if format == 'json':
                return json.dumps(export_data, indent=2).encode('utf-8')
            else:
                # For other formats, flatten the structure
                flat_data = {
                    'ticker': export_data['company']['ticker'],
                    'company_name': export_data['company']['name'],
                    'fiscal_period': export_data['transcript']['fiscal_period'],
                    'call_date': export_data['transcript']['call_date'],
                    'word_count': export_data['transcript']['word_count'],
                    'overall_sentiment': export_data['analysis']['overall_sentiment'],
                    'management_confidence': export_data['analysis']['management_confidence'],
                    'guidance_sentiment': export_data['analysis']['guidance_sentiment'],
                    'transcript_text': export_data['transcript']['full_text']
                }
                
                if format == 'csv':
                    return self._export_to_csv([flat_data])
                else:
                    raise ValueError(f"Unsupported format for transcript: {format}")
                    
        except Exception as e:
            logger.error(f"Transcript export failed: {str(e)}")
            raise 