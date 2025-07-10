"""PDF Generation Service"""
import logging
import io
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from app.models import Company, MonthlyReport, TrendAnalysis

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceBefore=12,
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976d2'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceBefore=10,
            spaceAfter=5
        ))
    
    def generate_monthly_report_pdf(self, report: MonthlyReport) -> bytes:
        """Generate a comprehensive monthly report PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
            title=f"OpalSight Monthly Report - {report.report_date.strftime('%B %Y')}",
            author="OpalSight Analytics"
        )
        
        # Build the story
        story = []
        
        # Title page
        story.extend(self._create_title_page(report))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._create_executive_summary(report))
        story.append(PageBreak())
        
        # Market overview chart
        story.extend(self._create_market_overview(report))
        story.append(PageBreak())
        
        # Detailed company analysis by category
        story.extend(self._create_category_analysis(report, 'improving'))
        story.append(PageBreak())
        
        story.extend(self._create_category_analysis(report, 'stable'))
        story.append(PageBreak())
        
        story.extend(self._create_category_analysis(report, 'declining'))
        story.append(PageBreak())
        
        # Top performers and concerns
        story.extend(self._create_highlights_section(report))
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        
        buffer.seek(0)
        return buffer.read()
    
    def _create_title_page(self, report: MonthlyReport) -> List:
        """Create the title page"""
        elements = []
        
        # Logo placeholder
        elements.append(Spacer(1, 2*inch))
        
        # Title
        title = Paragraph(
            "OpalSight Monthly Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        
        # Subtitle with date
        subtitle = Paragraph(
            f"Biotech/Medtech Earnings Analysis<br/>{report.report_date.strftime('%B %Y')}",
            self.styles['Subtitle']
        )
        elements.append(subtitle)
        
        elements.append(Spacer(1, 1*inch))
        
        # Summary stats
        stats_data = [
            ['Companies Analyzed', str(report.companies_analyzed)],
            ['Improving Sentiment', f"{report.improving_count} ({report.improving_count/report.companies_analyzed*100:.1f}%)"],
            ['Stable Sentiment', f"{report.stable_count} ({report.stable_count/report.companies_analyzed*100:.1f}%)"],
            ['Declining Sentiment', f"{report.declining_count} ({report.declining_count/report.companies_analyzed*100:.1f}%)"]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white)
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    def _create_executive_summary(self, report: MonthlyReport) -> List:
        """Create executive summary section"""
        elements = []
        
        # Header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 12))
        
        # Market overview text
        overview_data = report.report_data.get('overview', {})
        overview_text = f"""
        The biotech/medtech sector showed mixed performance in {report.report_date.strftime('%B %Y')}. 
        Analysis of {report.companies_analyzed} companies revealed {report.improving_count} companies 
        with improving sentiment, {report.stable_count} maintaining stable outlook, and {report.declining_count} 
        showing declining sentiment compared to previous quarters.
        """
        
        para = Paragraph(overview_text, self.styles['Normal'])
        elements.append(para)
        elements.append(Spacer(1, 12))
        
        # Key findings
        if report.report_data.get('top_performers'):
            elements.append(Paragraph("Key Positive Developments:", self.styles['Heading3']))
            for performer in report.report_data['top_performers'][:3]:
                text = f"• <b>{performer['ticker']}</b> - {performer['name']}: Sentiment improved by {performer['sentiment_change']:.2f}"
                elements.append(Paragraph(text, self.styles['Normal']))
            elements.append(Spacer(1, 12))
        
        if report.report_data.get('worst_performers'):
            elements.append(Paragraph("Areas of Concern:", self.styles['Heading3']))
            for performer in report.report_data['worst_performers'][:3]:
                text = f"• <b>{performer['ticker']}</b> - {performer['name']}: Sentiment declined by {performer['sentiment_change']:.2f}"
                elements.append(Paragraph(text, self.styles['Normal']))
        
        return elements
    
    def _create_market_overview(self, report: MonthlyReport) -> List:
        """Create market overview with chart"""
        elements = []
        
        header = Paragraph("Market Sentiment Distribution", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 12))
        
        # Generate pie chart
        fig, ax = plt.subplots(figsize=(6, 6))
        labels = ['Improving', 'Stable', 'Declining']
        sizes = [report.improving_count, report.stable_count, report.declining_count]
        colors_list = ['#4caf50', '#ff9800', '#f44336']
        
        ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        plt.title('Company Sentiment Distribution', fontsize=16)
        
        # Save to buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Add to PDF
        img = Image(img_buffer, width=4*inch, height=4*inch)
        elements.append(img)
        
        return elements
    
    def _create_category_analysis(self, report: MonthlyReport, category: str) -> List:
        """Create detailed analysis for a sentiment category"""
        elements = []
        
        # Header
        category_title = category.capitalize()
        color_map = {
            'improving': '#4caf50',
            'stable': '#ff9800',
            'declining': '#f44336'
        }
        
        header_style = ParagraphStyle(
            'CategoryHeader',
            parent=self.styles['SectionHeader'],
            textColor=colors.HexColor(color_map.get(category, '#333333'))
        )
        
        header = Paragraph(f"{category_title} Companies", header_style)
        elements.append(header)
        elements.append(Spacer(1, 12))
        
        # Company details
        companies = report.report_data.get('trends_by_category', {}).get(category, [])
        
        if not companies:
            elements.append(Paragraph("No companies in this category.", self.styles['Normal']))
            return elements
        
        # Create table with company details
        table_data = [['Company', 'Ticker', 'Sentiment Change', 'Confidence Change']]
        
        for company in companies[:10]:  # Limit to top 10
            table_data.append([
                company['name'][:30],  # Truncate long names
                company['ticker'],
                f"{company['sentiment_change']:+.2f}",
                f"{company['confidence_change']:+.2f}"
            ])
        
        table = Table(table_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(color_map.get(category, '#333333'))),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        if len(companies) > 10:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(
                f"... and {len(companies) - 10} more companies",
                self.styles['Normal']
            ))
        
        return elements
    
    def _create_highlights_section(self, report: MonthlyReport) -> List:
        """Create highlights and notable changes section"""
        elements = []
        
        header = Paragraph("Key Highlights & Notable Changes", self.styles['SectionHeader'])
        elements.append(header)
        elements.append(Spacer(1, 12))
        
        # Top performers detail
        if report.report_data.get('top_performers'):
            elements.append(Paragraph("Top Performers:", self.styles['Heading3']))
            
            for i, performer in enumerate(report.report_data['top_performers'], 1):
                text = f"""
                <b>{i}. {performer['ticker']} - {performer['name']}</b><br/>
                Sentiment Change: {performer['sentiment_change']:+.2f} | 
                Confidence Change: {performer['confidence_change']:+.2f}
                """
                elements.append(Paragraph(text, self.styles['Normal']))
                elements.append(Spacer(1, 6))
        
        return elements
    
    def _add_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawString(
            doc.leftMargin,
            doc.height + doc.topMargin + 10,
            "OpalSight Analytics - Confidential"
        )
        canvas_obj.drawRightString(
            doc.width + doc.leftMargin,
            doc.height + doc.topMargin + 10,
            datetime.now().strftime("%B %d, %Y")
        )
        
        # Footer with page number
        canvas_obj.drawString(
            doc.leftMargin,
            doc.bottomMargin - 10,
            f"Page {doc.page}"
        )
        
        canvas_obj.restoreState()
    
    def generate_company_report_pdf(self, company: Company, trends: List[TrendAnalysis]) -> bytes:
        """Generate a PDF report for a specific company"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
            title=f"{company.ticker} - Sentiment Analysis Report",
            author="OpalSight Analytics"
        )
        
        story = []
        
        # Title
        title = Paragraph(
            f"{company.ticker} - {company.name}",
            self.styles['CustomTitle']
        )
        story.append(title)
        
        subtitle = Paragraph(
            f"{company.industry}<br/>Market Cap: ${company.market_cap/1e9:.1f}B",
            self.styles['Subtitle']
        )
        story.append(subtitle)
        story.append(Spacer(1, 30))
        
        # Latest trend analysis
        if trends:
            latest_trend = trends[0]
            
            # Summary section
            story.append(Paragraph("Latest Analysis", self.styles['SectionHeader']))
            
            summary_data = [
                ['Trend Category', latest_trend.trend_category.upper()],
                ['Sentiment Change', f"{latest_trend.sentiment_change:+.2f}"],
                ['Confidence Change', f"{latest_trend.confidence_change:+.2f}"],
                ['Analysis Date', latest_trend.analysis_date.strftime('%Y-%m-%d')]
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer.read() 