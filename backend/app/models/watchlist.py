"""Watchlist model"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Index, UniqueConstraint

from . import db


class Watchlist(db.Model):
    """Model for user watchlists"""
    __tablename__ = 'watchlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    alert_threshold = db.Column(db.Float, default=0.2)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name='_user_company_uc'),
    )
    
    def __repr__(self):
        return f'<Watchlist user={self.user_id} company={self.company.ticker if self.company else "?"}>'
    
    def to_dict(self, include_company: bool = True) -> dict:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'company_id': self.company_id,
            'alert_threshold': self.alert_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_company and self.company:
            data['company'] = self.company.to_dict(include_latest=True)
        
        return data
    
    @classmethod
    def get_user_watchlist(cls, user_id: str) -> List['Watchlist']:
        """Get all watchlist items for a user"""
        from .company import Company
        return (
            cls.query
            .filter_by(user_id=user_id)
            .join(Company)
            .order_by(Company.ticker.asc())
            .all()
        )
    
    @classmethod
    def add_to_watchlist(
        cls, 
        user_id: str, 
        company_id: int, 
        alert_threshold: float = 0.2
    ) -> Optional['Watchlist']:
        """Add company to user's watchlist"""
        # Check if already exists
        existing = cls.query.filter_by(
            user_id=user_id, 
            company_id=company_id
        ).first()
        
        if existing:
            # Update threshold if different
            if existing.alert_threshold != alert_threshold:
                existing.alert_threshold = alert_threshold
                db.session.commit()
            return existing
        
        # Create new watchlist item
        watchlist_item = cls(
            user_id=user_id,
            company_id=company_id,
            alert_threshold=alert_threshold
        )
        
        db.session.add(watchlist_item)
        db.session.commit()
        
        return watchlist_item
    
    @classmethod
    def remove_from_watchlist(cls, user_id: str, company_id: int) -> bool:
        """Remove company from user's watchlist"""
        watchlist_item = cls.query.filter_by(
            user_id=user_id,
            company_id=company_id
        ).first()
        
        if watchlist_item:
            db.session.delete(watchlist_item)
            db.session.commit()
            return True
        
        return False
    
    @classmethod
    def is_on_watchlist(cls, user_id: str, company_id: int) -> bool:
        """Check if company is on user's watchlist"""
        return cls.query.filter_by(
            user_id=user_id,
            company_id=company_id
        ).count() > 0
    
    @classmethod
    def get_users_watching_company(cls, company_id: int) -> List[str]:
        """Get list of users watching a specific company"""
        watchlist_items = cls.query.filter_by(company_id=company_id).all()
        return [item.user_id for item in watchlist_items] 