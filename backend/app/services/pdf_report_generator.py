#!/usr/bin/env python3
"""
PDF Report Generator for OpalSight
Creates comprehensive PDF reports with quotes, sentiment analysis, and trends
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import io
import base64
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

from app.models import db, Company, Transcript, SentimentAnalysis, TrendAnalysis, MonthlyReport, Alert
from config.config import get_config

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate comprehensive PDF reports for OpalSight"""
    
    def __init__(self, config=None):
        """Initialize the PDF report generator"""
        self.config = config or get_config()
        self.styles = getSampleStyleSheet()
        
        # Colors for the report
        self.report_colors = {
            'primary': colors.HexColor('#1f77b4'),    # Blue
            'positive': colors.HexColor('#2ca02c'),    # Green
            'negative': colors.HexColor('#d62728'),    # Red
            'neutral': colors.HexColor('#ff7f0e'),     # Orange
            'header': colors.HexColor('#2c3e50'),      # Dark blue
            'light_gray': colors.HexColor('#ecf0f1'),  # Light gray
        }
        
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=self.report_colors['header'],
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=self.report_colors['header'],
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=1,
            borderColor=self.report_colors['primary'],
            borderPadding=5
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.report_colors['header'],
            spaceBefore=15,
            spaceAfter=8
        ))
        
        # Quote style
        self.styles.add(ParagraphStyle(
            name='Quote',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=20,
            rightIndent=20,
            spaceBefore=8,
            spaceAfter=8,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=10,
            backColor=colors.whitesmoke,
            fontName='Times-Italic'
        ))
        
        # Highlight style for important text
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            backColor=colors.yellow,
            borderWidth=1,
            borderColor=colors.orange,
            borderPadding=5
        ))
    
    def generate_company_report(self, ticker: str, include_quotes: bool = True) -> bytes:
        """Generate comprehensive company report"""
        try:
            company = Company.find_by_ticker(ticker)
            if not company:
                raise ValueError(f"Company {ticker} not found")
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build report content
            story = []
            
            # Title page
            self._add_company_title_page(story, company)
            story.append(PageBreak())
            
            # Executive summary
            self._add_executive_summary(story, company)
            
            # Sentiment analysis section
            self._add_sentiment_analysis_section(story, company, include_quotes)
            
            # Trend analysis section
            self._add_trend_analysis_section(story, company)
            
            # Historical comparison
            self._add_historical_comparison(story, company)
            
            # Recent alerts
            self._add_alerts_section(story, company)
            
            # Guidance tracking
            self._add_guidance_section(story, company)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated company report for {ticker}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating company report for {ticker}: {str(e)}")
            raise
    
    def generate_monthly_report(self, report_date: date) -> bytes:
        """Generate monthly industry summary report"""
        try:
            # Get monthly report data
            monthly_report = MonthlyReport.query.filter_by(report_date=report_date).first()
            if not monthly_report:
                raise ValueError(f"Monthly report for {report_date} not found")
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build report content
            story = []
            
            # Title page
            self._add_monthly_title_page(story, monthly_report)
            story.append(PageBreak())
            
            # Executive summary
            self._add_monthly_executive_summary(story, monthly_report)
            
            # Trend distribution
            self._add_trend_distribution_section(story, monthly_report)
            
            # Company categorization
            self._add_company_categorization(story, monthly_report)
            
            # Notable changes
            self._add_notable_changes_section(story, monthly_report)
            
            # Industry insights
            self._add_industry_insights(story, monthly_report)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated monthly report for {report_date}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating monthly report for {report_date}: {str(e)}")
            raise
    
    def _add_company_title_page(self, story: List, company: Company):
        """Add company report title page"""
        # Company name and ticker
        title = f"{company.name} ({company.ticker})"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 30))
        
        # Report type and date
        subtitle = "Comprehensive Sentiment Analysis Report"
        story.append(Paragraph(subtitle, self.styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Report date
        report_date = f"Generated on {datetime.now().strftime('%B %d, %Y')}"
        story.append(Paragraph(report_date, self.styles['Normal']))
        story.append(Spacer(1, 40))
        
        # Company overview table
        overview_data = [
            ['Company Name', company.name],
            ['Ticker Symbol', company.ticker],
            ['Sector', company.sector or 'N/A'],
            ['Industry', company.industry or 'N/A'],
            ['Exchange', company.exchange or 'N/A'],
            ['Market Cap', f"${company.market_cap_billions:.1f}B" if company.market_cap_billions else 'N/A']
        ]
        
        overview_table = Table(overview_data, colWidths=[2*inch, 3*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.report_colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(overview_table)
    
    def _add_executive_summary(self, story: List, company: Company):
        """Add executive summary section"""
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get latest transcript and analysis
        latest_transcript = company.latest_transcript
        latest_trend = company.latest_trend
        
        if latest_transcript and latest_transcript.sentiment_analysis:
            sentiment = latest_transcript.sentiment_analysis
            
            # Summary points
            summary_points = []
            
            # Overall sentiment
            sentiment_label = sentiment.sentiment_label.title()
            sentiment_score = sentiment.overall_sentiment or 0
            summary_points.append(f"• <b>Overall Sentiment:</b> {sentiment_label} (Score: {sentiment_score:.2f})")
            
            # Management confidence
            confidence_label = sentiment.confidence_label.title()
            confidence_score = sentiment.management_confidence_score or 0
            summary_points.append(f"• <b>Management Confidence:</b> {confidence_label} (Score: {confidence_score:.2f})")
            
            # Trend direction
            if latest_trend:
                trend_label = latest_trend.trend_category.title()
                summary_points.append(f"• <b>Trend Direction:</b> {trend_label}")
            
            # Key topics
            key_topics = sentiment.get_key_topics()
            if key_topics:
                topics_str = ", ".join(key_topics[:3])
                summary_points.append(f"• <b>Key Discussion Topics:</b> {topics_str}")
            
            # Recent fiscal period
            fiscal_period = f"{latest_transcript.fiscal_year} Q{latest_transcript.fiscal_quarter}"
            summary_points.append(f"• <b>Latest Earnings Call:</b> {fiscal_period}")
            
            for point in summary_points:
                story.append(Paragraph(point, self.styles['Normal']))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("No recent earnings call data available for analysis.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_sentiment_analysis_section(self, story: List, company: Company, include_quotes: bool = True):
        """Add detailed sentiment analysis section"""
        story.append(Paragraph("Sentiment Analysis", self.styles['SectionHeader']))
        
        latest_transcript = company.latest_transcript
        if not latest_transcript or not latest_transcript.sentiment_analysis:
            story.append(Paragraph("No sentiment analysis data available.", self.styles['Normal']))
            return
        
        sentiment = latest_transcript.sentiment_analysis
        
        # Sentiment scores table
        story.append(Paragraph("Sentiment Scores", self.styles['SubsectionHeader']))
        
        sentiment_data = [
            ['Metric', 'Score', 'Interpretation'],
            ['Overall Sentiment', f"{sentiment.overall_sentiment:.3f}" if sentiment.overall_sentiment else 'N/A', sentiment.sentiment_label.title()],
            ['Management Confidence', f"{sentiment.management_confidence_score:.3f}" if sentiment.management_confidence_score else 'N/A', sentiment.confidence_label.title()],
            ['Guidance Sentiment', f"{sentiment.guidance_sentiment:.3f}" if sentiment.guidance_sentiment else 'N/A', self._interpret_score(sentiment.guidance_sentiment)]
        ]
        
        sentiment_table = Table(sentiment_data, colWidths=[2*inch, 1*inch, 2*inch])
        sentiment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(sentiment_table)
        story.append(Spacer(1, 20))
        
        # Key quotes section
        if include_quotes:
            self._add_key_quotes_section(story, sentiment)
        
        # Product mentions
        self._add_product_mentions_section(story, sentiment)
    
    def _add_key_quotes_section(self, story: List, sentiment: SentimentAnalysis):
        """Add key quotes section with sentiment context"""
        story.append(Paragraph("Key Quotes and Insights", self.styles['SubsectionHeader']))
        
        key_quotes = sentiment.get_key_quotes()
        
        if key_quotes:
            for i, quote_data in enumerate(key_quotes[:5], 1):  # Limit to top 5 quotes
                # Quote header
                speaker = quote_data.get('speaker', 'Management')
                topic = quote_data.get('topic', 'General').replace('_', ' ').title()
                context = quote_data.get('context', 'general').title()
                quote_sentiment = quote_data.get('sentiment_score', 0)
                
                header_text = f"<b>Quote {i}</b> - {speaker} ({topic}, {context})"
                if quote_sentiment:
                    sentiment_color = 'green' if quote_sentiment > 0 else 'red' if quote_sentiment < -0.1 else 'orange'
                    header_text += f" <font color='{sentiment_color}'>[Sentiment: {quote_sentiment:.2f}]</font>"
                
                story.append(Paragraph(header_text, self.styles['Normal']))
                story.append(Spacer(1, 5))
                
                # The actual quote
                quote_text = quote_data.get('text', '')
                if quote_text:
                    story.append(Paragraph(f'"{quote_text}"', self.styles['Quote']))
                    story.append(Spacer(1, 15))
        else:
            story.append(Paragraph("No key quotes extracted from the latest transcript.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_product_mentions_section(self, story: List, sentiment: SentimentAnalysis):
        """Add product mentions section"""
        story.append(Paragraph("Product and Drug Mentions", self.styles['SubsectionHeader']))
        
        product_mentions = sentiment.get_product_mentions()
        
        if product_mentions:
            products_text = "Products/drugs mentioned in the earnings call:<br/>"
            for product in product_mentions[:10]:  # Limit to 10 products
                if isinstance(product, dict):
                    name = product.get('name', 'Unknown')
                    context = product.get('context', '')
                    products_text += f"• <b>{name}</b>"
                    if context:
                        products_text += f" ({context})"
                    products_text += "<br/>"
                else:
                    products_text += f"• <b>{product}</b><br/>"
            
            story.append(Paragraph(products_text, self.styles['Normal']))
        else:
            story.append(Paragraph("No specific product mentions identified.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_trend_analysis_section(self, story: List, company: Company):
        """Add trend analysis section"""
        story.append(Paragraph("Trend Analysis", self.styles['SectionHeader']))
        
        latest_trend = company.latest_trend
        
        if latest_trend:
            # Trend summary
            trend_category = latest_trend.trend_category.title()
            sentiment_change = latest_trend.sentiment_change or 0
            confidence_change = latest_trend.confidence_change or 0
            
            trend_text = f"<b>Current Trend:</b> {trend_category}<br/>"
            trend_text += f"<b>Sentiment Change:</b> {sentiment_change:+.3f} points<br/>"
            trend_text += f"<b>Confidence Change:</b> {confidence_change:+.3f} points<br/>"
            
            story.append(Paragraph(trend_text, self.styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Key changes
            key_changes = latest_trend.get_key_changes()
            if key_changes:
                story.append(Paragraph("Key Changes Identified:", self.styles['SubsectionHeader']))
                
                for change in key_changes:
                    if isinstance(change, dict):
                        description = change.get('description', '')
                        impact = change.get('impact', 'neutral')
                        change_type = change.get('type', 'unknown').replace('_', ' ').title()
                        
                        impact_color = 'green' if impact == 'positive' else 'red' if impact == 'negative' else 'orange'
                        change_text = f"• <b>{change_type}:</b> {description} "
                        change_text += f"<font color='{impact_color}'>[{impact.title()} Impact]</font>"
                        
                        story.append(Paragraph(change_text, self.styles['Normal']))
                        story.append(Spacer(1, 8))
            
            # Notable quotes from trend analysis
            notable_quotes = latest_trend.get_notable_quotes()
            if notable_quotes:
                story.append(Paragraph("Supporting Quotes:", self.styles['SubsectionHeader']))
                
                for quote in notable_quotes[:3]:  # Limit to 3 quotes
                    if isinstance(quote, dict):
                        quote_text = quote.get('text', '')
                        if quote_text:
                            story.append(Paragraph(f'"{quote_text}"', self.styles['Quote']))
                            story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("No trend analysis data available.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_historical_comparison(self, story: List, company: Company):
        """Add historical comparison section"""
        story.append(Paragraph("Historical Comparison", self.styles['SectionHeader']))
        
        # Get last 4 transcripts with sentiment analysis
        transcripts = (
            Transcript.query
            .filter_by(company_id=company.id)
            .join(SentimentAnalysis)
            .order_by(Transcript.fiscal_year.desc(), Transcript.fiscal_quarter.desc())
            .limit(4)
            .all()
        )
        
        if len(transcripts) >= 2:
            # Create historical table
            historical_data = [
                ['Period', 'Overall Sentiment', 'Management Confidence', 'Trend']
            ]
            
            for transcript in transcripts:
                period = f"{transcript.fiscal_year} Q{transcript.fiscal_quarter}"
                sentiment_score = transcript.sentiment_analysis.overall_sentiment or 0
                confidence_score = transcript.sentiment_analysis.management_confidence_score or 0
                
                # Determine trend arrow
                if len(historical_data) > 1:
                    prev_sentiment = float(historical_data[-1][1])
                    if sentiment_score > prev_sentiment + 0.1:
                        trend_arrow = "↗️ Improving"
                    elif sentiment_score < prev_sentiment - 0.1:
                        trend_arrow = "↘️ Declining"
                    else:
                        trend_arrow = "→ Stable"
                else:
                    trend_arrow = "N/A"
                
                historical_data.append([
                    period,
                    f"{sentiment_score:.3f}",
                    f"{confidence_score:.3f}",
                    trend_arrow
                ])
            
            historical_table = Table(historical_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            historical_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(historical_table)
            
            # Add interpretation
            story.append(Spacer(1, 15))
            latest_sentiment = transcripts[0].sentiment_analysis.overall_sentiment or 0
            previous_sentiment = transcripts[1].sentiment_analysis.overall_sentiment or 0
            sentiment_change = latest_sentiment - previous_sentiment
            
            if abs(sentiment_change) > 0.1:
                direction = "improved" if sentiment_change > 0 else "declined"
                interpretation = f"The company's sentiment has <b>{direction}</b> by {abs(sentiment_change):.3f} points since the previous quarter."
                
                if abs(sentiment_change) > 0.3:
                    interpretation += " This represents a <b>significant change</b> in market perception."
                
                story.append(Paragraph(interpretation, self.styles['Highlight']))
            else:
                story.append(Paragraph("Sentiment has remained relatively <b>stable</b> compared to the previous quarter.", self.styles['Normal']))
        else:
            story.append(Paragraph("Insufficient historical data for comparison (need at least 2 quarters).", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_alerts_section(self, story: List, company: Company):
        """Add recent alerts section"""
        story.append(Paragraph("Recent Alerts", self.styles['SectionHeader']))
        
        # Get recent alerts (last 30 days)
        recent_alerts = (
            Alert.query
            .filter_by(company_id=company.id)
            .filter(Alert.created_at >= datetime.utcnow() - timedelta(days=30))
            .order_by(Alert.created_at.desc())
            .limit(5)
            .all()
        )
        
        if recent_alerts:
            for alert in recent_alerts:
                # Alert header
                severity_color = 'red' if alert.severity == 'high' else 'orange' if alert.severity == 'medium' else 'blue'
                alert_header = f"<font color='{severity_color}'><b>{alert.severity.upper()} PRIORITY</b></font> - {alert.alert_type.replace('_', ' ').title()}"
                story.append(Paragraph(alert_header, self.styles['Normal']))
                
                # Alert message
                story.append(Paragraph(alert.message, self.styles['Normal']))
                
                # Alert date
                alert_date = alert.created_at.strftime('%B %d, %Y at %I:%M %p')
                story.append(Paragraph(f"<i>Generated on {alert_date}</i>", self.styles['Normal']))
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("No recent alerts generated for this company.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_guidance_section(self, story: List, company: Company):
        """Add guidance tracking section"""
        story.append(Paragraph("Guidance and Forward-Looking Statements", self.styles['SectionHeader']))
        
        latest_transcript = company.latest_transcript
        if latest_transcript and latest_transcript.sentiment_analysis:
            extracted_guidance = latest_transcript.sentiment_analysis.get_extracted_guidance()
            
            if extracted_guidance:
                story.append(Paragraph("Management guidance and forward-looking statements from the latest earnings call:", self.styles['Normal']))
                story.append(Spacer(1, 10))
                
                for guidance in extracted_guidance:
                    if isinstance(guidance, dict):
                        metric = guidance.get('metric', 'Unknown').replace('_', ' ').title()
                        value = guidance.get('value', 'Not specified')
                        timeframe = guidance.get('timeframe', 'Not specified')
                        confidence = guidance.get('confidence', 'medium')
                        
                        confidence_color = 'green' if confidence == 'high' else 'orange' if confidence == 'medium' else 'red'
                        
                        guidance_text = f"• <b>{metric}:</b> {value}"
                        if timeframe != 'Not specified':
                            guidance_text += f" (Timeframe: {timeframe})"
                        guidance_text += f" <font color='{confidence_color}'>[{confidence.title()} Confidence]</font>"
                        
                        story.append(Paragraph(guidance_text, self.styles['Normal']))
                        story.append(Spacer(1, 8))
            else:
                story.append(Paragraph("No specific guidance statements extracted from the latest earnings call.", self.styles['Normal']))
        else:
            story.append(Paragraph("No guidance data available.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_monthly_title_page(self, story: List, monthly_report: MonthlyReport):
        """Add monthly report title page"""
        title = "OpalSight Monthly Industry Report"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 30))
        
        # Report period
        report_period = monthly_report.report_date.strftime('%B %Y')
        subtitle = f"Biotech & Medtech Sentiment Analysis - {report_period}"
        story.append(Paragraph(subtitle, self.styles['Heading2']))
        story.append(Spacer(1, 40))
        
        # Summary statistics
        summary_data = [
            ['Total Companies Analyzed', str(monthly_report.companies_analyzed)],
            ['Companies Improving', str(monthly_report.improving_count)],
            ['Companies Stable', str(monthly_report.stable_count)],
            ['Companies Declining', str(monthly_report.declining_count)],
            ['Report Generated', datetime.now().strftime('%B %d, %Y')]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.report_colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
    
    def _add_monthly_executive_summary(self, story: List, monthly_report: MonthlyReport):
        """Add monthly report executive summary"""
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        total = monthly_report.companies_analyzed
        improving_pct = round(monthly_report.improving_count / total * 100, 1) if total > 0 else 0
        stable_pct = round(monthly_report.stable_count / total * 100, 1) if total > 0 else 0
        declining_pct = round(monthly_report.declining_count / total * 100, 1) if total > 0 else 0
        
        summary_text = f"""
        This report analyzes sentiment trends across {total} biotech and medtech companies based on their latest earnings call transcripts.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • {improving_pct}% of companies ({monthly_report.improving_count}) showed <font color='green'><b>improving sentiment</b></font><br/>
        • {stable_pct}% of companies ({monthly_report.stable_count}) maintained <font color='orange'><b>stable sentiment</b></font><br/>
        • {declining_pct}% of companies ({monthly_report.declining_count}) exhibited <font color='red'><b>declining sentiment</b></font><br/>
        """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
    
    def _add_trend_distribution_section(self, story: List, monthly_report: MonthlyReport):
        """Add trend distribution visualization"""
        story.append(Paragraph("Sentiment Distribution", self.styles['SectionHeader']))
        
        # Create a simple bar chart using reportlab
        # This would be enhanced with actual chart generation
        distribution_data = [
            ['Trend Category', 'Count', 'Percentage'],
            ['Improving', str(monthly_report.improving_count), f"{monthly_report.improving_count/monthly_report.companies_analyzed*100:.1f}%"],
            ['Stable', str(monthly_report.stable_count), f"{monthly_report.stable_count/monthly_report.companies_analyzed*100:.1f}%"],
            ['Declining', str(monthly_report.declining_count), f"{monthly_report.declining_count/monthly_report.companies_analyzed*100:.1f}%"]
        ]
        
        distribution_table = Table(distribution_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        distribution_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.report_colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(distribution_table)
        story.append(Spacer(1, 20))
    
    def _add_company_categorization(self, story: List, monthly_report: MonthlyReport):
        """Add detailed company categorization"""
        story.append(Paragraph("Company Details by Category", self.styles['SectionHeader']))
        
        report_data = monthly_report.report_data or {}
        trends_by_category = report_data.get('trends_by_category', {})
        
        for category in ['improving', 'stable', 'declining']:
            companies = trends_by_category.get(category, [])
            if companies:
                category_title = f"{category.title()} Companies"
                story.append(Paragraph(category_title, self.styles['SubsectionHeader']))
                
                for company in companies:
                    ticker = company.get('ticker', 'N/A')
                    name = company.get('name', 'N/A')
                    sentiment_change = company.get('sentiment_change', 0)
                    
                    change_color = 'green' if sentiment_change > 0 else 'red' if sentiment_change < 0 else 'orange'
                    company_text = f"• <b>{ticker}</b> - {name} "
                    company_text += f"<font color='{change_color}'>(Sentiment Change: {sentiment_change:+.2f})</font>"
                    
                    story.append(Paragraph(company_text, self.styles['Normal']))
                    story.append(Spacer(1, 5))
                
                story.append(Spacer(1, 15))
    
    def _add_notable_changes_section(self, story: List, monthly_report: MonthlyReport):
        """Add notable changes section"""
        story.append(Paragraph("Notable Changes", self.styles['SectionHeader']))
        
        # Get companies with significant sentiment changes
        significant_changes = []
        report_data = monthly_report.report_data or {}
        trends_by_category = report_data.get('trends_by_category', {})
        
        for category, companies in trends_by_category.items():
            for company in companies:
                sentiment_change = abs(company.get('sentiment_change', 0))
                if sentiment_change > 0.3:  # Significant change threshold
                    significant_changes.append(company)
        
        if significant_changes:
            story.append(Paragraph("The following companies showed significant sentiment changes (>0.3 points):", self.styles['Normal']))
            story.append(Spacer(1, 10))
            
            for company in significant_changes:
                ticker = company.get('ticker', 'N/A')
                name = company.get('name', 'N/A')
                sentiment_change = company.get('sentiment_change', 0)
                
                change_direction = "improved" if sentiment_change > 0 else "declined"
                change_text = f"<b>{ticker} ({name})</b> sentiment {change_direction} by {abs(sentiment_change):.2f} points"
                
                story.append(Paragraph(f"• {change_text}", self.styles['Highlight']))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("No companies showed significant sentiment changes (>0.3 points) this period.", self.styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    def _add_industry_insights(self, story: List, monthly_report: MonthlyReport):
        """Add industry-wide insights"""
        story.append(Paragraph("Industry Insights", self.styles['SectionHeader']))
        
        report_data = monthly_report.report_data or {}
        overview = report_data.get('overview', {})
        
        market_sentiment = overview.get('market_sentiment', 'Mixed')
        key_themes = overview.get('key_themes', [])
        
        insights_text = f"<b>Overall Market Sentiment:</b> {market_sentiment}<br/><br/>"
        
        if key_themes:
            insights_text += "<b>Key Industry Themes:</b><br/>"
            for theme in key_themes:
                insights_text += f"• {theme}<br/>"
        
        story.append(Paragraph(insights_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
    
    def _interpret_score(self, score: Optional[float]) -> str:
        """Interpret a sentiment score"""
        if score is None:
            return 'Unknown'
        elif score > 0.1:
            return 'Positive'
        elif score < -0.1:
            return 'Negative'
        else:
            return 'Neutral'


# Utility functions
def generate_company_pdf_report(ticker: str, include_quotes: bool = True) -> bytes:
    """Generate PDF report for a specific company"""
    generator = PDFReportGenerator()
    return generator.generate_company_report(ticker, include_quotes)


def generate_monthly_pdf_report(report_date: date) -> bytes:
    """Generate monthly industry PDF report"""
    generator = PDFReportGenerator()
    return generator.generate_monthly_report(report_date) 