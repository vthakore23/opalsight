#!/usr/bin/env python3
"""
OpalSight - Unified Application (Working Version)
Automated Earnings Call Analysis Platform for Biotech/Medtech Companies

This single-file application combines:
- Flask backend with all API routes
- SQLite database (embedded)
- In-memory caching
- FinBERT sentiment analysis
- Performance monitoring
- Export functionality
- Frontend serving

Run with: python3 opalsight_unified.py
Access at: http://localhost:3000
"""

import os
import sys
import time
import json
import sqlite3
import threading
import logging
import io
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any

# Flask and related imports
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests

# Data processing imports
import pandas as pd
import numpy as np

# ML imports (with error handling)
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# System monitoring
import psutil

# Export functionality
try:
    import xlsxwriter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-opalsight-2025')
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Database settings (SQLite)
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'opalsight_unified.db')
    
    # API settings
    FMP_API_KEY = os.getenv('FMP_API_KEY', '9a835ed8bbff501bf036a6f843d5a6fe')


# In-memory cache implementation
class MemoryCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                # Check if expired (default 5 minutes)
                if time.time() - self._timestamps[key] < 300:
                    return self._cache[key]
                else:
                    del self._cache[key]
                    del self._timestamps[key]
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def health_check(self) -> bool:
        try:
            test_key = "health_check"
            self.set(test_key, "test", 1)
            result = self.get(test_key)
            self.delete(test_key)
            return result == "test"
        except Exception:
            return False


