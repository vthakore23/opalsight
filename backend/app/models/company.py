"""Company model"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import Index
from sqlalchemy.orm import relationship, backref

from . import db


class Company(db.Model):
    """Company model for tracking biotech/medtech companies"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    market_cap = db.Column(db.Numeric(20, 2))
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(100))
    exchange = db.Column(db.String(50))
    fmp_has_transcripts = db.Column(db.Boolean, default=False)
    earnings_call_has_transcripts = db.Column(db.Boolean, default=False)
    transcript_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transcripts = relationship('Transcript', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    trend_analyses = relationship('TrendAnalysis', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    alerts = relationship('Alert', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    watchlists = relationship('Watchlist', backref='company', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_companies_market_cap', market_cap),
    )
    
    def __repr__(self):
        return f'<Company {self.ticker}: {self.name}>'
    
    @property
    def is_biotech(self) -> bool:
        """Check if company is in biotech/medtech industry"""
        if not self.industry:
            return False
        
        biotech_keywords = [
            'biotech', 'biotechnology', 'pharmaceutical',
            'drug', 'medical device', 'diagnostic', 'therapeutics'
        ]
        industry_lower = self.industry.lower()
        return any(keyword in industry_lower for keyword in biotech_keywords)
    
    @property
    def market_cap_billions(self) -> Optional[float]:
        """Get market cap in billions"""
        if self.market_cap:
            return float(self.market_cap) / 1_000_000_000
        return None
    
    @property
    def latest_transcript(self):
        """Get the most recent transcript"""
        return self.transcripts.order_by(
            db.desc('fiscal_year'), 
            db.desc('fiscal_quarter')
        ).first()
    
    @property
    def latest_trend(self):
        """Get the most recent trend analysis"""
        return self.trend_analyses.order_by(
            db.desc('analysis_date')
        ).first()
    
    def get_transcript_history(self, limit: int = 8):
        """Get transcript history with sentiment data"""
        return (
            db.session.query(self.transcripts)
            .join('sentiment_analysis')
            .order_by(
                db.desc('fiscal_year'),
                db.desc('fiscal_quarter')
            )
            .limit(limit)
            .all()
        )
    
    def to_dict(self, include_latest: bool = False) -> dict:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'ticker': self.ticker,
            'name': self.name,
            'market_cap': float(self.market_cap) if self.market_cap else None,
            'market_cap_billions': self.market_cap_billions,
            'sector': self.sector,
            'industry': self.industry,
            'exchange': self.exchange,
            'is_biotech': self.is_biotech,
            'transcript_count': self.transcript_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        
        if include_latest:
            latest_transcript = self.latest_transcript
            if latest_transcript:
                data['latest_transcript'] = {
                    'date': latest_transcript.call_date.isoformat(),
                    'fiscal_period': f"{latest_transcript.fiscal_year} Q{latest_transcript.fiscal_quarter}"
                }
            
            latest_trend = self.latest_trend
            if latest_trend:
                data['latest_trend'] = {
                    'category': latest_trend.trend_category,
                    'sentiment_change': float(latest_trend.sentiment_change) if latest_trend.sentiment_change else None,
                    'confidence_change': float(latest_trend.confidence_change) if latest_trend.confidence_change else None
                }
        
        return data
    
    @classmethod
    def find_by_ticker(cls, ticker: str) -> Optional['Company']:
        """Find company by ticker symbol"""
        return cls.query.filter_by(ticker=ticker.upper()).first()
    
    @classmethod
    def get_biotech_companies(cls, min_market_cap: Optional[float] = None) -> List['Company']:
        """Get all biotech/medtech companies"""
        query = cls.query
        
        if min_market_cap:
            query = query.filter(cls.market_cap >= min_market_cap)
        
        # Filter for biotech/medtech
        biotech_filter = db.or_(
            cls.industry.ilike('%biotech%'),
            cls.industry.ilike('%pharmaceutical%'),
            cls.industry.ilike('%drug%'),
            cls.industry.ilike('%medical device%'),
            cls.industry.ilike('%diagnostic%'),
            cls.industry.ilike('%therapeutics%')
        )
        
        return query.filter(biotech_filter).all()
    
    @classmethod
    def get_with_recent_transcripts(cls, days: int = 7) -> List['Company']:
        """Get companies with transcripts in the last N days"""
        from .transcript import Transcript
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (
            cls.query
            .join(Transcript)
            .filter(Transcript.fmp_fetch_date >= cutoff_date)
            .distinct()
            .all()
        ) 