"""Alert model"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import Index, CheckConstraint, JSON

from . import db


class Alert(db.Model):
    """Model for storing alerts about significant changes"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(
        db.String(20),
        CheckConstraint("severity IN ('low', 'medium', 'high')"),
        nullable=False
    )
    message = db.Column(db.Text, nullable=False)
    data = db.Column(JSON)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_alerts_company', 'company_id', 'created_at'),
        Index('idx_alerts_unresolved', 'resolved'),
    )
    
    def __repr__(self):
        return f'<Alert {self.alert_type} for {self.company.ticker if self.company else "?"} - {self.severity}>'
    
    @property
    def is_high_severity(self) -> bool:
        """Check if alert is high severity"""
        return self.severity == 'high'
    
    @property
    def age_days(self) -> int:
        """Get age of alert in days"""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0
    
    def get_data(self) -> Dict[str, Any]:
        """Get alert data"""
        if self.data and isinstance(self.data, dict):
            return self.data
        return {}
    
    def to_dict(self, include_company: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'data': self.get_data(),
            'resolved': self.resolved,
            'age_days': self.age_days,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_company and self.company:
            data['company'] = {
                'ticker': self.company.ticker,
                'name': self.company.name
            }
        
        return data
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        db.session.commit()
    
    @classmethod
    def create_sentiment_alert(
        cls,
        company_id: int,
        sentiment_change: float,
        previous_sentiment: float,
        current_sentiment: float
    ) -> 'Alert':
        """Create alert for significant sentiment change"""
        severity = 'high' if abs(sentiment_change) > 0.5 else 'medium'
        direction = 'improved' if sentiment_change > 0 else 'declined'
        
        alert = cls(
            company_id=company_id,
            alert_type='sentiment_change',
            severity=severity,
            message=f"Sentiment {direction} by {abs(sentiment_change):.2f} points",
            data={
                'sentiment_change': sentiment_change,
                'previous_sentiment': previous_sentiment,
                'current_sentiment': current_sentiment,
                'direction': direction
            }
        )
        
        return alert
    
    @classmethod
    def create_confidence_alert(
        cls,
        company_id: int,
        confidence_change: float,
        previous_confidence: float,
        current_confidence: float
    ) -> 'Alert':
        """Create alert for significant confidence change"""
        severity = 'high' if abs(confidence_change) > 0.5 else 'medium'
        direction = 'increased' if confidence_change > 0 else 'decreased'
        
        alert = cls(
            company_id=company_id,
            alert_type='confidence_change',
            severity=severity,
            message=f"Management confidence {direction} by {abs(confidence_change):.2f} points",
            data={
                'confidence_change': confidence_change,
                'previous_confidence': previous_confidence,
                'current_confidence': current_confidence,
                'direction': direction
            }
        )
        
        return alert
    
    @classmethod
    def get_unresolved(cls, company_id: Optional[int] = None) -> List['Alert']:
        """Get unresolved alerts"""
        query = cls.query.filter_by(resolved=False)
        
        if company_id:
            query = query.filter_by(company_id=company_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_recent_high_severity(cls, days: int = 7) -> List['Alert']:
        """Get recent high severity alerts"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (
            cls.query
            .filter_by(severity='high')
            .filter(cls.created_at >= cutoff_date)
            .order_by(cls.created_at.desc())
            .all()
        ) 