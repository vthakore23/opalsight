#!/usr/bin/env python3
"""
Real Data Collector for Q1 2025 Earnings
Fetches actual earnings call transcripts and performs comprehensive analysis
"""
import logging
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import aiohttp
import requests
from dataclasses import dataclass

from app.models import db, Company, Transcript, SentimentAnalysis, TrendAnalysis, Alert
from app.services.earnings_call_client import EarningsCallClient, EarningsCallError
from app.services.fmp_client import FMPClient, FMPError
from app.services.sentiment_analyzer import SentimentAnalyzer
from config.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class QuoteExtraction:
    """Structure for extracted quotes"""
    text: str
    speaker: str
    context: str
    sentiment_score: float
    topic: str


@dataclass
class GuidanceExtraction:
    """Structure for extracted guidance"""
    metric: str
    value: str
    timeframe: str
    confidence: str
    change_from_previous: Optional[str] = None


class RealDataCollector:
    """Comprehensive real data collection service for Q1 2025"""
    
    def __init__(self, config=None):
        """Initialize the real data collector"""
        self.config = config or get_config()
        self.earnings_client = EarningsCallClient(config=self.config)
        self.fmp_client = FMPClient(config=self.config)
        self.sentiment_analyzer = SentimentAnalyzer(config=self.config)
        
        # Target companies for Q1 2025 real data collection
        self.target_biotech_companies = [
            # High-priority biotech companies with regular earnings calls
            'BIIB', 'GILD', 'REGN', 'VRTX', 'ALNY', 'MRNA', 'BNTX',  # Large cap
            'HALO', 'SAGE', 'BGNE', 'EXEL', 'IOVA', 'FOLD', 'RARE',  # Mid cap
            'HROW', 'ETON', 'LQDA', 'RYTM', 'CDXS', 'SNWVD',        # Small cap (our existing)
            'TMDX', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VERV',         # Gene editing
            'NTRA', 'DNLI', 'ADAP', 'PRTA', 'MRTX', 'PRTK'          # Precision medicine
        ]
    
    async def collect_q1_2025_data(self) -> Dict[str, Any]:
        """Main entry point for Q1 2025 real data collection"""
        logger.info("Starting Q1 2025 real data collection...")
        
        results = {
            'companies_processed': 0,
            'transcripts_fetched': 0,
            'transcripts_analyzed': 0,
            'trends_generated': 0,
            'alerts_created': 0,
            'errors': [],
            'summary': {}
        }
        
        try:
            # Step 1: Update company database with target companies
            await self._update_company_database()
            
            # Step 2: Fetch Q1 2025 transcripts
            transcripts = await self._fetch_q1_2025_transcripts()
            results['transcripts_fetched'] = len(transcripts)
            
            # Step 3: Process each transcript with enhanced analysis
            for transcript_data in transcripts:
                try:
                    processed = await self._process_transcript_with_enhancement(transcript_data)
                    if processed:
                        results['transcripts_analyzed'] += 1
                        results['companies_processed'] += 1
                        
                        # Generate trend analysis
                        trend = await self._generate_trend_analysis(processed['company_id'])
                        if trend:
                            results['trends_generated'] += 1
                        
                        # Check for alerts
                        alerts = await self._check_for_alerts(processed)
                        results['alerts_created'] += len(alerts)
                
                except Exception as e:
                    error_msg = f"Error processing transcript for {transcript_data.get('symbol', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Step 4: Generate summary statistics
            results['summary'] = await self._generate_collection_summary()
            
            logger.info(f"Q1 2025 data collection completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Q1 2025 data collection failed: {str(e)}")
            results['errors'].append(str(e))
            return results
    
    async def _update_company_database(self):
        """Update database with target biotech companies"""
        logger.info("Updating company database...")
        
        for ticker in self.target_biotech_companies:
            try:
                # Check if company exists
                company = Company.find_by_ticker(ticker)
                
                if not company:
                    # Fetch company profile from FMP
                    profile = self.fmp_client.get_company_profile(ticker)
                    
                    if profile:
                        company = Company(
                            ticker=ticker,
                            name=profile.get('companyName', ''),
                            market_cap=profile.get('mktCap', 0),
                            sector=profile.get('sector', 'Healthcare'),
                            industry=profile.get('industry', 'Biotechnology'),
                            exchange=profile.get('exchangeShortName', 'NASDAQ'),
                            earnings_call_has_transcripts=True
                        )
                        db.session.add(company)
                        logger.info(f"Added new company: {ticker} - {company.name}")
                
                # Update earnings call availability
                if company:
                    company.earnings_call_has_transcripts = True
                    
            except Exception as e:
                logger.error(f"Error updating company {ticker}: {str(e)}")
        
        db.session.commit()
    
    async def _fetch_q1_2025_transcripts(self) -> List[Dict[str, Any]]:
        """Fetch Q1 2025 earnings call transcripts"""
        logger.info("Fetching Q1 2025 transcripts...")
        
        transcripts = []
        
        # Q1 2025 earnings calls typically happen in April-May 2025
        target_quarters = [
            (2025, 1),  # Q1 2025 reports
            (2024, 4),  # Q4 2024 reports (for comparison)
        ]
        
        for ticker in self.target_biotech_companies:
            company = Company.find_by_ticker(ticker)
            if not company:
                continue
                
            for year, quarter in target_quarters:
                try:
                    # Try Earnings Call API first
                    transcript = self.earnings_client.get_transcript(ticker, year, quarter)
                    
                    if not transcript:
                        # Try FMP API as backup
                        transcript = self.fmp_client.get_transcript(ticker, year, quarter)
                    
                    if transcript:
                        # Standardize format
                        standardized = {
                            'company_id': company.id,
                            'symbol': ticker,
                            'year': year,
                            'quarter': quarter,
                            'content': transcript.get('content', '') or transcript.get('transcript', ''),
                            'date': transcript.get('date'),
                            'participants': transcript.get('participants', []),
                            'source': 'earnings_call' if 'content' in transcript else 'fmp'
                        }
                        
                        if standardized['content']:
                            transcripts.append(standardized)
                            logger.info(f"Fetched transcript: {ticker} {year}Q{quarter}")
                        
                except Exception as e:
                    logger.error(f"Error fetching transcript {ticker} {year}Q{quarter}: {str(e)}")
        
        logger.info(f"Fetched {len(transcripts)} transcripts")
        return transcripts
    
    async def _process_transcript_with_enhancement(self, transcript_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process transcript with enhanced sentiment analysis and quote extraction"""
        try:
            company_id = transcript_data['company_id']
            content = transcript_data['content']
            
            # Check if transcript already exists
            existing = Transcript.query.filter_by(
                company_id=company_id,
                fiscal_year=transcript_data['year'],
                fiscal_quarter=transcript_data['quarter']
            ).first()
            
            if existing:
                logger.info(f"Transcript already exists: {transcript_data['symbol']} {transcript_data['year']}Q{transcript_data['quarter']}")
                return None
            
            # Clean and process the transcript
            cleaned_content = self._clean_transcript_text(content)
            
            # Extract quotes and guidance
            quotes = self._extract_key_quotes(cleaned_content)
            guidance = self._extract_guidance(cleaned_content)
            
            # Perform enhanced sentiment analysis
            sentiment_result = self.sentiment_analyzer.analyze_text(cleaned_content)
            
            # Create transcript record
            transcript = Transcript(
                company_id=company_id,
                call_date=datetime.strptime(transcript_data['date'], '%Y-%m-%d').date() if transcript_data.get('date') else date.today(),
                fiscal_year=transcript_data['year'],
                fiscal_quarter=transcript_data['quarter'],
                raw_text=content,
                cleaned_text=cleaned_content,
                word_count=len(cleaned_content.split())
            )
            
            db.session.add(transcript)
            db.session.flush()  # Get the ID
            
            # Create enhanced sentiment analysis
            sentiment = SentimentAnalysis(
                transcript_id=transcript.id,
                overall_sentiment=sentiment_result.get('overall_sentiment', 0),
                management_confidence_score=sentiment_result.get('confidence', 0),
                guidance_sentiment=sentiment_result.get('guidance_sentiment', 0),
                product_mentions=self._extract_product_mentions(cleaned_content),
                confidence_indicators=sentiment_result.get('confidence_indicators', {}),
                key_topics=sentiment_result.get('key_topics', []),
                sentiment_by_section=sentiment_result.get('sentiment_by_section', {}),
                gpt_enhanced=False,
                key_quotes=[quote.__dict__ for quote in quotes],
                extracted_guidance=[guidance_item.__dict__ for guidance_item in guidance]
            )
            
            db.session.add(sentiment)
            db.session.commit()
            
            logger.info(f"Processed transcript: {transcript_data['symbol']} {transcript_data['year']}Q{transcript_data['quarter']}")
            
            return {
                'transcript_id': transcript.id,
                'company_id': company_id,
                'sentiment_analysis': sentiment,
                'quotes': quotes,
                'guidance': guidance
            }
            
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
            db.session.rollback()
            return None
    
    def _clean_transcript_text(self, text: str) -> str:
        """Clean and normalize transcript text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove timestamps and formatting artifacts
        text = re.sub(r'\[\d+:\d+:\d+\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)  # Remove parenthetical notes
        
        # Clean up speaker indicators
        text = re.sub(r'^[A-Z\s]+:', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    def _extract_key_quotes(self, text: str) -> List[QuoteExtraction]:
        """Extract key quotes from the transcript"""
        quotes = []
        
        # Patterns for important statements
        important_patterns = [
            r'(we (?:expect|anticipate|believe|are confident|project).*?[.!])',
            r'(our guidance.*?[.!])',
            r'(revenue.*?(?:increased|decreased|grew|declined).*?[.!])',
            r'(clinical trial.*?(?:results|data|outcomes).*?[.!])',
            r'(fda.*?(?:approval|clearance|submission).*?[.!])',
            r'(pipeline.*?(?:advancing|progress|development).*?[.!])'
        ]
        
        for pattern in important_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                quote_text = match.group(1).strip()
                if len(quote_text) > 20 and len(quote_text) < 300:  # Reasonable quote length
                    # Analyze sentiment of the quote
                    quote_sentiment = self.sentiment_analyzer.analyze_text(quote_text)
                    
                    quote = QuoteExtraction(
                        text=quote_text,
                        speaker="Management",  # Could be enhanced to detect specific speakers
                        context=self._determine_quote_context(quote_text),
                        sentiment_score=quote_sentiment.get('overall_sentiment', 0),
                        topic=self._categorize_quote_topic(quote_text)
                    )
                    quotes.append(quote)
        
        return quotes[:10]  # Limit to top 10 quotes
    
    def _extract_guidance(self, text: str) -> List[GuidanceExtraction]:
        """Extract financial and operational guidance"""
        guidance = []
        
        # Patterns for guidance statements
        guidance_patterns = [
            r'(?:revenue|sales|earnings).*?(?:expect|guidance|target|project).*?(\$[\d.,]+\s*(?:million|billion|M|B))',
            r'(?:expect|guidance|target|project).*?(?:revenue|sales|earnings).*?(\$[\d.,]+\s*(?:million|billion|M|B))',
            r'(?:patient enrollment|trial completion|data readout).*?(Q[1-4]|quarter|month).*?(\d{4})',
            r'(?:fda|regulatory).*?(?:filing|submission|approval).*?(Q[1-4]|quarter|month).*?(\d{4})'
        ]
        
        for pattern in guidance_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                guidance_text = match.group(0)
                
                guidance_item = GuidanceExtraction(
                    metric=self._extract_guidance_metric(guidance_text),
                    value=self._extract_guidance_value(guidance_text),
                    timeframe=self._extract_guidance_timeframe(guidance_text),
                    confidence=self._extract_guidance_confidence(guidance_text)
                )
                guidance.append(guidance_item)
        
        return guidance[:5]  # Limit to top 5 guidance items
    
    def _extract_product_mentions(self, text: str) -> List[str]:
        """Extract product/drug mentions"""
        # Common biotech product naming patterns
        product_patterns = [
            r'\b[A-Z]{2,}-\d+\b',  # Drug codes like AB-123
            r'\b[a-z]+mab\b',      # Monoclonal antibodies
            r'\b[A-Z][a-z]+\d+\b', # Product names like Drug123
        ]
        
        products = set()
        for pattern in product_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                products.add(match.group(0))
        
        return list(products)[:10]
    
    def _determine_quote_context(self, quote: str) -> str:
        """Determine the context of a quote"""
        quote_lower = quote.lower()
        
        if any(word in quote_lower for word in ['revenue', 'sales', 'earnings', 'financial']):
            return 'financial'
        elif any(word in quote_lower for word in ['clinical', 'trial', 'patient', 'study']):
            return 'clinical'
        elif any(word in quote_lower for word in ['fda', 'regulatory', 'approval', 'submission']):
            return 'regulatory'
        elif any(word in quote_lower for word in ['pipeline', 'development', 'research']):
            return 'pipeline'
        else:
            return 'general'
    
    def _categorize_quote_topic(self, quote: str) -> str:
        """Categorize the topic of a quote"""
        quote_lower = quote.lower()
        
        topics = {
            'financial_performance': ['revenue', 'earnings', 'profit', 'cash', 'expenses'],
            'clinical_development': ['clinical', 'trial', 'patient', 'efficacy', 'safety'],
            'regulatory_affairs': ['fda', 'approval', 'submission', 'regulatory', 'compliance'],
            'business_strategy': ['partnership', 'acquisition', 'expansion', 'market', 'competition'],
            'pipeline_progress': ['pipeline', 'development', 'research', 'discovery', 'candidate']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in quote_lower for keyword in keywords):
                return topic
        
        return 'other'
    
    def _extract_guidance_metric(self, text: str) -> str:
        """Extract the metric being guided"""
        text_lower = text.lower()
        
        if 'revenue' in text_lower or 'sales' in text_lower:
            return 'revenue'
        elif 'earnings' in text_lower or 'eps' in text_lower:
            return 'earnings'
        elif 'enrollment' in text_lower:
            return 'patient_enrollment'
        elif 'approval' in text_lower or 'filing' in text_lower:
            return 'regulatory_milestone'
        else:
            return 'unknown'
    
    def _extract_guidance_value(self, text: str) -> str:
        """Extract the numerical value from guidance"""
        # Look for monetary values
        money_match = re.search(r'\$[\d.,]+\s*(?:million|billion|M|B)', text, re.IGNORECASE)
        if money_match:
            return money_match.group(0)
        
        # Look for other numerical values
        number_match = re.search(r'\d+(?:,\d+)*(?:\.\d+)?', text)
        if number_match:
            return number_match.group(0)
        
        return 'Not specified'
    
    def _extract_guidance_timeframe(self, text: str) -> str:
        """Extract the timeframe for guidance"""
        timeframe_match = re.search(r'(Q[1-4]\s*\d{4}|quarter\s*\d+|month\s*\d+|\d{4})', text, re.IGNORECASE)
        if timeframe_match:
            return timeframe_match.group(0)
        return 'Not specified'
    
    def _extract_guidance_confidence(self, text: str) -> str:
        """Extract confidence level for guidance"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['confident', 'certain', 'definitive']):
            return 'high'
        elif any(word in text_lower for word in ['expect', 'believe', 'anticipate']):
            return 'medium'
        elif any(word in text_lower for word in ['may', 'could', 'potential', 'possible']):
            return 'low'
        else:
            return 'medium'
    
    async def _generate_trend_analysis(self, company_id: int) -> Optional[TrendAnalysis]:
        """Generate trend analysis comparing with historical data"""
        try:
            # Get the company's transcripts ordered by date
            transcripts = Transcript.query.filter_by(company_id=company_id)\
                .join(SentimentAnalysis)\
                .order_by(Transcript.fiscal_year.desc(), Transcript.fiscal_quarter.desc())\
                .limit(4).all()
            
            if len(transcripts) < 2:
                return None  # Need at least 2 transcripts for comparison
            
            latest = transcripts[0]
            previous = transcripts[1]
            
            # Calculate changes
            sentiment_change = latest.sentiment_analysis.overall_sentiment - previous.sentiment_analysis.overall_sentiment
            confidence_change = latest.sentiment_analysis.management_confidence_score - previous.sentiment_analysis.management_confidence_score
            
            # Determine trend category
            if sentiment_change > 0.15:
                trend_category = 'improving'
            elif sentiment_change < -0.15:
                trend_category = 'declining'
            else:
                trend_category = 'stable'
            
            # Create trend analysis
            trend = TrendAnalysis(
                company_id=company_id,
                analysis_date=date.today(),
                trend_category=trend_category,
                sentiment_change=sentiment_change,
                confidence_change=confidence_change,
                key_changes=[{
                    'type': 'sentiment_shift',
                    'description': f'Sentiment {"improved" if sentiment_change > 0 else "declined"} by {abs(sentiment_change):.2f} points',
                    'impact': 'positive' if sentiment_change > 0 else 'negative'
                }],
                notable_quotes=getattr(latest.sentiment_analysis, 'key_quotes', [])[:3]
            )
            
            db.session.add(trend)
            db.session.commit()
            
            return trend
            
        except Exception as e:
            logger.error(f"Error generating trend analysis: {str(e)}")
            return None
    
    async def _check_for_alerts(self, processed_data: Dict[str, Any]) -> List[Alert]:
        """Check for conditions that warrant alerts"""
        alerts = []
        
        try:
            sentiment = processed_data['sentiment_analysis']
            company_id = processed_data['company_id']
            
            # Check for significant sentiment changes
            if abs(sentiment.overall_sentiment) > 0.3:
                severity = 'high' if abs(sentiment.overall_sentiment) > 0.5 else 'medium'
                direction = 'positive' if sentiment.overall_sentiment > 0 else 'negative'
                
                alert = Alert(
                    company_id=company_id,
                    alert_type='significant_sentiment_change',
                    severity=severity,
                    message=f'Significant {direction} sentiment detected (score: {sentiment.overall_sentiment:.2f})',
                    data={
                        'sentiment_score': sentiment.overall_sentiment,
                        'confidence_score': sentiment.management_confidence_score,
                        'key_quotes': processed_data.get('quotes', [])[:2]
                    }
                )
                
                db.session.add(alert)
                alerts.append(alert)
            
            # Check for guidance-related alerts
            guidance = processed_data.get('guidance', [])
            if guidance:
                alert = Alert(
                    company_id=company_id,
                    alert_type='guidance_update',
                    severity='medium',
                    message=f'New guidance provided: {len(guidance)} items',
                    data={
                        'guidance_items': [g.__dict__ for g in guidance],
                        'guidance_count': len(guidance)
                    }
                )
                
                db.session.add(alert)
                alerts.append(alert)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error checking for alerts: {str(e)}")
        
        return alerts
    
    async def _generate_collection_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for the collection run"""
        try:
            # Get counts
            total_companies = Company.query.count()
            total_transcripts = Transcript.query.count()
            total_trends = TrendAnalysis.query.count()
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_transcripts = Transcript.query.filter(Transcript.created_at >= yesterday).count()
            recent_trends = TrendAnalysis.query.filter(TrendAnalysis.created_at >= yesterday).count()
            
            # Get trend distribution
            trend_summary = TrendAnalysis.get_summary_stats()
            
            return {
                'total_companies': total_companies,
                'total_transcripts': total_transcripts,
                'total_trends': total_trends,
                'recent_transcripts': recent_transcripts,
                'recent_trends': recent_trends,
                'trend_distribution': trend_summary,
                'collection_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {}


# Async helper functions
async def run_q1_2025_collection():
    """Main entry point for Q1 2025 data collection"""
    collector = RealDataCollector()
    return await collector.collect_q1_2025_data()


# Sync wrapper for compatibility
def collect_q1_2025_data_sync():
    """Synchronous wrapper for Q1 2025 data collection"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_q1_2025_collection())
    finally:
        loop.close() 