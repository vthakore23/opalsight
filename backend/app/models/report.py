"""Monthly Report model"""
from datetime import datetime, date
from typing import Dict, Any, Optional

from sqlalchemy import Index, UniqueConstraint, JSON

from . import db


class MonthlyReport(db.Model):
    """Model for storing monthly analysis reports"""
    __tablename__ = 'monthly_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, unique=True)
    companies_analyzed = db.Column(db.Integer)
    improving_count = db.Column(db.Integer)
    stable_count = db.Column(db.Integer)
    declining_count = db.Column(db.Integer)
    report_data = db.Column(JSON)
    pdf_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MonthlyReport {self.report_date}>'
    
    @property
    def month_year(self) -> str:
        """Get month and year as string"""
        if self.report_date:
            return self.report_date.strftime('%B %Y')
        return ''
    
    @property
    def total_companies(self) -> int:
        """Get total companies analyzed"""
        return self.companies_analyzed or 0
    
    @property
    def improvement_rate(self) -> float:
        """Calculate improvement rate"""
        if self.companies_analyzed and self.companies_analyzed > 0:
            return (self.improving_count or 0) / self.companies_analyzed
        return 0.0
    
    @property
    def decline_rate(self) -> float:
        """Calculate decline rate"""
        if self.companies_analyzed and self.companies_analyzed > 0:
            return (self.declining_count or 0) / self.companies_analyzed
        return 0.0
    
    def get_report_data(self) -> Dict[str, Any]:
        """Get report data"""
        if self.report_data and isinstance(self.report_data, dict):
            return self.report_data
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'month_year': self.month_year,
            'companies_analyzed': self.companies_analyzed,
            'improving_count': self.improving_count,
            'stable_count': self.stable_count,
            'declining_count': self.declining_count,
            'improvement_rate': round(self.improvement_rate, 3),
            'decline_rate': round(self.decline_rate, 3),
            'pdf_url': self.pdf_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_latest(cls, limit: int = 12) -> list['MonthlyReport']:
        """Get latest monthly reports"""
        return (
            cls.query
            .order_by(cls.report_date.desc())
            .limit(limit)
            .all()
        )
    
    @classmethod
    def get_by_date(cls, report_date: date) -> Optional['MonthlyReport']:
        """Get report by date"""
        return cls.query.filter_by(report_date=report_date).first() 