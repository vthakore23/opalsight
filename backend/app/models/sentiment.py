"""Sentiment Analysis model"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from sqlalchemy import Index, JSON

from . import db


class SentimentAnalysis(db.Model):
    """Model for storing sentiment analysis results"""
    __tablename__ = 'sentiment_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    transcript_id = db.Column(
        db.Integer, 
        db.ForeignKey('transcripts.id', ondelete='CASCADE'), 
        nullable=False,
        unique=True
    )
    overall_sentiment = db.Column(db.Float)
    management_confidence_score = db.Column(db.Float)
    guidance_sentiment = db.Column(db.Float)
    product_mentions = db.Column(JSON)
    confidence_indicators = db.Column(JSON)
    key_topics = db.Column(JSON)
    sentiment_by_section = db.Column(JSON)
    gpt_enhanced = db.Column(db.Boolean, default=False)
    gpt_insights = db.Column(JSON)
    key_quotes = db.Column(JSON)  # New field for extracted quotes
    extracted_guidance = db.Column(JSON)  # New field for guidance extraction
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_sentiment_transcript', 'transcript_id'),
        Index('idx_sentiment_scores', 'overall_sentiment', 'management_confidence_score'),
    )
    
    def __repr__(self):
        return f'<SentimentAnalysis transcript_id={self.transcript_id} sentiment={self.overall_sentiment:.2f}>'
    
    @property
    def is_positive(self) -> bool:
        """Check if overall sentiment is positive"""
        return self.overall_sentiment > 0.1 if self.overall_sentiment else False
    
    @property
    def is_negative(self) -> bool:
        """Check if overall sentiment is negative"""
        return self.overall_sentiment < -0.1 if self.overall_sentiment else False
    
    @property
    def sentiment_label(self) -> str:
        """Get sentiment label"""
        if self.overall_sentiment is None:
            return 'unknown'
        elif self.overall_sentiment > 0.1:
            return 'positive'
        elif self.overall_sentiment < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    @property
    def confidence_label(self) -> str:
        """Get confidence label"""
        if self.management_confidence_score is None:
            return 'unknown'
        elif self.management_confidence_score > 0.3:
            return 'high'
        elif self.management_confidence_score < -0.3:
            return 'low'
        else:
            return 'moderate'
    
    def get_product_mentions(self) -> List[Dict[str, Any]]:
        """Get product mentions as list"""
        if self.product_mentions:
            return self.product_mentions if isinstance(self.product_mentions, list) else []
        return []
    
    def get_confidence_indicators(self) -> Dict[str, Any]:
        """Get confidence indicators"""
        if self.confidence_indicators:
            return self.confidence_indicators if isinstance(self.confidence_indicators, dict) else {}
        return {
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'phrases': [],
            'score': 0.0
        }
    
    def get_key_topics(self) -> List[str]:
        """Get key topics discussed"""
        if self.key_topics:
            if isinstance(self.key_topics, list):
                return self.key_topics
            elif isinstance(self.key_topics, dict) and 'topics' in self.key_topics:
                return self.key_topics['topics']
        return []
    
    def get_section_sentiments(self) -> Dict[str, float]:
        """Get sentiment scores by section"""
        if self.sentiment_by_section and isinstance(self.sentiment_by_section, dict):
            return {
                section: data.get('score', 0.0) if isinstance(data, dict) else 0.0
                for section, data in self.sentiment_by_section.items()
            }
        return {}
    
    def get_gpt_insights(self) -> Optional[str]:
        """Get GPT-generated insights if available"""
        if self.gpt_insights and isinstance(self.gpt_insights, dict):
            return self.gpt_insights.get('insights')
        return None
    
    def get_key_quotes(self) -> List[Dict[str, Any]]:
        """Get extracted key quotes"""
        if self.key_quotes and isinstance(self.key_quotes, list):
            return self.key_quotes
        return []
    
    def get_extracted_guidance(self) -> List[Dict[str, Any]]:
        """Get extracted guidance items"""
        if self.extracted_guidance and isinstance(self.extracted_guidance, list):
            return self.extracted_guidance
        return []
    
    def to_dict(self, detailed: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'transcript_id': self.transcript_id,
            'overall_sentiment': self.overall_sentiment,
            'sentiment_label': self.sentiment_label,
            'management_confidence_score': self.management_confidence_score,
            'confidence_label': self.confidence_label,
            'guidance_sentiment': self.guidance_sentiment,
            'gpt_enhanced': self.gpt_enhanced,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if detailed:
            data.update({
                'product_mentions': self.get_product_mentions(),
                'confidence_indicators': self.get_confidence_indicators(),
                'key_topics': self.get_key_topics(),
                'sentiment_by_section': self.get_section_sentiments(),
                'gpt_insights': self.get_gpt_insights(),
                'key_quotes': self.get_key_quotes(),
                'extracted_guidance': self.get_extracted_guidance()
            })
        
        return data
    
    @classmethod
    def create_from_analysis(cls, transcript_id: int, analysis_data: Dict[str, Any]) -> 'SentimentAnalysis':
        """Create from analysis results"""
        sentiment = cls(transcript_id=transcript_id)
        
        # Core sentiment scores
        sentiment.overall_sentiment = analysis_data.get('overall_sentiment')
        sentiment.management_confidence_score = analysis_data.get('management_confidence_score')
        sentiment.guidance_sentiment = analysis_data.get('guidance_sentiment')
        
        # Structured data
        sentiment.product_mentions = analysis_data.get('product_mentions', [])
        sentiment.confidence_indicators = analysis_data.get('confidence_indicators', {})
        sentiment.key_topics = analysis_data.get('key_topics', {})
        sentiment.sentiment_by_section = analysis_data.get('sentiment_by_section', {})
        
        # GPT enhancement
        if 'gpt_insights' in analysis_data:
            sentiment.gpt_enhanced = True
            sentiment.gpt_insights = analysis_data['gpt_insights']
        
        return sentiment
    
    @classmethod
    def get_by_company(cls, company_id: int, limit: int = 10):
        """Get sentiment analyses for a company"""
        from .transcript import Transcript
        
        return (
            cls.query
            .join(Transcript)
            .filter(Transcript.company_id == company_id)
            .order_by(Transcript.fiscal_year.desc(), Transcript.fiscal_quarter.desc())
            .limit(limit)
            .all()
        )
    
    @classmethod
    def get_extreme_sentiments(
        cls, 
        threshold: float = 0.5, 
        days: int = 30,
        sentiment_type: str = 'both'
    ) -> List['SentimentAnalysis']:
        """Get analyses with extreme sentiment scores"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = cls.query.filter(cls.created_at >= cutoff_date)
        
        if sentiment_type == 'positive':
            query = query.filter(cls.overall_sentiment > threshold)
        elif sentiment_type == 'negative':
            query = query.filter(cls.overall_sentiment < -threshold)
        else:  # both
            query = query.filter(
                db.or_(
                    cls.overall_sentiment > threshold,
                    cls.overall_sentiment < -threshold
                )
            )
        
        return query.order_by(db.func.abs(cls.overall_sentiment).desc()).all() 