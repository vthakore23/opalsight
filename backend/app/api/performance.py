"""Performance Testing API Routes"""
import time
import traceback
import psutil
import redis
import asyncio
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app import db
from app.models import Company, Transcript, SentimentAnalysis
from app.services.fmp_client import FMPClient
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.data_collector import DataCollector
from config.config import Config

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

# Initialize services
config = Config()
fmp_client = FMPClient(config)
sentiment_analyzer = SentimentAnalyzer(config)

# Redis client for caching tests
try:
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=True
    )
except:
    redis_client = None


def measure_time(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        execution_time = end - start
        
        if isinstance(result, dict):
            result['execution_time_ms'] = round(execution_time * 1000, 2)
        
        return result
    return wrapper


def get_system_metrics() -> Dict[str, Any]:
    """Get current system resource usage"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2)
            },
            'process': {
                'memory_mb': round(process_memory.rss / (1024**2), 2),
                'cpu_percent': process.cpu_percent()
            }
        }
    except Exception as e:
        return {'error': str(e)}


@performance_bp.route('/status', methods=['GET'])
def performance_status():
    """Get overall performance status and metrics"""
    try:
        metrics = get_system_metrics()
        
        # Test database connection
        db_start = time.time()
        db.session.execute(text('SELECT 1'))
        db_latency = (time.time() - db_start) * 1000
        
        # Test Redis connection
        redis_latency = None
        if redis_client:
            redis_start = time.time()
            try:
                redis_client.ping()
                redis_latency = (time.time() - redis_start) * 1000
            except:
                pass
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'system_metrics': metrics,
            'service_latencies': {
                'database_ms': round(db_latency, 2),
                'redis_ms': round(redis_latency, 2) if redis_latency else None
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/test/database', methods=['POST'])
@measure_time
def test_database_performance():
    """Test database query performance"""
    test_config = request.json or {}
    num_queries = test_config.get('num_queries', 10)
    query_type = test_config.get('query_type', 'simple')
    
    results = {
        'test': 'database_performance',
        'config': test_config,
        'queries': []
    }
    
    try:
        session = db.session
        
        # Test different query types
        for i in range(num_queries):
            query_start = time.time()
            
            if query_type == 'simple':
                # Simple query
                result = session.query(Company).limit(10).all()
            elif query_type == 'complex':
                # Complex join query
                result = session.query(Company, Transcript, SentimentAnalysis)\
                    .join(Transcript)\
                    .join(SentimentAnalysis)\
                    .filter(Company.market_cap > 50000000)\
                    .limit(10).all()
            elif query_type == 'aggregate':
                # Aggregate query
                result = session.query(
                    Company.sector,
                    db.func.count(Company.id),
                    db.func.avg(Company.market_cap)
                ).group_by(Company.sector).all()
            
            query_time = (time.time() - query_start) * 1000
            results['queries'].append({
                'query_num': i + 1,
                'time_ms': round(query_time, 2)
            })
        
        # Calculate statistics
        query_times = [q['time_ms'] for q in results['queries']]
        results['statistics'] = {
            'avg_ms': round(sum(query_times) / len(query_times), 2),
            'min_ms': round(min(query_times), 2),
            'max_ms': round(max(query_times), 2),
            'total_ms': round(sum(query_times), 2)
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/test/api', methods=['POST'])
@measure_time
def test_api_performance():
    """Test FMP API performance and rate limiting"""
    test_config = request.json or {}
    num_requests = test_config.get('num_requests', 5)
    
    results = {
        'test': 'api_performance',
        'config': test_config,
        'requests': []
    }
    
    try:
        # Test API requests with rate limiting
        for i in range(num_requests):
            request_start = time.time()
            
            # Use a test endpoint that returns quickly
            response = fmp_client._make_request('/api/v3/quote/AAPL')
            
            request_time = (time.time() - request_start) * 1000
            results['requests'].append({
                'request_num': i + 1,
                'time_ms': round(request_time, 2),
                'status': 'success' if response else 'failed'
            })
        
        # Calculate statistics
        request_times = [r['time_ms'] for r in results['requests']]
        results['statistics'] = {
            'avg_ms': round(sum(request_times) / len(request_times), 2),
            'min_ms': round(min(request_times), 2),
            'max_ms': round(max(request_times), 2),
            'total_ms': round(sum(request_times), 2),
            'rate_limit_delay_ms': config.API_RATE_LIMIT_DELAY
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/test/sentiment', methods=['POST'])
@measure_time
def test_sentiment_performance():
    """Test sentiment analysis performance"""
    test_config = request.json or {}
    test_text = test_config.get('text', """
        We are pleased to report strong quarterly results with revenue growth of 25% year-over-year. 
        Our clinical trials are progressing well, and we remain confident in our pipeline. 
        However, we face some challenges in the competitive landscape that we are actively addressing.
    """)
    num_analyses = test_config.get('num_analyses', 5)
    
    results = {
        'test': 'sentiment_performance',
        'config': test_config,
        'analyses': []
    }
    
    try:
        from app.services.transcript_processor import TranscriptProcessor
        processor = TranscriptProcessor()
        
        for i in range(num_analyses):
            analysis_start = time.time()
            
            # Process transcript
            processed = processor.process_transcript(test_text, {
                'company': 'Test Company',
                'quarter': 'Q1',
                'year': 2024
            })
            
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.analyze_transcript(processed)
            
            analysis_time = (time.time() - analysis_start) * 1000
            results['analyses'].append({
                'analysis_num': i + 1,
                'time_ms': round(analysis_time, 2),
                'sentiment_score': sentiment_result['overall_sentiment'],
                'confidence_score': sentiment_result['management_confidence_score']
            })
        
        # Calculate statistics
        analysis_times = [a['time_ms'] for a in results['analyses']]
        results['statistics'] = {
            'avg_ms': round(sum(analysis_times) / len(analysis_times), 2),
            'min_ms': round(min(analysis_times), 2),
            'max_ms': round(max(analysis_times), 2),
            'total_ms': round(sum(analysis_times), 2)
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/test/cache', methods=['POST'])
@measure_time
def test_cache_performance():
    """Test Redis cache performance"""
    if not redis_client:
        return jsonify({'error': 'Redis not configured'}), 503
    
    test_config = request.json or {}
    num_operations = test_config.get('num_operations', 100)
    
    results = {
        'test': 'cache_performance',
        'config': test_config,
        'operations': {
            'set': [],
            'get': [],
            'delete': []
        }
    }
    
    try:
        # Test SET operations
        for i in range(num_operations):
            key = f'perf_test_{i}'
            value = f'test_value_{i}' * 100  # Make value larger
            
            set_start = time.time()
            redis_client.set(key, value, ex=60)  # 60 second expiry
            set_time = (time.time() - set_start) * 1000
            results['operations']['set'].append(round(set_time, 2))
        
        # Test GET operations
        for i in range(num_operations):
            key = f'perf_test_{i}'
            
            get_start = time.time()
            redis_client.get(key)
            get_time = (time.time() - get_start) * 1000
            results['operations']['get'].append(round(get_time, 2))
        
        # Test DELETE operations
        for i in range(num_operations):
            key = f'perf_test_{i}'
            
            del_start = time.time()
            redis_client.delete(key)
            del_time = (time.time() - del_start) * 1000
            results['operations']['delete'].append(round(del_time, 2))
        
        # Calculate statistics for each operation type
        for op_type in ['set', 'get', 'delete']:
            times = results['operations'][op_type]
            results[f'{op_type}_stats'] = {
                'avg_ms': round(sum(times) / len(times), 2),
                'min_ms': round(min(times), 2),
                'max_ms': round(max(times), 2)
            }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/test/concurrent', methods=['POST'])
async def test_concurrent_performance():
    """Test system performance under concurrent load"""
    test_config = request.json or {}
    num_concurrent = test_config.get('num_concurrent', 10)
    test_type = test_config.get('test_type', 'mixed')
    
    results = {
        'test': 'concurrent_performance',
        'config': test_config,
        'start_time': datetime.utcnow().isoformat()
    }
    
    try:
        # Define concurrent tasks
        async def db_task():
            start = time.time()
            companies = Company.query.limit(10).all()
            return ('db', (time.time() - start) * 1000)
        
        async def api_task():
            start = time.time()
            # Simulate API call
            await asyncio.sleep(0.1)
            return ('api', (time.time() - start) * 1000)
        
        async def cache_task():
            if not redis_client:
                return ('cache', 0)
            start = time.time()
            redis_client.set('concurrent_test', 'value')
            redis_client.get('concurrent_test')
            return ('cache', (time.time() - start) * 1000)
        
        # Create tasks based on test type
        tasks = []
        if test_type == 'mixed':
            for i in range(num_concurrent):
                tasks.extend([db_task(), api_task(), cache_task()])
        elif test_type == 'database':
            tasks = [db_task() for _ in range(num_concurrent)]
        elif test_type == 'api':
            tasks = [api_task() for _ in range(num_concurrent)]
        
        # Run tasks concurrently
        start_time = time.time()
        task_results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # Group results by type
        results['task_results'] = {}
        for task_type, duration in task_results:
            if task_type not in results['task_results']:
                results['task_results'][task_type] = []
            results['task_results'][task_type].append(round(duration, 2))
        
        # Calculate statistics
        results['statistics'] = {
            'total_tasks': len(tasks),
            'total_time_ms': round(total_time, 2),
            'avg_time_per_task_ms': round(total_time / len(tasks), 2)
        }
        
        # Per-type statistics
        for task_type, durations in results['task_results'].items():
            if durations:
                results['statistics'][f'{task_type}_avg_ms'] = round(
                    sum(durations) / len(durations), 2
                )
        
        results['end_time'] = datetime.utcnow().isoformat()
        results['system_metrics'] = get_system_metrics()
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/stress-test', methods=['POST'])
def run_stress_test():
    """Run a comprehensive stress test"""
    test_config = request.json or {}
    duration_seconds = test_config.get('duration_seconds', 30)
    
    results = {
        'test': 'stress_test',
        'config': test_config,
        'start_time': datetime.utcnow().isoformat(),
        'metrics_timeline': []
    }
    
    try:
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            iteration_start = time.time()
            
            # Collect current metrics
            metrics = get_system_metrics()
            
            # Perform various operations
            # Database operations
            companies = Company.query.limit(50).all()
            
            # Cache operations
            if redis_client:
                for i in range(10):
                    redis_client.set(f'stress_{i}', 'data' * 100)
                    redis_client.get(f'stress_{i}')
            
            # Record metrics
            results['metrics_timeline'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'elapsed_seconds': round(time.time() - start_time, 1),
                'metrics': metrics,
                'iteration_time_ms': round((time.time() - iteration_start) * 1000, 2)
            })
            
            # Sleep briefly to avoid overwhelming the system
            time.sleep(1)
        
        results['end_time'] = datetime.utcnow().isoformat()
        results['total_duration_seconds'] = round(time.time() - start_time, 2)
        
        # Clean up
        if redis_client:
            for i in range(10):
                redis_client.delete(f'stress_{i}')
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@performance_bp.route('/benchmark', methods=['GET'])
def run_benchmark():
    """Run a complete system benchmark"""
    results = {
        'benchmark_start': datetime.utcnow().isoformat(),
        'tests': {}
    }
    
    try:
        # Database benchmark
        db_test = test_database_performance()
        results['tests']['database'] = db_test.get_json()
        
        # API benchmark
        api_test = test_api_performance()
        results['tests']['api'] = api_test.get_json()
        
        # Sentiment analysis benchmark
        sentiment_test = test_sentiment_performance()
        results['tests']['sentiment'] = sentiment_test.get_json()
        
        # Cache benchmark
        if redis_client:
            cache_test = test_cache_performance()
            results['tests']['cache'] = cache_test.get_json()
        
        results['benchmark_end'] = datetime.utcnow().isoformat()
        results['system_metrics'] = get_system_metrics()
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500 