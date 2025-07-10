"""Trend Analysis model"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import json

from sqlalchemy import Index, CheckConstraint, JSON

from . import db


class TrendAnalysis(db.Model):
    """Model for storing trend analysis results"""
    __tablename__ = 'trend_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    analysis_date = db.Column(db.Date, nullable=False)
    trend_category = db.Column(
        db.String(20), 
        CheckConstraint("trend_category IN ('improving', 'stable', 'declining', 'insufficient_data')"),
        nullable=False
    )
    sentiment_change = db.Column(db.Float)
    confidence_change = db.Column(db.Float)
    key_changes = db.Column(JSON)
    notable_quotes = db.Column(JSON)
    comparison_window = db.Column(db.Integer, default=4)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_trend_company_date', 'company_id', 'analysis_date'),
        Index('idx_trend_category', 'trend_category'),
    )
    
    def __repr__(self):
        return f'<TrendAnalysis {self.company.ticker if self.company else "?"} {self.trend_category} on {self.analysis_date}>'
    
    @property
    def is_improving(self) -> bool:
        """Check if trend is improving"""
        return self.trend_category == 'improving'
    
    @property
    def is_declining(self) -> bool:
        """Check if trend is declining"""
        return self.trend_category == 'declining'
    
    @property
    def is_significant_change(self) -> bool:
        """Check if there's a significant sentiment change"""
        threshold = 0.2
        return (
            (self.sentiment_change and abs(self.sentiment_change) > threshold) or
            (self.confidence_change and abs(self.confidence_change) > threshold)
        )
    
    def get_key_changes(self) -> List[Dict[str, Any]]:
        """Get key changes as list"""
        if self.key_changes and isinstance(self.key_changes, list):
            return self.key_changes
        return []
    
    def get_notable_quotes(self) -> List[str]:
        """Get notable quotes"""
        if self.notable_quotes:
            if isinstance(self.notable_quotes, list):
                return self.notable_quotes
            elif isinstance(self.notable_quotes, dict) and 'quotes' in self.notable_quotes:
                return self.notable_quotes['quotes']
        return []
    
    def to_dict(self, include_company: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'trend_category': self.trend_category,
            'sentiment_change': self.sentiment_change,
            'confidence_change': self.confidence_change,
            'is_significant_change': self.is_significant_change,
            'comparison_window': self.comparison_window,
            'key_changes': self.get_key_changes(),
            'notable_quotes': self.get_notable_quotes(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_company and self.company:
            data['company'] = {
                'ticker': self.company.ticker,
                'name': self.company.name,
                'sector': self.company.sector,
                'industry': self.company.industry
            }
        
        return data
    
    @classmethod
    def get_latest_by_category(cls, category: str, limit: int = 10) -> List['TrendAnalysis']:
        """Get latest trends by category"""
        return (
            cls.query
            .filter_by(trend_category=category)
            .order_by(cls.analysis_date.desc())
            .limit(limit)
            .all()
        )
    
    @classmethod
    def get_summary_stats(cls, analysis_date: Optional[date] = None) -> Dict[str, int]:
        """Get summary statistics for a given date"""
        if analysis_date is None:
            analysis_date = db.session.query(db.func.max(cls.analysis_date)).scalar()
        
        if not analysis_date:
            return {'improving': 0, 'stable': 0, 'declining': 0, 'insufficient_data': 0}
        
        results = (
            db.session.query(cls.trend_category, db.func.count(cls.id))
            .filter(cls.analysis_date == analysis_date)
            .group_by(cls.trend_category)
            .all()
        )
        
        stats = {'improving': 0, 'stable': 0, 'declining': 0, 'insufficient_data': 0}
        for category, count in results:
            stats[category] = count
        
        return stats
    
    @classmethod
    def get_significant_changes(
        cls, 
        days: int = 7, 
        threshold: float = 0.2
    ) -> List['TrendAnalysis']:
        """Get trends with significant changes"""
        cutoff_date = date.today() - timedelta(days=days)
        
        return (
            cls.query
            .filter(cls.analysis_date >= cutoff_date)
            .filter(
                db.or_(
                    db.func.abs(cls.sentiment_change) > threshold,
                    db.func.abs(cls.confidence_change) > threshold
                )
            )
            .order_by(db.func.abs(cls.sentiment_change).desc())
            .all()
        ) 