# Database management
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize the SQLite database with all required tables"""
        conn = self.get_connection()
        try:
            # Companies table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    sector TEXT,
                    market_cap INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Transcripts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER REFERENCES companies(id),
                    quarter TEXT,
                    year INTEGER,
                    date DATE,
                    content TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Sentiment analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sentiment_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcript_id INTEGER REFERENCES transcripts(id),
                    overall_sentiment REAL,
                    confidence_score REAL,
                    positive_segments INTEGER DEFAULT 0,
                    negative_segments INTEGER DEFAULT 0,
                    neutral_segments INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API usage table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT,
                    method TEXT,
                    ip_address TEXT,
                    response_time_ms REAL,
                    status_code INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_transcripts_company_id ON transcripts(company_id)",
                "CREATE INDEX IF NOT EXISTS idx_transcripts_date ON transcripts(date)",
                "CREATE INDEX IF NOT EXISTS idx_sentiment_transcript_id ON sentiment_analysis(transcript_id)",
                "CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            # Insert sample data
            self.insert_sample_data(conn)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def insert_sample_data(self, conn):
        """Insert sample companies data"""
        sample_companies = [
            ('MRNA', 'Moderna Inc.', 'Biotechnology', 50000000000),
            ('PFE', 'Pfizer Inc.', 'Biotechnology', 200000000000),
            ('JNJ', 'Johnson & Johnson', 'Healthcare', 400000000000),
            ('GILD', 'Gilead Sciences Inc.', 'Biotechnology', 80000000000),
            ('AMGN', 'Amgen Inc.', 'Biotechnology', 140000000000),
            ('REGN', 'Regeneron Pharmaceuticals', 'Biotechnology', 75000000000),
            ('VRTX', 'Vertex Pharmaceuticals', 'Biotechnology', 60000000000),
            ('BIIB', 'Biogen Inc.', 'Biotechnology', 35000000000)
        ]
        
        # Insert sample transcripts for demonstration
        sample_transcripts = [
            (1, 'Q4', 2024, '2024-12-15', 'Strong quarter with increased revenue from COVID-19 vaccine sales and promising pipeline developments.', 'https://example.com/mrna-q4-2024'),
            (2, 'Q4', 2024, '2024-12-10', 'Solid performance across all therapeutic areas with particular strength in oncology division.', 'https://example.com/pfe-q4-2024'),
            (3, 'Q4', 2024, '2024-12-20', 'Diversified portfolio showing resilience with pharmaceutical and medical device segments performing well.', 'https://example.com/jnj-q4-2024')
        ]
        
        for symbol, name, sector, market_cap in sample_companies:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO companies (symbol, name, sector, market_cap) VALUES (?, ?, ?, ?)",
                    (symbol, name, sector, market_cap)
                )
            except Exception as e:
                logger.warning(f"Error inserting sample company {symbol}: {e}")
        
        for company_id, quarter, year, date, content, url in sample_transcripts:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO transcripts (company_id, quarter, year, date, content, url) VALUES (?, ?, ?, ?, ?, ?)",
                    (company_id, quarter, year, date, content, url)
                )
            except Exception as e:
                logger.warning(f"Error inserting sample transcript: {e}")
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            conn = self.get_connection()
            conn.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False


# Sentiment Analysis Service
class SentimentAnalyzer:
    def __init__(self):
        self.model_name = "ProsusAI/finbert"
        self.tokenizer = None
        self.model = None
        self._lock = threading.Lock()
        self.model_loaded = False
        
        if ML_AVAILABLE:
            self.load_model()
    
    def load_model(self):
        """Load FinBERT model for financial sentiment analysis"""
        try:
            logger.info("Loading FinBERT model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model_loaded = True
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading FinBERT model: {e}")
            self.tokenizer = None
            self.model = None
            self.model_loaded = False
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of given text"""
        if not ML_AVAILABLE:
            return {
                "sentiment": 0.0, 
                "confidence": 0.0, 
                "error": "ML libraries not available",
                "scores": {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
            }
        
        if not self.model_loaded or not self.model or not self.tokenizer:
            return {
                "sentiment": 0.0, 
                "confidence": 0.0, 
                "error": "Model not loaded",
                "scores": {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
            }
        
        try:
            with self._lock:
                # Tokenize and predict
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Get sentiment scores (negative, neutral, positive)
                scores = predictions[0].detach().numpy()
                labels = ['negative', 'neutral', 'positive']
                
                # Calculate overall sentiment (-1 to 1)
                sentiment_score = scores[2] - scores[0]  # positive - negative
                confidence = float(max(scores))
                
                return {
                    "sentiment": float(sentiment_score),
                    "confidence": confidence,
                    "scores": {labels[i]: float(scores[i]) for i in range(len(labels))}
                }
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "sentiment": 0.0, 
                "confidence": 0.0, 
                "error": str(e),
                "scores": {"negative": 0.33, "neutral": 0.34, "positive": 0.33}
            }


# Performance Monitoring
class PerformanceMonitor:
    def __init__(self, db_manager: DatabaseManager, cache: MemoryCache):
        self.db_manager = db_manager
        self.cache = cache
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            process_cpu = process.cpu_percent()
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
                },
                "process": {
                    "cpu_percent": process_cpu,
                    "memory_mb": round(process_memory, 2)
                }
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def get_service_latencies(self) -> Dict[str, Optional[float]]:
        """Test service latencies"""
        latencies = {}
        
        # Database latency
        try:
            start_time = time.time()
            self.db_manager.health_check()
            latencies["database_ms"] = round((time.time() - start_time) * 1000, 2)
        except Exception:
            latencies["database_ms"] = None
        
        # Cache latency
        try:
            start_time = time.time()
            self.cache.health_check()
            latencies["cache_ms"] = round((time.time() - start_time) * 1000, 2)
        except Exception:
            latencies["cache_ms"] = None
        
        return latencies


# Export Service
class ExportService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def export_companies_csv(self) -> str:
        """Export companies data to CSV"""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT * FROM companies ORDER BY market_cap DESC")
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([description[0] for description in cursor.description])
        
        # Write data
        for row in cursor:
            writer.writerow(row)
        
        conn.close()
        return output.getvalue()
    
    def export_companies_json(self) -> str:
        """Export companies data to JSON"""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT * FROM companies ORDER BY market_cap DESC")
        
        companies = []
        for row in cursor:
            companies.append(dict(row))
        
        conn.close()
        return json.dumps(companies, indent=2, default=str)


