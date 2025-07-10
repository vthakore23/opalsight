"""Email Notification Service"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime
import jinja2
from email.mime.base import MIMEBase
from email import encoders

from config.config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.enabled = bool(self.config.SMTP_HOST and self.config.SMTP_FROM_EMAIL)
        
        # Set up Jinja2 for email templates
        self.template_env = jinja2.Environment(
            loader=jinja2.DictLoader({
                'alert': self._get_alert_template(),
                'weekly_summary': self._get_weekly_summary_template(),
                'watchlist_update': self._get_watchlist_update_template(),
                'monthly_report': self._get_monthly_report_template()
            })
        )
        
        if self.enabled:
            logger.info("Email service enabled")
        else:
            logger.warning("Email service disabled - missing SMTP configuration")
    
    def send_email(self, to_emails: List[str], subject: str, body_html: str, body_text: str = None) -> bool:
        """Send email to recipients"""
        if not self.enabled:
            logger.warning(f"Email service disabled - would have sent: {subject} to {to_emails}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"OpalSight <{self.config.SMTP_FROM_EMAIL}>"
            msg['To'] = ', '.join(to_emails)
            
            # Add text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT) as server:
                if self.config.SMTP_USE_TLS:
                    server.starttls()
                if self.config.SMTP_USERNAME:
                    server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                
                server.send_message(msg)
                logger.info(f"Email sent successfully: {subject} to {to_emails}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _get_alert_template(self) -> str:
        """Get alert email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #1976d2; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f5f5f5; }
        .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
        .alert-high { background-color: #ffebee; border-left: 5px solid #f44336; }
        .alert-medium { background-color: #fff3e0; border-left: 5px solid #ff9800; }
        .alert-low { background-color: #e8f5e9; border-left: 5px solid #4caf50; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>OpalSight Alert</h2>
        </div>
        <div class="content">
            <h3>{{ alert.title }}</h3>
            <div class="alert alert-{{ alert.severity }}">
                <p><strong>Company:</strong> {{ alert.company_ticker }} - {{ alert.company_name }}</p>
                <p><strong>Severity:</strong> {{ alert.severity|upper }}</p>
                <p><strong>Message:</strong> {{ alert.message }}</p>
            </div>
            <p><a href="{{ frontend_url }}/company/{{ alert.company_ticker }}">View Company Details</a></p>
        </div>
        <div class="footer">
            <p>This is an automated alert from OpalSight Analytics</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _get_weekly_summary_template(self) -> str:
        """Get weekly summary email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #1976d2; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f5f5f5; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat { text-align: center; padding: 15px; background: white; border-radius: 5px; }
        .stat-number { font-size: 24px; font-weight: bold; color: #1976d2; }
        .company-list { margin: 10px 0; }
        .company { padding: 10px; background: white; margin: 5px 0; border-radius: 5px; }
        .improving { border-left: 5px solid #4caf50; }
        .declining { border-left: 5px solid #f44336; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>OpalSight Weekly Summary</h2>
            <p>{{ start_date }} - {{ end_date }}</p>
        </div>
        <div class="content">
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{{ summary.new_transcripts }}</div>
                    <div>New Transcripts</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{{ summary.companies_analyzed }}</div>
                    <div>Companies Analyzed</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{{ summary.alerts_generated }}</div>
                    <div>Alerts Generated</div>
                </div>
            </div>
            
            {% if summary.improving_companies %}
            <h3>Companies with Improving Sentiment</h3>
            <div class="company-list">
                {% for company in summary.improving_companies %}
                <div class="company improving">
                    <strong>{{ company.ticker }}</strong> - {{ company.name }}
                    <br>Sentiment change: +{{ company.sentiment_change }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            {% if summary.declining_companies %}
            <h3>Companies with Declining Sentiment</h3>
            <div class="company-list">
                {% for company in summary.declining_companies %}
                <div class="company declining">
                    <strong>{{ company.ticker }}</strong> - {{ company.name }}
                    <br>Sentiment change: {{ company.sentiment_change }}
                </div>
                {% endfor %}
            </div>
            {% endif %}
            
            <p style="margin-top: 20px;">
                <a href="{{ frontend_url }}/dashboard">View Full Dashboard</a>
            </p>
        </div>
        <div class="footer">
            <p>This is an automated summary from OpalSight Analytics</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _get_watchlist_update_template(self) -> str:
        """Get watchlist update email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #1976d2; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f5f5f5; }
        .update { padding: 15px; margin: 10px 0; background: white; border-radius: 5px; }
        .positive { border-left: 5px solid #4caf50; }
        .negative { border-left: 5px solid #f44336; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Watchlist Update</h2>
        </div>
        <div class="content">
            <h3>Your Watched Companies Have New Updates</h3>
            {% for update in updates %}
            <div class="update {{ 'positive' if update.sentiment_change > 0 else 'negative' }}">
                <strong>{{ update.ticker }} - {{ update.company_name }}</strong>
                <p>New transcript available: {{ update.period }}</p>
                <p>Sentiment change: {{ update.sentiment_change }}</p>
                <p>Trend: {{ update.trend_category|upper }}</p>
            </div>
            {% endfor %}
            <p style="margin-top: 20px;">
                <a href="{{ frontend_url }}/watchlist">View Your Watchlist</a>
            </p>
        </div>
        <div class="footer">
            <p>You're receiving this because these companies are on your watchlist</p>
        </div>
    </div>
</body>
</html>
""" 
    
    def _get_monthly_report_template(self) -> str:
        """Get monthly report email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; color: #333; line-height: 1.6; }
        .container { max-width: 700px; margin: 0 auto; padding: 20px; }
        .header { background-color: #1976d2; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .header h1 { margin: 0; font-size: 28px; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .content { padding: 30px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 0 0 10px 10px; }
        .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }
        .summary-card { background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }
        .summary-card .number { font-size: 36px; font-weight: bold; margin: 10px 0; }
        .improving { color: #4caf50; }
        .stable { color: #ff9800; }
        .declining { color: #f44336; }
        .highlights { margin: 30px 0; }
        .highlight-section { margin: 20px 0; }
        .company-item { padding: 12px; background: #f9f9f9; margin: 8px 0; border-radius: 5px; border-left: 4px solid #1976d2; }
        .cta { background: #1976d2; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }
        .footer { text-align: center; padding: 30px; color: #666; font-size: 12px; border-top: 1px solid #e0e0e0; margin-top: 40px; }
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f0f0f0;">
    <div class="container">
        <div class="header">
            <h1>OpalSight Monthly Report</h1>
            <p>{{ report_date }}</p>
        </div>
        <div class="content">
            <h2>Executive Summary</h2>
            <p>This month's analysis of the biotech/medtech sector reveals important trends and developments across {{ companies_analyzed }} companies.</p>
            
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="label">Improving</div>
                    <div class="number improving">{{ improving_count }}</div>
                    <div class="percentage">{{ improving_percentage }}%</div>
                </div>
                <div class="summary-card">
                    <div class="label">Stable</div>
                    <div class="number stable">{{ stable_count }}</div>
                    <div class="percentage">{{ stable_percentage }}%</div>
                </div>
                <div class="summary-card">
                    <div class="label">Declining</div>
                    <div class="number declining">{{ declining_count }}</div>
                    <div class="percentage">{{ declining_percentage }}%</div>
                </div>
            </div>
            
            <div class="highlights">
                {% if top_performers %}
                <div class="highlight-section">
                    <h3>🚀 Top Performers</h3>
                    {% for company in top_performers[:3] %}
                    <div class="company-item">
                        <strong>{{ company.ticker }} - {{ company.name }}</strong><br>
                        Sentiment improved by {{ company.sentiment_change }}
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if concerns %}
                <div class="highlight-section">
                    <h3>⚠️ Areas of Concern</h3>
                    {% for company in concerns[:3] %}
                    <div class="company-item">
                        <strong>{{ company.ticker }} - {{ company.name }}</strong><br>
                        Sentiment declined by {{ company.sentiment_change }}
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
            
            <p>The attached PDF contains a comprehensive analysis of all companies, including detailed breakdowns by category, trend analysis, and key insights.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ frontend_url }}/reports/{{ report_id }}" class="cta">View Full Report Online</a>
            </div>
        </div>
        <div class="footer">
            <p><strong>OpalSight Analytics</strong><br>
            Automated Biotech/Medtech Earnings Intelligence<br>
            This email and any attachments are confidential and intended solely for the addressee.</p>
        </div>
    </div>
</body>
</html>
"""
    
    def send_alert_email(self, alert: Dict[str, Any], recipients: List[str]) -> bool:
        """Send alert email to recipients"""
        if not self.enabled or not recipients:
            logger.warning("Email service disabled or no recipients")
            return False
        
        try:
            # Render template
            template = self.template_env.get_template('alert')
            html_content = template.render(
                alert=alert,
                frontend_url=self.config.FRONTEND_URL
            )
            
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = f"OpalSight Alert: {alert['title']}"
            msg['From'] = self.config.SMTP_FROM_EMAIL
            msg['To'] = ', '.join(recipients)
            
            # Attach HTML
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send
            self.send_email(recipients, msg['Subject'], html_content)
            
            logger.info(f"Alert email sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
            return False
    
    def send_weekly_summary(self, summary: Dict[str, Any], recipients: List[str]) -> bool:
        """Send weekly summary email"""
        if not self.enabled or not recipients:
            return False
        
        try:
            # Render template
            template = self.template_env.get_template('weekly_summary')
            html_content = template.render(
                summary=summary,
                start_date=summary['start_date'],
                end_date=summary['end_date'],
                frontend_url=self.config.FRONTEND_URL
            )
            
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = f"OpalSight Weekly Summary - {summary['end_date']}"
            msg['From'] = self.config.SMTP_FROM_EMAIL
            msg['To'] = ', '.join(recipients)
            
            # Attach HTML
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send
            self.send_email(recipients, msg['Subject'], html_content)
            
            logger.info(f"Weekly summary sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send weekly summary: {str(e)}")
            return False
    
    def send_monthly_report(self, report_data: Dict[str, Any], pdf_data: bytes, recipients: List[str]) -> bool:
        """Send monthly report email with PDF attachment"""
        if not self.enabled or not recipients:
            logger.warning("Email service disabled or no recipients")
            return False
        
        try:
            # Render template
            template = self.template_env.get_template('monthly_report')
            html_content = template.render(
                report_date=report_data['report_date'],
                companies_analyzed=report_data['companies_analyzed'],
                improving_count=report_data['improving_count'],
                improving_percentage=report_data.get('improving_percentage', 0),
                stable_count=report_data['stable_count'],
                stable_percentage=report_data.get('stable_percentage', 0),
                declining_count=report_data['declining_count'],
                declining_percentage=report_data.get('declining_percentage', 0),
                top_performers=report_data.get('top_performers', []),
                concerns=report_data.get('worst_performers', []),
                report_id=report_data.get('report_id'),
                frontend_url=self.config.FRONTEND_URL
            )
            
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = f"OpalSight Monthly Report - {report_data['report_date']}"
            msg['From'] = self.config.SMTP_FROM_EMAIL
            msg['To'] = ', '.join(recipients)
            
            # Attach HTML
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach PDF
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(pdf_data)
            encoders.encode_base64(pdf_attachment)
            pdf_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="OpalSight_Monthly_Report_{report_data["report_date"]}.pdf"'
            )
            msg.attach(pdf_attachment)
            
            # Send
            self.send_email(recipients, msg['Subject'], html_content)
            
            logger.info(f"Monthly report sent to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send monthly report: {str(e)}")
            return False
    
    def send_watchlist_update(self, updates: List[Dict[str, Any]], user_email: str) -> bool:
        """Send watchlist update notification"""
        template = self.template_env.get_template('watchlist_update')
        
        # Prepare context
        context = {
            'user_name': user_email.split('@')[0], # Extract username from email
            'companies': updates,
            'update_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            'watchlist_url': f"{self.config.FRONTEND_URL}/watchlist"
        }
        
        html = template.render(**context)
        subject = "OpalSight: Your Watchlist Update"
        
        return self.send_email([user_email], subject, html) 