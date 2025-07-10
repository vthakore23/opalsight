"""Trend Analysis Service"""
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from app.models import db, Company, Transcript, SentimentAnalysis, TrendAnalysis, Alert

logger = logging.getLogger(__name__)


@dataclass
class TrendResult:
    """Container for trend analysis results"""
    company_id: int
    trend_category: str
    sentiment_trend: Dict[str, Any]
    confidence_trend: Dict[str, Any]
    latest_sentiment: float
    latest_confidence: float
    notable_changes: List[Dict[str, Any]]
    comparison_window: int
    analysis_date: date


class TrendAnalyzer:
    """Service for analyzing sentiment trends over time"""
    
    def __init__(self, lookback_quarters: int = 4):
        self.lookback_quarters = lookback_quarters
        self.significance_threshold = 0.2
    
    def analyze_company_trend(self, company_id: int, 
                            lookback_quarters: Optional[int] = None) -> Optional[TrendResult]:
        """Analyze sentiment trend for a company"""
        try:
            if lookback_quarters is None:
                lookback_quarters = self.lookback_quarters
            
            # Fetch historical analyses
            analyses = self._fetch_historical_analyses(company_id, lookback_quarters + 1)
            
            if len(analyses) < 2:
                logger.warning(f"Insufficient data for trend analysis: company_id={company_id}")
                return self._create_insufficient_data_result(company_id)
            
            # Separate latest from historical
            latest = analyses[0]
            historical = analyses[1:]
            
            # Calculate trends
            sentiment_trend = self._calculate_trend(
                [a['overall_sentiment'] for a in analyses]
            )
            
            confidence_trend = self._calculate_trend(
                [a['management_confidence_score'] for a in analyses]
            )
            
            # Determine overall trend category
            trend_category = self._categorize_trend(
                sentiment_trend, 
                confidence_trend,
                latest,
                historical
            )
            
            # Extract notable changes
            notable_changes = self._extract_notable_changes(latest, historical)
            
            # Check for alerts
            self._check_for_alerts(company_id, latest, historical, sentiment_trend, confidence_trend)
            
            return TrendResult(
                company_id=company_id,
                trend_category=trend_category,
                sentiment_trend=sentiment_trend,
                confidence_trend=confidence_trend,
                latest_sentiment=latest['overall_sentiment'],
                latest_confidence=latest['management_confidence_score'],
                notable_changes=notable_changes,
                comparison_window=lookback_quarters,
                analysis_date=date.today()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trend for company {company_id}: {str(e)}")
            raise
    
    def _fetch_historical_analyses(self, company_id: int, limit: int) -> List[Dict[str, Any]]:
        """Fetch historical sentiment analyses"""
        results = (
            db.session.query(
                Transcript.fiscal_year,
                Transcript.fiscal_quarter,
                Transcript.call_date,
                SentimentAnalysis.overall_sentiment,
                SentimentAnalysis.management_confidence_score,
                SentimentAnalysis.guidance_sentiment,
                SentimentAnalysis.confidence_indicators,
                SentimentAnalysis.product_mentions
            )
            .join(SentimentAnalysis, Transcript.id == SentimentAnalysis.transcript_id)
            .filter(Transcript.company_id == company_id)
            .order_by(Transcript.fiscal_year.desc(), Transcript.fiscal_quarter.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                'fiscal_year': r[0],
                'fiscal_quarter': r[1],
                'call_date': r[2],
                'overall_sentiment': r[3] or 0.0,
                'management_confidence_score': r[4] or 0.0,
                'guidance_sentiment': r[5] or 0.0,
                'confidence_indicators': r[6] or {},
                'product_mentions': r[7] or []
            }
            for r in results
        ]
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend statistics"""
        if len(values) < 2:
            return {
                'direction': 'stable',
                'slope': 0.0,
                'change': 0.0,
                'latest': values[0] if values else 0.0,
                'average_historical': 0.0,
                'std_dev': 0.0,
                'trend_strength': 0.0
            }
        
        # Simple linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Flip x because values are in reverse chronological order
        x = x[::-1]
        
        # Calculate slope using polyfit
        coefficients = np.polyfit(x, y, 1)
        slope = float(coefficients[0])
        
        # Calculate change magnitude
        change = float(values[0] - np.mean(values[1:]))
        
        # Calculate standard deviation
        std_dev = float(np.std(values))
        
        # Calculate trend strength (normalized slope)
        trend_strength = abs(slope) / (std_dev + 0.01)  # Add small value to avoid division by zero
        
        # Determine direction
        if slope > 0.05 and change > 0.1:
            direction = 'improving'
        elif slope < -0.05 and change < -0.1:
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'slope': slope,
            'change': change,
            'latest': float(values[0]),
            'average_historical': float(np.mean(values[1:])),
            'std_dev': std_dev,
            'trend_strength': float(trend_strength),
            'values': [float(v) for v in values]  # Include actual values for visualization
        }
    
    def _categorize_trend(self, sentiment_trend: Dict[str, Any], 
                        confidence_trend: Dict[str, Any],
                        latest: Dict[str, Any],
                        historical: List[Dict[str, Any]]) -> str:
        """Categorize overall trend"""
        # Weighted scoring
        sentiment_weight = 0.6
        confidence_weight = 0.4
        
        # Calculate direction scores
        direction_scores = {
            'improving': 0,
            'stable': 0,
            'declining': 0
        }
        
        # Add sentiment trend score
        if sentiment_trend['direction'] == 'improving':
            direction_scores['improving'] += sentiment_weight
        elif sentiment_trend['direction'] == 'declining':
            direction_scores['declining'] += sentiment_weight
        else:
            direction_scores['stable'] += sentiment_weight
        
        # Add confidence trend score
        if confidence_trend['direction'] == 'improving':
            direction_scores['improving'] += confidence_weight
        elif confidence_trend['direction'] == 'declining':
            direction_scores['declining'] += confidence_weight
        else:
            direction_scores['stable'] += confidence_weight
        
        # Check absolute levels
        if latest['overall_sentiment'] < -0.3 and latest['management_confidence_score'] < -0.3:
            direction_scores['declining'] += 0.5
        elif latest['overall_sentiment'] > 0.3 and latest['management_confidence_score'] > 0.3:
            direction_scores['improving'] += 0.5
        
        # Check magnitude of changes
        if abs(sentiment_trend['change']) > 0.3 or abs(confidence_trend['change']) > 0.3:
            if sentiment_trend['change'] > 0:
                direction_scores['improving'] += 0.3
            else:
                direction_scores['declining'] += 0.3
        
        # Determine final category
        max_score = max(direction_scores.values())
        for category, score in direction_scores.items():
            if score == max_score:
                return category
        
        return 'stable'
    
    def _extract_notable_changes(self, latest: Dict[str, Any], 
                               historical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract notable changes in language and metrics"""
        changes = []
        
        # Calculate historical averages
        hist_avg_positive = np.mean([
            h['confidence_indicators'].get('positive_count', 0) 
            for h in historical
        ])
        hist_avg_negative = np.mean([
            h['confidence_indicators'].get('negative_count', 0) 
            for h in historical
        ])
        
        latest_indicators = latest['confidence_indicators']
        
        # Check for significant increase in positive language
        if latest_indicators.get('positive_count', 0) > hist_avg_positive * 1.5:
            changes.append({
                'type': 'positive_language_increase',
                'description': 'Significant increase in positive language',
                'magnitude': 'high',
                'details': {
                    'current': latest_indicators.get('positive_count', 0),
                    'historical_avg': hist_avg_positive,
                    'increase_factor': latest_indicators.get('positive_count', 0) / (hist_avg_positive + 1)
                }
            })
        
        # Check for significant increase in negative language
        if latest_indicators.get('negative_count', 0) > hist_avg_negative * 1.5:
            changes.append({
                'type': 'negative_language_increase',
                'description': 'Notable increase in cautionary language',
                'magnitude': 'high',
                'details': {
                    'current': latest_indicators.get('negative_count', 0),
                    'historical_avg': hist_avg_negative,
                    'increase_factor': latest_indicators.get('negative_count', 0) / (hist_avg_negative + 1)
                }
            })
        
        # Check for new product mentions
        latest_products = set(p['name'] for p in latest.get('product_mentions', []))
        historical_products = set()
        for h in historical:
            for p in h.get('product_mentions', []):
                historical_products.add(p['name'])
        
        new_products = latest_products - historical_products
        if new_products:
            changes.append({
                'type': 'new_product_mentions',
                'description': f'New product mentions: {", ".join(list(new_products)[:3])}',
                'magnitude': 'medium',
                'details': {
                    'new_products': list(new_products),
                    'count': len(new_products)
                }
            })
        
        # Check for guidance changes
        if latest.get('guidance_sentiment') is not None:
            hist_guidance_avg = np.mean([
                h.get('guidance_sentiment', 0) for h in historical 
                if h.get('guidance_sentiment') is not None
            ])
            
            guidance_change = latest['guidance_sentiment'] - hist_guidance_avg
            if abs(guidance_change) > 0.3:
                changes.append({
                    'type': 'guidance_sentiment_change',
                    'description': f'Guidance sentiment {"improved" if guidance_change > 0 else "declined"} significantly',
                    'magnitude': 'high',
                    'details': {
                        'current': latest['guidance_sentiment'],
                        'historical_avg': hist_guidance_avg,
                        'change': guidance_change
                    }
                })
        
        return changes
    
    def _check_for_alerts(self, company_id: int, latest: Dict[str, Any],
                         historical: List[Dict[str, Any]], 
                         sentiment_trend: Dict[str, Any],
                         confidence_trend: Dict[str, Any]):
        """Check if alerts should be created"""
        # Check for significant sentiment change
        if abs(sentiment_trend['change']) > self.significance_threshold:
            previous_sentiment = historical[0]['overall_sentiment'] if historical else 0
            
            alert = Alert.create_sentiment_alert(
                company_id=company_id,
                sentiment_change=sentiment_trend['change'],
                previous_sentiment=previous_sentiment,
                current_sentiment=latest['overall_sentiment']
            )
            db.session.add(alert)
        
        # Check for significant confidence change
        if abs(confidence_trend['change']) > self.significance_threshold:
            previous_confidence = historical[0]['management_confidence_score'] if historical else 0
            
            alert = Alert.create_confidence_alert(
                company_id=company_id,
                confidence_change=confidence_trend['change'],
                previous_confidence=previous_confidence,
                current_confidence=latest['management_confidence_score']
            )
            db.session.add(alert)
        
        # Commit alerts if any were created
        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to create alerts: {str(e)}")
            db.session.rollback()
    
    def _create_insufficient_data_result(self, company_id: int) -> TrendResult:
        """Create result for insufficient data"""
        return TrendResult(
            company_id=company_id,
            trend_category='insufficient_data',
            sentiment_trend={'direction': 'insufficient_data', 'slope': 0, 'change': 0},
            confidence_trend={'direction': 'insufficient_data', 'slope': 0, 'change': 0},
            latest_sentiment=0.0,
            latest_confidence=0.0,
            notable_changes=[],
            comparison_window=self.lookback_quarters,
            analysis_date=date.today()
        )
    
    def save_trend_analysis(self, trend_result: TrendResult) -> TrendAnalysis:
        """Save trend analysis to database"""
        trend_analysis = TrendAnalysis(
            company_id=trend_result.company_id,
            analysis_date=trend_result.analysis_date,
            trend_category=trend_result.trend_category,
            sentiment_change=trend_result.sentiment_trend.get('change', 0),
            confidence_change=trend_result.confidence_trend.get('change', 0),
            key_changes=trend_result.notable_changes,
            notable_quotes=[],  # To be implemented
            comparison_window=trend_result.comparison_window
        )
        
        db.session.add(trend_analysis)
        db.session.commit()
        
        return trend_analysis
    
    def get_market_overview(self, analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """Get market-wide trend overview"""
        if analysis_date is None:
            analysis_date = date.today()
        
        # Get summary statistics
        stats = TrendAnalysis.get_summary_stats(analysis_date)
        
        # Get recent significant changes
        significant_changes = TrendAnalysis.get_significant_changes(days=7, threshold=0.2)
        
        # Calculate percentages
        total = sum(stats.values())
        percentages = {
            k: (v / total * 100) if total > 0 else 0 
            for k, v in stats.items()
        }
        
        return {
            'analysis_date': analysis_date.isoformat(),
            'summary': stats,
            'percentages': percentages,
            'total_companies': total,
            'significant_changes': len(significant_changes),
            'top_movers': [
                {
                    'company_id': t.company_id,
                    'ticker': t.company.ticker if t.company else None,
                    'name': t.company.name if t.company else None,
                    'trend': t.trend_category,
                    'sentiment_change': t.sentiment_change,
                    'confidence_change': t.confidence_change
                }
                for t in significant_changes[:10]
            ]
        } 