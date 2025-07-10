"""Financial Modeling Prep API Client"""
import time
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config.config import Config

logger = logging.getLogger(__name__)


class FMPError(Exception):
    """Base exception for FMP API errors"""
    pass


class FMPRateLimitError(FMPError):
    """Rate limit exceeded error"""
    pass


class FMPClient:
    """Client for Financial Modeling Prep API"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """Initialize FMP client"""
        self.config = config or Config()
        self.api_key = api_key or self.config.FMP_API_KEY
        self.base_url = self.config.FMP_BASE_URL
        self.rate_limit_delay = self.config.FMP_RATE_LIMIT_DELAY
        self.timeout = self.config.FMP_TIMEOUT
        
        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Track API usage
        self._last_request_time = 0
        self._request_count = 0
    
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        version: str = 'v3'
    ) -> Any:
        """Make API request with rate limiting and error handling"""
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        url = urljoin(self.base_url, f'{version}/{endpoint}')
        
        try:
            logger.debug(f"Making request to {url}")
            response = self.session.get(
                url, 
                params=params, 
                timeout=self.timeout
            )
            
            # Track successful request
            self._track_api_usage(endpoint, True)
            
            # Check for rate limit
            if response.status_code == 429:
                raise FMPRateLimitError("Rate limit exceeded")
            
            # Check for other errors
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Check for API errors in response
            if isinstance(data, dict) and 'Error Message' in data:
                raise FMPError(f"API Error: {data['Error Message']}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            self._track_api_usage(endpoint, False)
            raise FMPError(f"Request timeout after {self.timeout} seconds")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            self._track_api_usage(endpoint, False)
            raise FMPError(f"Request failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            self._track_api_usage(endpoint, False)
            raise
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
        self._request_count += 1
    
    def _track_api_usage(self, endpoint: str, success: bool):
        """Track API usage for monitoring"""
        # This will be implemented to save to database
        logger.info(
            f"API call to {endpoint}: {'success' if success else 'failed'} "
            f"(Total calls: {self._request_count})"
        )
    
    # Earnings Transcript Methods
    
    def get_transcript(
        self, 
        symbol: str, 
        year: int, 
        quarter: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch specific earnings transcript"""
        endpoint = f'earning_call_transcript/{symbol}'
        params = {'year': year, 'quarter': quarter}
        
        try:
            result = self._make_request(endpoint, params)
            if result and isinstance(result, list) and len(result) > 0:
                return result[0]
            return None
        except FMPError as e:
            logger.error(f"Failed to fetch transcript for {symbol} {year}Q{quarter}: {e}")
            return None
    
    def get_available_transcripts(self, symbol: str) -> List[Dict[str, Any]]:
        """Get list of available transcripts for a symbol"""
        endpoint = 'earning_call_transcript'
        params = {'symbol': symbol}
        
        try:
            return self._make_request(endpoint, params, version='v4') or []
        except FMPError as e:
            logger.error(f"Failed to fetch transcript list for {symbol}: {e}")
            return []
    
    def get_batch_transcripts(
        self, 
        symbol: str, 
        year: int
    ) -> List[Dict[str, Any]]:
        """Get all transcripts for a symbol in a specific year"""
        endpoint = f'batch_earning_call_transcript/{symbol}'
        params = {'year': year}
        
        try:
            return self._make_request(endpoint, params, version='v4') or []
        except FMPError as e:
            logger.error(f"Failed to fetch batch transcripts for {symbol} {year}: {e}")
            return []
    
    def get_transcript_symbols(self) -> List[Tuple[str, int]]:
        """Get list of all symbols with available transcripts"""
        endpoint = 'earning-call-transcript-symbols-list'
        
        try:
            result = self._make_request(endpoint)
            if result and isinstance(result, list):
                return [
                    (item.get('symbol', ''), item.get('transcriptCount', 0)) 
                    for item in result
                ]
            return []
        except FMPError as e:
            logger.error(f"Failed to fetch transcript symbols: {e}")
            return []
    
    # Company Information Methods
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile information"""
        endpoint = f'profile/{symbol}'
        
        try:
            result = self._make_request(endpoint)
            if result and isinstance(result, list) and len(result) > 0:
                return result[0]
            return {}
        except FMPError as e:
            logger.error(f"Failed to fetch company profile for {symbol}: {e}")
            return {}
    
    def get_key_metrics(
        self, 
        symbol: str, 
        period: str = 'quarter'
    ) -> List[Dict[str, Any]]:
        """Get key financial metrics"""
        endpoint = f'key-metrics/{symbol}'
        params = {'period': period}
        
        try:
            return self._make_request(endpoint, params) or []
        except FMPError as e:
            logger.error(f"Failed to fetch key metrics for {symbol}: {e}")
            return []
    
    def get_income_statement(
        self, 
        symbol: str, 
        period: str = 'quarter'
    ) -> List[Dict[str, Any]]:
        """Get income statement data"""
        endpoint = f'income-statement/{symbol}'
        params = {'period': period}
        
        try:
            return self._make_request(endpoint, params) or []
        except FMPError as e:
            logger.error(f"Failed to fetch income statement for {symbol}: {e}")
            return []
    
    # Biotech/Medtech Specific Methods
    
    def get_healthcare_companies(
        self, 
        min_market_cap: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get list of healthcare/biotech companies"""
        # FMP doesn't have a direct endpoint for this, so we'll filter from all companies
        endpoint = 'stock-screener'
        params = {
            'sector': 'Healthcare',
            'marketCapMoreThan': min_market_cap or self.config.MIN_MARKET_CAP,
            'limit': 1000
        }
        
        try:
            companies = self._make_request(endpoint, params) or []
            # Filter for biotech/medtech industries
            biotech_keywords = [
                'biotech', 'biotechnology', 'pharmaceutical', 
                'drug', 'medical device', 'diagnostic'
            ]
            
            filtered = []
            for company in companies:
                industry = (company.get('industry') or '').lower()
                if any(keyword in industry for keyword in biotech_keywords):
                    filtered.append(company)
            
            return filtered
        except FMPError as e:
            logger.error(f"Failed to fetch healthcare companies: {e}")
            return []
    
    # Batch Operations
    
    def get_recent_transcripts(
        self, 
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """Get transcripts released in the last N days"""
        # This would need to be implemented by checking each company
        # FMP doesn't have a direct endpoint for recent transcripts across all companies
        transcripts = []
        
        # Get all symbols with transcripts
        symbols = self.get_transcript_symbols()
        
        for symbol, count in symbols[:100]:  # Limit to avoid too many API calls
            if count > 0:
                # Get available transcripts for this symbol
                available = self.get_available_transcripts(symbol)
                
                # Filter by date
                for transcript_meta in available:
                    # Parse date if available
                    if 'date' in transcript_meta:
                        try:
                            transcript_date = datetime.fromisoformat(
                                transcript_meta['date'].replace('Z', '+00:00')
                            )
                            if (datetime.now() - transcript_date).days <= days_back:
                                # Fetch full transcript
                                full_transcript = self.get_transcript(
                                    symbol,
                                    transcript_meta.get('year'),
                                    transcript_meta.get('quarter')
                                )
                                if full_transcript:
                                    transcripts.append(full_transcript)
                        except (ValueError, TypeError):
                            continue
        
        return transcripts
    
    def test_connection(self) -> bool:
        """Test API connection and credentials"""
        try:
            # Try to fetch a well-known company profile
            profile = self.get_company_profile('AAPL')
            return bool(profile)
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False 