# Main Flask Application
def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object(Config)
    CORS(app)
    
    # Initialize services
    cache = MemoryCache()
    db_manager = DatabaseManager(Config.DATABASE_PATH)
    sentiment_analyzer = SentimentAnalyzer()
    performance_monitor = PerformanceMonitor(db_manager, cache)
    export_service = ExportService(db_manager)
    
    # Middleware for API usage tracking
    @app.before_request
    def before_request():
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        try:
            if request.path.startswith('/api/'):
                response_time = (time.time() - request.start_time) * 1000
                conn = db_manager.get_connection()
                conn.execute('''
                    INSERT INTO api_usage (endpoint, method, ip_address, response_time_ms, status_code)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    request.path,
                    request.method,
                    request.remote_addr,
                    response_time,
                    response.status_code
                ))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")
        
        return response
    
    # Frontend routes
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        """Serve React app"""
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        db_healthy = db_manager.health_check()
        cache_healthy = cache.health_check()
        
        status = "healthy" if db_healthy and cache_healthy else "unhealthy"
        
        return jsonify({
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "ml_models": "available" if ML_AVAILABLE and sentiment_analyzer.model_loaded else "unavailable"
            },
            "message": "OpalSight Unified Application is running!"
        })
    
    # Companies API
    @app.route('/api/companies')
    def get_companies():
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            offset = (page - 1) * per_page
            
            # Check cache first
            cache_key = f"companies:page:{page}:per_page:{per_page}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return jsonify(cached_result)
            
            conn = db_manager.get_connection()
            
            # Get total count
            count_cursor = conn.execute("SELECT COUNT(*) FROM companies")
            total = count_cursor.fetchone()[0]
            
            # Get companies
            cursor = conn.execute(
                "SELECT * FROM companies ORDER BY market_cap DESC LIMIT ? OFFSET ?",
                (per_page, offset)
            )
            companies = [dict(row) for row in cursor]
            conn.close()
            
            result = {
                "companies": companies,
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
            
            # Cache the result
            cache.set(cache_key, result, 300)  # 5 minutes
            
            return jsonify({"data": result})
            
        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/companies/<symbol>')
    def get_company(symbol):
        try:
            cache_key = f"company:{symbol}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return jsonify(cached_result)
            
            conn = db_manager.get_connection()
            cursor = conn.execute("SELECT * FROM companies WHERE symbol = ?", (symbol,))
            company = cursor.fetchone()
            
            if not company:
                return jsonify({"error": "Company not found"}), 404
            
            company_dict = dict(company)
            
            # Get recent transcripts
            transcript_cursor = conn.execute(
                "SELECT * FROM transcripts WHERE company_id = ? ORDER BY date DESC LIMIT 5",
                (company_dict['id'],)
            )
            company_dict['recent_transcripts'] = [dict(row) for row in transcript_cursor]
            
            conn.close()
            
            # Cache the result
            cache.set(cache_key, company_dict, 300)
            
            return jsonify(company_dict)
            
        except Exception as e:
            logger.error(f"Error getting company {symbol}: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Sentiment Analysis API
    @app.route('/api/analyze/sentiment', methods=['POST'])
    def analyze_sentiment():
        try:
            data = request.get_json()
            text = data.get('text', '')
            
            if not text:
                return jsonify({"error": "Text is required"}), 400
            
            result = sentiment_analyzer.analyze_sentiment(text)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Company Sentiment Analysis API
    @app.route('/api/analyze/company', methods=['POST'])
    def analyze_company():
        try:
            data = request.get_json()
            company_name = data.get('company_name', '')
            text = data.get('text', '')
            
            if not company_name or not text:
                return jsonify({"error": "Company name and text are required"}), 400
            
            # Analyze sentiment
            sentiment_result = sentiment_analyzer.analyze_sentiment(text)
            
            # Store the analysis result
            conn = db_manager.get_connection()
            
            # Check if company exists
            cursor = conn.execute("SELECT id FROM companies WHERE LOWER(name) LIKE ?", (f"%{company_name.lower()}%",))
            company_row = cursor.fetchone()
            
            if company_row:
                company_id = company_row[0]
                # Store as a manual analysis
                conn.execute('''
                    INSERT INTO analyses (transcript_id, sentiment_score, confidence, created_at)
                    VALUES (NULL, ?, ?, ?)
                ''', (sentiment_result['score'], sentiment_result.get('confidence', 0.0), datetime.now().isoformat()))
                conn.commit()
            
            conn.close()
            
            # Handle both FinBERT and fallback sentiment results
            if isinstance(sentiment_result, dict) and 'score' in sentiment_result:
                score = sentiment_result['score']
            else:
                # Fallback for simple sentiment
                score = sentiment_result if isinstance(sentiment_result, (int, float)) else 0.0
                sentiment_result = {
                    'score': score,
                    'label': 'positive' if score > 0 else 'negative' if score < 0 else 'neutral',
                    'confidence': abs(score)
                }
            
            result = {
                "company_name": company_name,
                "sentiment": sentiment_result,
                "timestamp": datetime.now().isoformat(),
                "text_length": len(text),
                "recommendation": "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
            }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error analyzing company: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Alerts API
    @app.route('/api/alerts')
    def get_alerts():
        """Get alerts based on significant sentiment changes"""
        try:
            # For demo, return sample alerts
            alerts = [
                {
                    "id": 1,
                    "company": "Moderna Inc.",
                    "symbol": "MRNA",
                    "type": "sentiment_change",
                    "message": "Significant positive sentiment change detected",
                    "change": 0.45,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "company": "Pfizer Inc.",
                    "symbol": "PFE",
                    "type": "sentiment_drop",
                    "message": "Sentiment dropped below threshold",
                    "change": -0.32,
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            return jsonify({"data": {"alerts": alerts, "total": len(alerts)}})
            
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return jsonify({'error': 'Failed to fetch alerts'}), 500
    
    # Watchlist API
    @app.route('/api/watchlist')
    def get_watchlist():
        """Get user's watchlist"""
        try:
            # For demo, return top companies as watchlist
            conn = db_manager.get_connection()
            cursor = conn.execute("""
                SELECT symbol, name, market_cap 
                FROM companies 
                ORDER BY market_cap DESC 
                LIMIT 10
            """)
            
            watchlist = []
            for row in cursor.fetchall():
                watchlist.append({
                    'symbol': row[0],
                    'name': row[1],
                    'market_cap': row[2],
                    'added_at': datetime.now().isoformat()
                })
            
            conn.close()
            
            return jsonify({"data": {"watchlist": watchlist, "total": len(watchlist)}})
            
        except Exception as e:
            logger.error(f"Error fetching watchlist: {e}")
            return jsonify({'error': 'Failed to fetch watchlist'}), 500
    
    # Performance Monitoring API
    # Reports endpoint
    @app.route('/api/reports')
    def get_reports():
        """Get analysis reports"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get recent analyses with sentiment scores
            cursor.execute("""
                SELECT 
                    a.id,
                    c.symbol,
                    c.name,
                    t.quarter,
                    t.year,
                    a.sentiment_score,
                    a.created_at
                FROM analyses a
                JOIN transcripts t ON a.transcript_id = t.id
                JOIN companies c ON t.company_id = c.id
                ORDER BY a.created_at DESC
                LIMIT 50
            """)
            
            reports = []
            for row in cursor.fetchall():
                reports.append({
                    'id': row[0],
                    'symbol': row[1],
                    'company_name': row[2],
                    'quarter': row[3],
                    'year': row[4],
                    'sentiment_score': row[5],
                    'created_at': row[6]
                })
            
            return jsonify({'data': {'reports': reports}})
        except Exception as e:
            logger.error(f"Error fetching reports: {e}")
            return jsonify({'error': 'Failed to fetch reports'}), 500
    
    @app.route('/api/performance/status')
    def performance_status():
        try:
            metrics = performance_monitor.get_system_metrics()
            latencies = performance_monitor.get_service_latencies()
            
            status = "healthy"
            if latencies.get("database_ms", 0) > 1000 or latencies.get("cache_ms", 0) > 100:
                status = "degraded"
            
            return jsonify({
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "system_metrics": metrics,
                "service_latencies": latencies
            })
            
        except Exception as e:
            logger.error(f"Error getting performance status: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/performance/test/database', methods=['POST'])
    def test_database_performance():
        try:
            start_time = time.time()
            
            # Perform database operations
            conn = db_manager.get_connection()
            for i in range(10):
                conn.execute("SELECT COUNT(*) FROM companies")
            conn.close()
            
            end_time = time.time()
            
            return jsonify({
                "test": "database",
                "duration_ms": round((end_time - start_time) * 1000, 2),
                "operations": 10,
                "avg_ms_per_op": round(((end_time - start_time) * 1000) / 10, 2),
                "status": "completed"
            })
            
        except Exception as e:
            logger.error(f"Error testing database performance: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/performance/test/cache', methods=['POST'])
    def test_cache_performance():
        try:
            start_time = time.time()
            
            # Perform cache operations
            for i in range(100):
                cache.set(f"test_key_{i}", f"test_value_{i}")
                cache.get(f"test_key_{i}")
            
            # Cleanup
            for i in range(100):
                cache.delete(f"test_key_{i}")
            
            end_time = time.time()
            
            return jsonify({
                "test": "cache",
                "duration_ms": round((end_time - start_time) * 1000, 2),
                "operations": 300,  # 100 sets + 100 gets + 100 deletes
                "avg_ms_per_op": round(((end_time - start_time) * 1000) / 300, 2),
                "status": "completed"
            })
            
        except Exception as e:
            logger.error(f"Error testing cache performance: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/performance/test/sentiment', methods=['POST'])
    def test_sentiment_performance():
        try:
            test_text = "The company reported strong quarterly earnings with revenue growth of 15% year-over-year."
            
            start_time = time.time()
            result = sentiment_analyzer.analyze_sentiment(test_text)
            end_time = time.time()
            
            return jsonify({
                "test": "sentiment_analysis",
                "duration_ms": round((end_time - start_time) * 1000, 2),
                "sentiment_result": result,
                "status": "completed"
            })
            
        except Exception as e:
            logger.error(f"Error testing sentiment performance: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Dashboard API
    @app.route('/api/dashboard/summary')
    @app.route('/api/dashboard')
    def dashboard_summary():
        try:
            cache_key = "dashboard:summary"
            cached_result = cache.get(cache_key)
            if cached_result:
                return jsonify(cached_result)
            
            conn = db_manager.get_connection()
            
            # Get basic stats
            company_count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
            transcript_count = conn.execute("SELECT COUNT(*) FROM transcripts").fetchone()[0]
            
            # Get recent companies by market cap
            recent_companies = conn.execute(
                "SELECT symbol, name, market_cap FROM companies ORDER BY market_cap DESC LIMIT 5"
            ).fetchall()
            
            conn.close()
            
            result = {
                "total_companies": company_count,
                "total_transcripts": transcript_count,
                "top_companies": [dict(row) for row in recent_companies],
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, result, 300)
            
            return jsonify({"data": result})
            
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Export API
    @app.route('/api/export/companies/csv')
    def export_companies_csv():
        try:
            csv_data = export_service.export_companies_csv()
            return send_file(
                io.BytesIO(csv_data.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'companies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
        except Exception as e:
            logger.error(f"Error exporting companies CSV: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/export/companies/json')
    def export_companies_json():
        try:
            json_data = export_service.export_companies_json()
            return send_file(
                io.BytesIO(json_data.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'companies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            
        except Exception as e:
            logger.error(f"Error exporting companies JSON: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app


def main():
    """Main function to run the unified OpalSight application"""
    print("🚀 Starting OpalSight Unified Application...")
    print("=" * 60)
    
    # Create and run the Flask app
    app = create_app()
    
    print("\n✅ OpalSight Application Ready!")
    print(f"🌐 Frontend: http://localhost:3000")
    print(f"🔧 API Health: http://localhost:3000/api/health")
    print(f"📊 Performance: http://localhost:3000/api/performance/status")
    print(f"🏢 Companies: http://localhost:3000/api/companies")
    print(f"📈 Dashboard: http://localhost:3000/api/dashboard/summary")
    print("=" * 60)
    print("Features included:")
    print("  ✓ React Frontend (served from /static)")
    print("  ✓ Flask Backend API")
    print("  ✓ SQLite Database (embedded)")
    print("  ✓ In-Memory Caching")
    if ML_AVAILABLE:
        print("  ✓ FinBERT Sentiment Analysis")
    else:
        print("  ⚠ ML Libraries not available (install torch & transformers)")
    print("  ✓ Performance Monitoring")
    print("  ✓ Export Functionality (CSV/JSON)")
    print("  ✓ Sample Biotech Companies & Transcripts")
    print("=" * 60)
    print("Press Ctrl+C to stop the application")
    
    try:
        app.run(host='0.0.0.0', port=3000, debug=Config.DEBUG, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Stopping OpalSight Application...")
    except Exception as e:
        logger.error(f"Error running application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
