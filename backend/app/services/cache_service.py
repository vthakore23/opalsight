"""Caching Service for Performance Optimization"""
import json
import logging
import redis
from typing import Any, Optional, Union, List
from datetime import datetime, timedelta
from functools import wraps

from config.config import Config

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching frequently accessed data"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.enabled = False
        
        try:
            self.redis_client = redis.Redis(
                host="redis", port=6379, db=0,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("Cache service initialized successfully")
        except Exception as e:
            logger.warning(f"Cache service disabled: {str(e)}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds"""
        if not self.enabled:
            return False
        
        try:
            json_value = json.dumps(value)
            return self.redis_client.setex(key, ttl, json_value)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error: {str(e)}")
            return 0
    
    def get_or_set(self, key: str, func, ttl: int = 300) -> Any:
        """Get from cache or compute and cache result"""
        # Try to get from cache
        cached_value = self.get(key)
        if cached_value is not None:
            logger.debug(f"Cache hit: {key}")
            return cached_value
        
        # Compute value
        logger.debug(f"Cache miss: {key}")
        value = func()
        
        # Cache the result
        self.set(key, value, ttl)
        
        return value
    
    # Cache key generators
    @staticmethod
    def company_key(ticker: str) -> str:
        """Generate cache key for company data"""
        return f"company:{ticker}"
    
    @staticmethod
    def company_list_key(page: int = 1, per_page: int = 20, **filters) -> str:
        """Generate cache key for company list"""
        filter_str = '_'.join(f"{k}={v}" for k, v in sorted(filters.items()) if v)
        return f"companies:page={page}:per_page={per_page}:{filter_str}"
    
    @staticmethod
    def sentiment_timeline_key(ticker: str) -> str:
        """Generate cache key for sentiment timeline"""
        return f"timeline:{ticker}"
    
    @staticmethod
    def dashboard_key() -> str:
        """Generate cache key for dashboard data"""
        return "dashboard:main"
    
    @staticmethod
    def market_overview_key() -> str:
        """Generate cache key for market overview"""
        return "market:overview"
    
    @staticmethod
    def report_key(report_id: int) -> str:
        """Generate cache key for report"""
        return f"report:{report_id}"
    
    # Cache invalidation methods
    def invalidate_company(self, ticker: str):
        """Invalidate all cache entries for a company"""
        patterns = [
            f"company:{ticker}",
            f"timeline:{ticker}",
            f"companies:*",  # List views might include this company
            "dashboard:*",   # Dashboard might show this company
            "market:*"       # Market overview includes this company
        ]
        
        for pattern in patterns:
            self.delete_pattern(pattern)
    
    def invalidate_dashboard(self):
        """Invalidate dashboard cache"""
        self.delete_pattern("dashboard:*")
        self.delete_pattern("market:*")
    
    def invalidate_all(self):
        """Clear all cache entries"""
        if not self.enabled:
            return
        
        try:
            self.redis_client.flushdb()
            logger.info("All cache entries cleared")
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")
    
    # Performance metrics
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            return {
                "enabled": True,
                "used_memory_mb": round(info.get("used_memory", 0) / (1024 * 1024), 2),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100, 
                    2
                ),
                "evicted_keys": info.get("evicted_keys", 0),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {"enabled": True, "error": str(e)}


def cache_result(ttl: int = 300, key_prefix: str = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_service = CacheService()
            
            if key_prefix:
                cache_key = f"{key_prefix}:{func.__name__}"
            else:
                cache_key = f"func:{func.__name__}"
            
            # Add args and kwargs to key
            if args:
                cache_key += f":args={str(args)}"
            if kwargs:
                cache_key += f":kwargs={str(sorted(kwargs.items()))}"
            
            # Use cache service
            return cache_service.get_or_set(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl
            )
        
        return wrapper
    return decorator


# Singleton instance
_cache_service = None

def get_cache_service() -> CacheService:
    """Get singleton cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service 