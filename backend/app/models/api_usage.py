"""API Usage tracking model"""
from datetime import datetime, date, timedelta
from typing import Dict, List

from sqlalchemy import Index, UniqueConstraint

from . import db


class APIUsage(db.Model):
    """Model for tracking API usage"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)
    calls_made = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('date', 'endpoint', name='_date_endpoint_uc'),
        Index('idx_api_usage_date', 'date'),
    )
    
    def __repr__(self):
        return f'<APIUsage {self.date} {self.endpoint}: {self.calls_made} calls>'
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.calls_made > 0:
            return self.success_count / self.calls_made
        return 0.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.calls_made > 0:
            return self.error_count / self.calls_made
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'endpoint': self.endpoint,
            'calls_made': self.calls_made,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': round(self.success_rate, 3),
            'error_rate': round(self.error_rate, 3)
        }
    
    @classmethod
    def track_call(cls, endpoint: str, success: bool = True):
        """Track an API call"""
        today = date.today()
        
        # Find or create record for today
        usage = cls.query.filter_by(date=today, endpoint=endpoint).first()
        if not usage:
            usage = cls(date=today, endpoint=endpoint)
            db.session.add(usage)
        
        # Update counts
        usage.calls_made += 1
        if success:
            usage.success_count += 1
        else:
            usage.error_count += 1
        
        db.session.commit()
    
    @classmethod
    def get_daily_usage(cls, date: date) -> List['APIUsage']:
        """Get usage for a specific date"""
        return cls.query.filter_by(date=date).all()
    
    @classmethod
    def get_usage_summary(cls, days: int = 30) -> Dict:
        """Get usage summary for the last N days"""
        cutoff_date = date.today() - timedelta(days=days)
        
        results = (
            db.session.query(
                db.func.sum(cls.calls_made).label('total_calls'),
                db.func.sum(cls.success_count).label('total_success'),
                db.func.sum(cls.error_count).label('total_errors'),
                db.func.count(db.distinct(cls.endpoint)).label('unique_endpoints')
            )
            .filter(cls.date >= cutoff_date)
            .first()
        )
        
        return {
            'total_calls': results.total_calls or 0,
            'total_success': results.total_success or 0,
            'total_errors': results.total_errors or 0,
            'unique_endpoints': results.unique_endpoints or 0,
            'success_rate': (
                results.total_success / results.total_calls 
                if results.total_calls else 0
            )
        } 