"""Transcript model"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.orm import relationship

from . import db


class Transcript(db.Model):
    """Model for storing earnings call transcripts"""
    __tablename__ = 'transcripts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    call_date = db.Column(db.DateTime, nullable=False)
    fiscal_year = db.Column(db.Integer, nullable=False)
    fiscal_quarter = db.Column(db.Integer, nullable=False)
    raw_text = db.Column(db.Text)
    cleaned_text = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    fmp_fetch_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sentiment_analysis = relationship(
        'SentimentAnalysis', 
        backref='transcript', 
        uselist=False, 
        cascade='all, delete-orphan'
    )
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('company_id', 'fiscal_year', 'fiscal_quarter', name='_company_fiscal_uc'),
        Index('idx_transcripts_company_date', 'company_id', 'call_date'),
        Index('idx_transcripts_fiscal', 'fiscal_year', 'fiscal_quarter'),
    )
    
    def __repr__(self):
        return f'<Transcript {self.company.ticker if self.company else "?"} {self.fiscal_year}Q{self.fiscal_quarter}>'
    
    @property
    def fiscal_period(self) -> str:
        """Get fiscal period as string"""
        return f"{self.fiscal_year} Q{self.fiscal_quarter}"
    
    @property
    def has_sentiment_analysis(self) -> bool:
        """Check if sentiment analysis has been performed"""
        return self.sentiment_analysis is not None
    
    @property
    def sentiment_score(self) -> Optional[float]:
        """Get overall sentiment score if available"""
        if self.sentiment_analysis:
            return self.sentiment_analysis.overall_sentiment
        return None
    
    @property
    def confidence_score(self) -> Optional[float]:
        """Get management confidence score if available"""
        if self.sentiment_analysis:
            return self.sentiment_analysis.management_confidence_score
        return None
    
    def get_sections(self) -> Dict[str, str]:
        """Get transcript sections"""
        # This would be populated during processing
        # For now, return the full text
        return {
            'full': self.cleaned_text or self.raw_text or '',
            'prepared_remarks': '',
            'qa_section': ''
        }
    
    def to_dict(self, include_sentiment: bool = True) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'ticker': self.company.ticker if self.company else None,
            'company_name': self.company.name if self.company else None,
            'call_date': self.call_date.isoformat() if self.call_date else None,
            'fiscal_year': self.fiscal_year,
            'fiscal_quarter': self.fiscal_quarter,
            'fiscal_period': self.fiscal_period,
            'word_count': self.word_count,
            'has_sentiment_analysis': self.has_sentiment_analysis,
            'fmp_fetch_date': self.fmp_fetch_date.isoformat() if self.fmp_fetch_date else None
        }
        
        if include_sentiment and self.sentiment_analysis:
            data['sentiment'] = {
                'overall_sentiment': self.sentiment_score,
                'management_confidence': self.confidence_score,
                'guidance_sentiment': self.sentiment_analysis.guidance_sentiment
            }
        
        return data
    
    @classmethod
    def find_by_company_and_period(
        cls, 
        company_id: int, 
        year: int, 
        quarter: int
    ) -> Optional['Transcript']:
        """Find transcript by company and fiscal period"""
        return cls.query.filter_by(
            company_id=company_id,
            fiscal_year=year,
            fiscal_quarter=quarter
        ).first()
    
    @classmethod
    def get_recent(cls, days: int = 7, limit: int = 50):
        """Get recently fetched transcripts"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (
            cls.query
            .filter(cls.fmp_fetch_date >= cutoff_date)
            .order_by(cls.fmp_fetch_date.desc())
            .limit(limit)
            .all()
        )
    
    @classmethod
    def get_for_analysis(cls, company_id: int, quarters: int = 4):
        """Get transcripts for trend analysis"""
        return (
            cls.query
            .filter_by(company_id=company_id)
            .order_by(cls.fiscal_year.desc(), cls.fiscal_quarter.desc())
            .limit(quarters + 1)  # Get one extra for comparison
            .all()
        )
    
    def create_from_fmp_data(self, fmp_data: Dict[str, Any], company_id: int) -> 'Transcript':
        """Create transcript from FMP API data"""
        self.company_id = company_id
        self.raw_text = fmp_data.get('content', '')
        
        # Parse date
        date_str = fmp_data.get('date')
        if date_str:
            try:
                self.call_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                self.call_date = datetime.utcnow()
        else:
            self.call_date = datetime.utcnow()
        
        # Set fiscal period
        self.fiscal_year = fmp_data.get('year', self.call_date.year)
        self.fiscal_quarter = fmp_data.get('quarter', (self.call_date.month - 1) // 3 + 1)
        
        # Calculate word count
        if self.raw_text:
            self.word_count = len(self.raw_text.split())
        
        return self 