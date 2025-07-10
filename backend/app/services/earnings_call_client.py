"""Earnings Call API Client"""
import logging
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config.config import Config

logger = logging.getLogger(__name__)


class EarningsCallError(Exception):
    """Base exception for Earnings Call API errors"""
    pass


class EarningsCallRateLimitError(EarningsCallError):
    """Rate limit exceeded error"""
    pass


class EarningsCallClient:
    """Client for Earnings Call API"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Config] = None):
        """Initialize Earnings Call client"""
        self.config = config or Config()
        self.api_key = api_key or self.config.EARNINGS_CALL_API_KEY
        self.base_url = "https://v2.api.earningscall.biz"  # Updated to v2 API
        self.rate_limit_delay = 0.5  # 500ms between calls
        self.timeout = 30
        
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
        
        # Set headers (v2 API uses apikey as query param, not Authorization header)
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Track API usage
        self._last_request_time = 0
        self._request_count = 0
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make API request with rate limiting and error handling"""
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params (v2 API requires it as query parameter)
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = self.session.post(url, json=data, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Track successful request
            self._track_api_usage(endpoint, True)
            
            # Check for rate limit
            if response.status_code == 429:
                raise EarningsCallRateLimitError("Rate limit exceeded")
            
            # Check for other errors
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Check for API errors in response
            if isinstance(data, dict) and 'error' in data:
                raise EarningsCallError(f"API Error: {data['error']}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {endpoint}")
            self._track_api_usage(endpoint, False)
            raise EarningsCallError(f"Request timeout after {self.timeout} seconds")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {endpoint}: {str(e)}")
            self._track_api_usage(endpoint, False)
            raise EarningsCallError(f"Request failed: {str(e)}")
            
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
        logger.info(
            f"API call to {endpoint}: {'success' if success else 'failed'} "
            f"(Total calls: {self._request_count})"
        )
    
    # Transcript Methods
    
    def get_transcript(
        self, 
        ticker: str, 
        year: int, 
        quarter: int,
        exchange: str = 'nasdaq'  # Most biotech companies are on NASDAQ
    ) -> Optional[Dict[str, Any]]:
        """Fetch specific earnings transcript"""
        endpoint = "transcript"
        params = {
            'exchange': exchange.lower(),
            'symbol': ticker.upper(),
            'year': year,
            'quarter': quarter
        }
        
        try:
            result = self._make_request(endpoint, params=params)
            if result:
                # Standardize the response format
                return {
                    'symbol': ticker,
                    'year': year,
                    'quarter': quarter,
                    'date': result.get('date'),
                    'content': result.get('transcript', ''),
                    'participants': result.get('participants', []),
                    'qa_session': result.get('qa_session', [])
                }
            return None
        except EarningsCallError as e:
            logger.error(f"Failed to fetch transcript for {ticker} {year}Q{quarter}: {e}")
            return None
    
    def get_available_transcripts(self, ticker: str) -> List[Dict[str, Any]]:
        """Get list of available transcripts for a ticker"""
        endpoint = f"transcripts/{ticker}"
        
        try:
            result = self._make_request(endpoint)
            if result and isinstance(result, list):
                return result
            return []
        except EarningsCallError as e:
            logger.error(f"Failed to fetch transcript list for {ticker}: {e}")
            return []
    
    def get_recent_transcripts(
        self, 
        days_back: int = 30,
        exchange: str = 'nasdaq'
    ) -> List[Dict[str, Any]]:
        """Get transcripts released in the last N days"""
        endpoint = "events"
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'exchange': exchange.lower(),
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d')
        }
        
        try:
            result = self._make_request(endpoint, params=params)
            if result and isinstance(result, list):
                # Filter for events that have transcripts
                transcripts = []
                for event in result:
                    if event.get('hasTranscript', False):
                        transcripts.append({
                            'ticker': event.get('symbol', ''),
                            'year': event.get('year'),
                            'quarter': event.get('quarter'),
                            'date': event.get('date'),
                            'exchange': event.get('exchange', 'nasdaq')
                        })
                return transcripts
            return []
        except EarningsCallError as e:
            logger.error(f"Failed to fetch recent transcripts: {e}")
            return []
    
    def get_companies_list(
        self,
        sector: Optional[str] = None,
        min_market_cap: Optional[float] = None,
        exchange: str = 'nasdaq'
    ) -> List[Dict[str, Any]]:
        """Get list of companies with available transcripts"""
        endpoint = "symbols"
        params = {
            'exchange': exchange.lower()
        }
        
        try:
            result = self._make_request(endpoint, params=params)
            if result and isinstance(result, list):
                # Filter for biotech/medtech companies
                biotech_keywords = [
                    'biotech', 'biotechnology', 'pharmaceutical', 'pharmaceuticals',
                    'drug', 'medical device', 'diagnostic', 'therapeutics',
                    'biopharmaceutical', 'health', 'medicine', 'clinical'
                ]
                
                filtered = []
                for company in result:
                    # Check industry/sector fields
                    industry = (company.get('industry') or '').lower()
                    sector_val = (company.get('sector') or '').lower() 
                    name = (company.get('name') or '').lower()
                    
                    # Include if matches biotech keywords or if no sector filter
                    is_biotech = any(keyword in industry or keyword in sector_val or keyword in name 
                                   for keyword in biotech_keywords)
                    
                    if sector and sector.lower() in ['healthcare', 'biotechnology', 'pharmaceuticals']:
                        if is_biotech:
                            # Add market cap filter if specified
                            market_cap = company.get('marketCap', 0)
                            if not min_market_cap or market_cap >= min_market_cap:
                                filtered.append({
                                    'ticker': company.get('symbol', ''),
                                    'name': company.get('name', ''),
                                    'sector': 'Healthcare',
                                    'industry': company.get('industry', 'Biotechnology'),
                                    'exchange': exchange.upper(),
                                    'market_cap': market_cap
                                })
                    elif not sector and is_biotech:
                        # Default biotech filter when no sector specified
                        market_cap = company.get('marketCap', 0)
                        if not min_market_cap or market_cap >= min_market_cap:
                            filtered.append({
                                'ticker': company.get('symbol', ''),
                                'name': company.get('name', ''),
                                'sector': 'Healthcare', 
                                'industry': company.get('industry', 'Biotechnology'),
                                'exchange': exchange.upper(),
                                'market_cap': market_cap
                            })
                
                return filtered
            return []
        except EarningsCallError as e:
            logger.error(f"Failed to fetch companies list: {e}")
            return []
    
    def search_transcripts(
        self,
        query: str,
        tickers: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search transcripts for specific terms"""
        endpoint = "search"
        data = {
            'query': query,
            'tickers': tickers,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            result = self._make_request(endpoint, method='POST', data=data)
            if result and isinstance(result, list):
                return result
            return []
        except EarningsCallError as e:
            logger.error(f"Failed to search transcripts: {e}")
            return []
    
    def get_batch_transcripts(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get multiple transcripts in batch"""
        endpoint = "batch-transcripts"
        data = {
            'tickers': tickers,
            'start_date': start_date,
            'end_date': end_date
        }
        
        try:
            result = self._make_request(endpoint, method='POST', data=data)
            if result and isinstance(result, list):
                return result
            return []
        except EarningsCallError as e:
            logger.error(f"Failed to fetch batch transcripts: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test API connection and credentials"""
        try:
            # Try to fetch recent transcripts with small limit
            recent = self.get_recent_transcripts(days_back=7)
            return True
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False 