"""Transcript processing service"""
import re
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessedTranscript:
    """Container for processed transcript data"""
    date: datetime
    symbol: str
    year: int
    quarter: int
    cleaned_text: str
    sections: Dict[str, str]
    word_count: int
    confidence_indicators: Dict[str, Any]
    product_mentions: List[Dict[str, Any]]
    guidance_statements: List[str]
    key_metrics: Dict[str, Any]


class TranscriptProcessor:
    """Service for processing earnings call transcripts"""
    
    def __init__(self):
        # Confidence indicator patterns
        self.confidence_patterns = {
            'positive': [
                r'strong\s+momentum',
                r'ahead\s+of\s+schedule',
                r'exceed(?:ing|ed)?\s+expectations',
                r'confident\s+in\s+our\s+ability',
                r'on\s+track\s+to',
                r'well[\s-]positioned',
                r'significant\s+progress',
                r'pleased\s+with',
                r'outperform(?:ing|ed)?',
                r'accelerat(?:ing|ed)\s+growth',
                r'strong\s+pipeline',
                r'robust\s+demand',
                r'positive\s+momentum',
                r'breakthrough',
                r'milestone\s+achievement'
            ],
            'negative': [
                r'challenging\s+environment',
                r'below\s+expectations',
                r'uncertain(?:ty)?',
                r'delay(?:ed|s)?',
                r'setback',
                r'concerns?\s+about',
                r'difficult\s+quarter',
                r'headwinds?',
                r'disappointing',
                r'slower\s+than\s+expected',
                r'competitive\s+pressure',
                r'supply\s+chain\s+issues',
                r'regulatory\s+challenges',
                r'clinical\s+trial\s+failure',
                r'discontinued?\s+(?:study|program)'
            ],
            'neutral': [
                r'in\s+line\s+with',
                r'as\s+expected',
                r'maintain(?:ing|ed)?',
                r'continues?\s+to',
                r'steady',
                r'consistent\s+with',
                r'on\s+plan',
                r'unchanged'
            ]
        }
        
        # Product/drug name patterns for biotech
        self.product_patterns = [
            # Drug codes (e.g., ABC-123, XYZ-4567)
            r'(?<![A-Z0-9])([A-Z]{2,4}[-\s]?\d{3,4}[A-Z]?)(?![A-Z0-9])',
            # Clinical programs
            r'our\s+([A-Z][\w-]+)\s+(?:product|drug|therapy|treatment|candidate|program)',
            # Phase mentions
            r'Phase\s+(?:I{1,3}|[1-3][ab]?)\s+(?:trial|study|data|results)\s+(?:of|for)\s+([A-Z][\w-]+)',
            # Brand names in quotes
            r'["\']([A-Z][\w-]+)["\']?\s+(?:product|drug|therapy)',
            # FDA submissions
            r'(?:NDA|BLA|IND|510\(k\))\s+for\s+([A-Z][\w-]+)'
        ]
        
        # Guidance patterns
        self.guidance_patterns = [
            r'(?:expect|anticipate|project|forecast|guide).*?(?:\$[\d,]+\s*(?:million|billion))',
            r'(?:revenue|earnings)\s+(?:guidance|outlook).*?(?:\d+%|\$[\d,]+)',
            r'(?:full[\s-]year|annual|FY\s*\d{4}).*?(?:expect|anticipate).*?(?:\d+%|\$[\d,]+)',
            r'reaffirm(?:ing|ed)?\s+(?:our\s+)?(?:\d{4}\s+)?guidance',
            r'rais(?:ing|ed)\s+(?:our\s+)?(?:\d{4}\s+)?guidance',
            r'lower(?:ing|ed)?\s+(?:our\s+)?(?:\d{4}\s+)?guidance'
        ]
    
    def process_transcript(self, transcript_data: Dict[str, Any]) -> ProcessedTranscript:
        """Process raw transcript into structured data"""
        try:
            content = transcript_data.get('content', '')
            
            # Clean the text
            cleaned_text = self.clean_text(content)
            
            # Split into sections
            sections = self.split_into_sections(cleaned_text)
            
            # Extract various components
            confidence_indicators = self.extract_confidence_indicators(cleaned_text)
            product_mentions = self.extract_product_mentions(cleaned_text)
            guidance_statements = self.extract_guidance(cleaned_text)
            key_metrics = self.extract_key_metrics(cleaned_text)
            
            # Parse date
            date_str = transcript_data.get('date', '')
            try:
                call_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                call_date = datetime.utcnow()
            
            return ProcessedTranscript(
                date=call_date,
                symbol=transcript_data.get('symbol', ''),
                year=transcript_data.get('year', call_date.year),
                quarter=transcript_data.get('quarter', (call_date.month - 1) // 3 + 1),
                cleaned_text=cleaned_text,
                sections=sections,
                word_count=len(cleaned_text.split()),
                confidence_indicators=confidence_indicators,
                product_mentions=product_mentions,
                guidance_statements=guidance_statements,
                key_metrics=key_metrics
            )
            
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
            raise
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize transcript text"""
        if not text:
            return ''
        
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Fix spacing issues
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*--\s*', ' ', text)
        
        # Normalize quotes and apostrophes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r'['']', "'", text)
        
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\$\%\(\)\'\"\/]', ' ', text)
        
        # Fix multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        # Normalize case for acronyms
        text = re.sub(r'\b([A-Z]\.){2,}', lambda m: m.group(0).replace('.', ''), text)
        
        return text.strip()
    
    def split_into_sections(self, text: str) -> Dict[str, str]:
        """Split transcript into prepared remarks and Q&A sections"""
        sections = {
            'full': text,
            'prepared_remarks': '',
            'qa_section': '',
            'ceo_remarks': '',
            'cfo_remarks': ''
        }
        
        # Find Q&A section
        qa_markers = [
            r'question[\s-]and[\s-]answer',
            r'q\s*&\s*a\s+session',
            r'we\'?ll\s+now\s+(?:take|open|begin)\s+questions?',
            r'now\s+open\s+(?:the\s+)?(?:floor|line)?\s*(?:for|to)\s+questions?',
            r'turn\s+(?:it\s+)?over\s+(?:to|for)\s+questions?',
            r'operator\s+instructions'
        ]
        
        qa_start = None
        for marker in qa_markers:
            match = re.search(marker, text, re.IGNORECASE)
            if match:
                qa_start = match.start()
                break
        
        if qa_start:
            sections['prepared_remarks'] = text[:qa_start].strip()
            sections['qa_section'] = text[qa_start:].strip()
        else:
            sections['prepared_remarks'] = text
        
        # Extract CEO remarks
        ceo_pattern = r'(?:CEO|Chief\s+Executive\s+Officer)[\s\:]+([^.]+\.(?:[^.]+\.){0,10})'
        ceo_matches = re.findall(ceo_pattern, text, re.IGNORECASE)
        if ceo_matches:
            sections['ceo_remarks'] = ' '.join(ceo_matches[:3])  # First 3 segments
        
        # Extract CFO remarks
        cfo_pattern = r'(?:CFO|Chief\s+Financial\s+Officer)[\s\:]+([^.]+\.(?:[^.]+\.){0,10})'
        cfo_matches = re.findall(cfo_pattern, text, re.IGNORECASE)
        if cfo_matches:
            sections['cfo_remarks'] = ' '.join(cfo_matches[:3])
        
        return sections
    
    def extract_confidence_indicators(self, text: str) -> Dict[str, Any]:
        """Extract and score confidence indicators"""
        indicators = {
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'phrases': [],
            'score': 0.0,
            'positive_phrases': [],
            'negative_phrases': [],
            'context_snippets': []
        }
        
        text_lower = text.lower()
        
        # Extract positive indicators with context
        for pattern in self.confidence_patterns['positive']:
            matches = list(re.finditer(pattern, text_lower))
            indicators['positive_count'] += len(matches)
            
            for match in matches[:5]:  # Limit to first 5 of each type
                phrase = match.group(0)
                indicators['positive_phrases'].append(phrase)
                
                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text_lower), match.end() + 50)
                context = text_lower[start:end]
                indicators['context_snippets'].append({
                    'type': 'positive',
                    'phrase': phrase,
                    'context': context
                })
        
        # Extract negative indicators with context
        for pattern in self.confidence_patterns['negative']:
            matches = list(re.finditer(pattern, text_lower))
            indicators['negative_count'] += len(matches)
            
            for match in matches[:5]:
                phrase = match.group(0)
                indicators['negative_phrases'].append(phrase)
                
                start = max(0, match.start() - 50)
                end = min(len(text_lower), match.end() + 50)
                context = text_lower[start:end]
                indicators['context_snippets'].append({
                    'type': 'negative',
                    'phrase': phrase,
                    'context': context
                })
        
        # Count neutral indicators
        for pattern in self.confidence_patterns['neutral']:
            matches = re.findall(pattern, text_lower)
            indicators['neutral_count'] += len(matches)
        
        # Calculate confidence score (-1 to 1)
        total = indicators['positive_count'] + indicators['negative_count'] + indicators['neutral_count']
        if total > 0:
            positive_weight = indicators['positive_count'] / total
            negative_weight = indicators['negative_count'] / total
            indicators['score'] = positive_weight - negative_weight
        
        return indicators
    
    def extract_product_mentions(self, text: str) -> List[Dict[str, Any]]:
        """Extract product/drug mentions for biotech companies"""
        products = {}
        
        for pattern in self.product_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                product_name = match.group(1) if match.lastindex else match.group(0)
                product_name = product_name.strip()
                
                # Skip common false positives
                if len(product_name) < 3 or product_name.lower() in ['the', 'our', 'this', 'that']:
                    continue
                
                # Normalize product name
                product_key = product_name.upper()
                
                if product_key not in products:
                    products[product_key] = {
                        'name': product_name,
                        'mentions': 0,
                        'contexts': []
                    }
                
                products[product_key]['mentions'] += 1
                
                # Get context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].strip()
                
                if len(products[product_key]['contexts']) < 3:
                    products[product_key]['contexts'].append(context)
        
        # Convert to list and sort by mentions
        product_list = list(products.values())
        product_list.sort(key=lambda x: x['mentions'], reverse=True)
        
        return product_list[:10]  # Return top 10 products
    
    def extract_guidance(self, text: str) -> List[str]:
        """Extract forward-looking guidance statements"""
        guidance = []
        
        for pattern in self.guidance_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Get the full sentence
                start = text.rfind('.', 0, match.start()) + 1
                end = text.find('.', match.end())
                if end == -1:
                    end = len(text)
                
                statement = text[start:end].strip()
                
                # Avoid duplicates
                if statement and statement not in guidance and len(statement) < 500:
                    guidance.append(statement)
        
        return guidance[:10]  # Return top 10 guidance statements
    
    def extract_key_metrics(self, text: str) -> Dict[str, Any]:
        """Extract key financial and operational metrics"""
        metrics = {
            'revenue_mentions': [],
            'earnings_mentions': [],
            'clinical_updates': [],
            'percentage_changes': [],
            'dollar_amounts': []
        }
        
        # Revenue mentions
        revenue_pattern = r'revenue.*?(?:\$[\d,]+\s*(?:million|billion)|[\d\.]+%)'
        revenue_matches = re.findall(revenue_pattern, text, re.IGNORECASE)
        metrics['revenue_mentions'] = revenue_matches[:5]
        
        # Clinical trial updates
        clinical_pattern = r'(?:Phase\s+(?:I{1,3}|[1-3][ab]?)|clinical\s+trial|study).*?(?:complet|enroll|result|data|success|fail)'
        clinical_matches = re.findall(clinical_pattern, text, re.IGNORECASE)
        metrics['clinical_updates'] = [match[:200] for match in clinical_matches[:5]]
        
        # Percentage changes
        percent_pattern = r'(?:increase|decrease|growth|decline|up|down).*?([\d\.]+)%'
        percent_matches = re.findall(percent_pattern, text, re.IGNORECASE)
        metrics['percentage_changes'] = percent_matches[:10]
        
        # Dollar amounts
        dollar_pattern = r'\$[\d,]+(?:\.\d+)?\s*(?:million|billion|thousand)?'
        dollar_matches = re.findall(dollar_pattern, text)
        metrics['dollar_amounts'] = dollar_matches[:10]
        
        return metrics 