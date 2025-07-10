"""Sentiment Analysis Service"""
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import openai

from config.config import Config
from .transcript_processor import ProcessedTranscript

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Service for analyzing sentiment in earnings call transcripts"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Initialize FinBERT
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
            self.model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
            self.finbert = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("FinBERT initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FinBERT: {str(e)}")
            self.finbert = None
        
        # Initialize OpenAI if API key is available
        self.use_gpt = False
        if self.config.OPENAI_API_KEY and self.config.USE_GPT_ENHANCEMENT:
            try:
                openai.api_key = self.config.OPENAI_API_KEY
                self.use_gpt = True
                logger.info("OpenAI GPT enhancement enabled")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI: {str(e)}")
        
        # Biotech/Medtech specific terms for enhanced analysis
        self.biotech_positive_terms = [
            'breakthrough', 'positive results', 'exceeded expectations', 'ahead of schedule',
            'fda approval', 'fast track', 'met primary endpoint', 'statistically significant',
            'strong enrollment', 'positive safety profile', 'favorable outcomes',
            'accelerated approval', 'promising data', 'successful trial', 'robust pipeline',
            'commercial launch', 'market expansion', 'revenue growth', 'patent granted',
            'strategic partnership', 'licensing agreement', 'milestone achieved'
        ]
        
        self.biotech_negative_terms = [
            'failed trial', 'missed endpoint', 'delayed enrollment', 'safety concerns',
            'regulatory setback', 'clinical hold', 'discontinued', 'below expectations',
            'adverse events', 'fda rejection', 'trial halted', 'funding challenges',
            'pipeline setback', 'competitive pressure', 'patent expiration', 'layoffs',
            'restructuring', 'cash burn', 'going concern', 'material weakness'
        ]
        
        self.guidance_keywords = [
            'guidance', 'outlook', 'expect', 'anticipate', 'project', 'forecast',
            'target', 'goal', 'milestone', 'timeline', 'enrollment target',
            'revenue projection', 'cash runway', 'burn rate', 'operating expenses'
        ]
    
    def analyze_transcript(self, processed_transcript: ProcessedTranscript) -> Dict[str, Any]:
        """Perform comprehensive sentiment analysis on processed transcript"""
        try:
            # Analyze overall sentiment
            overall_sentiment = self._analyze_text_sentiment(processed_transcript.cleaned_text)
            
            # Add biotech-specific sentiment adjustment
            biotech_adjustment = self._calculate_biotech_sentiment_adjustment(
                processed_transcript.cleaned_text
            )
            
            # Adjust overall sentiment based on biotech-specific terms
            adjusted_sentiment = overall_sentiment['score'] + biotech_adjustment
            adjusted_sentiment = max(-1.0, min(1.0, adjusted_sentiment))  # Clamp to [-1, 1]
            
            # Analyze by section
            section_sentiments = {}
            for section_name, section_text in processed_transcript.sections.items():
                if section_text and section_name != 'full':
                    section_sentiments[section_name] = self._analyze_text_sentiment(section_text)
            
            # Use confidence indicators from processing
            confidence_score = processed_transcript.confidence_indicators['score']
            
            # Analyze guidance sentiment with biotech context
            guidance_sentiment = self._analyze_guidance_sentiment(
                processed_transcript.guidance_statements
            )
            
            # Extract guidance changes
            guidance_changes = self._extract_guidance_changes(
                processed_transcript.guidance_statements
            )
            
            # Extract key topics
            key_topics = self._extract_key_topics(processed_transcript)
            
            # Extract biotech-specific insights
            biotech_insights = self._extract_biotech_insights(processed_transcript)
            
            # Compile analysis results
            analysis = {
                'overall_sentiment': adjusted_sentiment,
                'sentiment_label': self._score_to_label(adjusted_sentiment),
                'raw_sentiment': overall_sentiment['score'],
                'biotech_adjustment': biotech_adjustment,
                'sentiment_by_section': section_sentiments,
                'management_confidence_score': confidence_score,
                'guidance_sentiment': guidance_sentiment,
                'guidance_changes': guidance_changes,
                'confidence_indicators': processed_transcript.confidence_indicators,
                'product_mentions': processed_transcript.product_mentions,
                'key_topics': key_topics,
                'biotech_insights': biotech_insights,
                'key_metrics': processed_transcript.key_metrics,
                'analysis_metadata': {
                    'word_count': processed_transcript.word_count,
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            }
            
            # Optional GPT enhancement for edge cases
            if self.use_gpt and self._should_use_gpt_enhancement(analysis):
                gpt_insights = self._get_gpt_insights(
                    processed_transcript.cleaned_text[:4000],  # Limit text length
                    analysis
                )
                if gpt_insights:
                    analysis['gpt_enhanced'] = True
                    analysis['gpt_insights'] = gpt_insights
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            raise
    
    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using FinBERT"""
        if not text or not self.finbert:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
        
        # Split text into chunks (FinBERT has token limits)
        chunks = self._split_text_into_chunks(text, max_length=500)
        
        sentiments = []
        confidences = []
        
        for chunk in chunks:
            try:
                results = self.finbert(chunk)
                if results:
                    result = results[0]
                    
                    # Convert to numeric score
                    score = result['score']
                    if result['label'] == 'negative':
                        score = -score
                    elif result['label'] == 'neutral':
                        score = 0
                    
                    sentiments.append(score)
                    confidences.append(result['score'])
            except Exception as e:
                logger.warning(f"Error analyzing chunk: {str(e)}")
                continue
        
        if not sentiments:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
        
        # Calculate weighted average based on confidence
        weights = np.array(confidences)
        scores = np.array(sentiments)
        avg_sentiment = np.average(scores, weights=weights)
        avg_confidence = np.mean(confidences)
        
        return {
            'score': float(avg_sentiment),
            'label': self._score_to_label(avg_sentiment),
            'confidence': float(avg_confidence)
        }
    
    def _analyze_guidance_sentiment(self, guidance_statements: List[str]) -> float:
        """Analyze sentiment of guidance statements"""
        if not guidance_statements:
            return 0.0
        
        sentiments = []
        for statement in guidance_statements:
            result = self._analyze_text_sentiment(statement)
            sentiments.append(result['score'])
        
        return float(np.mean(sentiments)) if sentiments else 0.0
    
    def _extract_key_topics(self, processed_transcript: ProcessedTranscript) -> Dict[str, Any]:
        """Extract key topics from the transcript"""
        topics = {
            'clinical_trials': [],
            'financial_performance': [],
            'regulatory': [],
            'competitive_landscape': [],
            'partnerships': []
        }
        
        text_lower = processed_transcript.cleaned_text.lower()
        
        # Clinical trials
        if 'phase' in text_lower or 'trial' in text_lower or 'study' in text_lower:
            topics['clinical_trials'] = self._extract_topic_mentions(
                text_lower,
                ['phase', 'trial', 'study', 'enrollment', 'data', 'results']
            )
        
        # Financial performance
        if 'revenue' in text_lower or 'earnings' in text_lower:
            topics['financial_performance'] = self._extract_topic_mentions(
                text_lower,
                ['revenue', 'earnings', 'margin', 'growth', 'expenses', 'cash']
            )
        
        # Regulatory
        if 'fda' in text_lower or 'regulatory' in text_lower:
            topics['regulatory'] = self._extract_topic_mentions(
                text_lower,
                ['fda', 'regulatory', 'approval', 'submission', 'clearance']
            )
        
        # Competitive landscape
        if 'competit' in text_lower or 'market' in text_lower:
            topics['competitive_landscape'] = self._extract_topic_mentions(
                text_lower,
                ['competitive', 'market', 'competitor', 'differentiate']
            )
        
        # Partnerships
        if 'partner' in text_lower or 'collaborat' in text_lower:
            topics['partnerships'] = self._extract_topic_mentions(
                text_lower,
                ['partnership', 'collaboration', 'alliance', 'agreement']
            )
        
        # Filter out empty topics
        return {k: v for k, v in topics.items() if v}
    
    def _extract_topic_mentions(self, text: str, keywords: List[str]) -> List[str]:
        """Extract sentences mentioning specific keywords"""
        sentences = text.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                # Clean and add sentence
                clean_sentence = sentence.strip()
                if 20 < len(clean_sentence) < 300:  # Reasonable sentence length
                    relevant_sentences.append(clean_sentence)
        
        return relevant_sentences[:5]  # Return top 5 sentences
    
    def _should_use_gpt_enhancement(self, analysis: Dict[str, Any]) -> bool:
        """Determine if GPT enhancement would be valuable"""
        confidence = analysis['management_confidence_score']
        sentiment = analysis['overall_sentiment']
        
        # Use GPT for edge cases or conflicting signals
        if (confidence > 0.3 and sentiment < -0.1) or \
           (confidence < -0.3 and sentiment > 0.1):
            return True
        
        # Use for extreme values
        if abs(confidence) > 0.5 or abs(sentiment) > 0.5:
            return True
        
        # Use if sentiment sections vary significantly
        if 'sentiment_by_section' in analysis:
            section_scores = [s['score'] for s in analysis['sentiment_by_section'].values()]
            if section_scores and (max(section_scores) - min(section_scores)) > 0.5:
                return True
        
        return False
    
    def _get_gpt_insights(self, text: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get enhanced insights using GPT-4"""
        if not self.use_gpt:
            return None
        
        try:
            prompt = f"""
            As a financial analyst, analyze this earnings call transcript excerpt and provide insights on:
            
            1. Key tone shifts or unusual language compared to typical earnings calls
            2. Specific phrases indicating management confidence or concern
            3. Notable product/strategy updates for this biotech/medtech company
            4. Any discrepancies between stated optimism and underlying concerns
            
            Current analysis shows:
            - Overall sentiment: {analysis['overall_sentiment']:.2f} ({analysis['sentiment_label']})
            - Management confidence: {analysis['management_confidence_score']:.2f}
            - Key products mentioned: {len(analysis.get('product_mentions', []))}
            
            Transcript excerpt:
            {text}
            
            Provide a brief, structured analysis (max 300 words) focusing on actionable insights.
            Format as JSON with keys: tone_shifts, confidence_indicators, product_updates, concerns
            """
            
            response = openai.ChatCompletion.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in biotech/medtech earnings calls."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            insights_text = response.choices[0].message['content']
            
            # Try to parse as JSON, fallback to text
            try:
                import json
                insights = json.loads(insights_text)
            except:
                insights = {'analysis': insights_text}
            
            return {
                'insights': insights,
                'model': self.config.OPENAI_MODEL,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"GPT enhancement failed: {str(e)}")
            return None
    
    def _split_text_into_chunks(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into chunks for processing"""
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(' '.join(current_chunk)) > max_length:
                if len(current_chunk) > 1:
                    # Remove last word and create chunk
                    current_chunk.pop()
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                else:
                    # Single word exceeds max length
                    chunks.append(word[:max_length])
                    current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _score_to_label(self, score: float) -> str:
        """Convert numeric score to label"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_biotech_sentiment_adjustment(self, text: str) -> float:
        """Calculate sentiment adjustment based on biotech-specific terms"""
        text_lower = text.lower()
        positive_count = 0
        negative_count = 0
        
        # Count positive terms
        for term in self.biotech_positive_terms:
            positive_count += text_lower.count(term.lower())
        
        # Count negative terms
        for term in self.biotech_negative_terms:
            negative_count += text_lower.count(term.lower())
        
        # Calculate adjustment (limit to ±0.3 to avoid overwhelming base sentiment)
        net_count = positive_count - negative_count
        adjustment = net_count * 0.02  # Each term contributes 0.02
        adjustment = max(-0.3, min(0.3, adjustment))
        
        return adjustment
    
    def _extract_guidance_changes(self, guidance_statements: List[str]) -> Dict[str, Any]:
        """Extract specific guidance changes from statements"""
        changes = {
            'revenue_guidance': None,
            'timeline_updates': [],
            'enrollment_targets': [],
            'milestone_updates': [],
            'financial_outlook': None
        }
        
        for statement in guidance_statements:
            statement_lower = statement.lower()
            
            # Revenue guidance
            if any(word in statement_lower for word in ['revenue', 'sales', 'income']):
                if 'increase' in statement_lower or 'raise' in statement_lower:
                    changes['revenue_guidance'] = 'raised'
                elif 'decrease' in statement_lower or 'lower' in statement_lower:
                    changes['revenue_guidance'] = 'lowered'
                elif 'maintain' in statement_lower or 'reaffirm' in statement_lower:
                    changes['revenue_guidance'] = 'maintained'
            
            # Timeline updates
            if 'timeline' in statement_lower or 'schedule' in statement_lower:
                changes['timeline_updates'].append(statement)
            
            # Enrollment targets
            if 'enrollment' in statement_lower:
                changes['enrollment_targets'].append(statement)
            
            # Milestone updates
            if 'milestone' in statement_lower:
                changes['milestone_updates'].append(statement)
        
        return changes
    
    def _extract_biotech_insights(self, processed_transcript: ProcessedTranscript) -> Dict[str, Any]:
        """Extract biotech-specific insights from the transcript"""
        insights = {
            'clinical_trial_status': [],
            'regulatory_updates': [],
            'pipeline_developments': [],
            'competitive_positioning': [],
            'funding_status': None
        }
        
        text_lower = processed_transcript.cleaned_text.lower()
        sentences = processed_transcript.cleaned_text.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            
            # Clinical trial status
            if any(term in sentence_lower for term in ['phase', 'trial', 'study', 'endpoint']):
                if any(term in sentence_lower for term in ['complete', 'met', 'positive', 'successful']):
                    insights['clinical_trial_status'].append({
                        'status': 'positive',
                        'text': sentence.strip()
                    })
                elif any(term in sentence_lower for term in ['fail', 'miss', 'delay', 'halt']):
                    insights['clinical_trial_status'].append({
                        'status': 'negative',
                        'text': sentence.strip()
                    })
            
            # Regulatory updates
            if any(term in sentence_lower for term in ['fda', 'regulatory', 'approval', 'clearance']):
                insights['regulatory_updates'].append(sentence.strip())
            
            # Pipeline developments
            if any(term in sentence_lower for term in ['pipeline', 'candidate', 'development', 'discovery']):
                insights['pipeline_developments'].append(sentence.strip())
            
            # Funding status
            if any(term in sentence_lower for term in ['cash runway', 'funding', 'capital', 'burn rate']):
                if 'sufficient' in sentence_lower or 'strong' in sentence_lower:
                    insights['funding_status'] = 'strong'
                elif 'concern' in sentence_lower or 'need' in sentence_lower:
                    insights['funding_status'] = 'concerning'
        
        # Limit insights to most relevant
        for key in ['clinical_trial_status', 'regulatory_updates', 'pipeline_developments']:
            if key in insights and len(insights[key]) > 3:
                insights[key] = insights[key][:3]
        
        return insights
    
    def compare_sentiments(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current sentiment with previous analysis"""
        comparison = {
            'sentiment_change': current['overall_sentiment'] - previous['overall_sentiment'],
            'confidence_change': current['management_confidence_score'] - previous['management_confidence_score'],
            'guidance_change': current.get('guidance_sentiment', 0) - previous.get('guidance_sentiment', 0),
            'direction': 'improving' if current['overall_sentiment'] > previous['overall_sentiment'] else 'declining'
        }
        
        # Check for significant changes
        threshold = 0.2
        comparison['is_significant'] = (
            abs(comparison['sentiment_change']) > threshold or
            abs(comparison['confidence_change']) > threshold
        )
        
        return comparison 