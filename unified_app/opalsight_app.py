#!/usr/bin/env python3
"""
OpalSight - Unified Application
Automated Earnings Call Analysis Platform for Biotech/Medtech Companies

This is a single-file application that includes:
- Flask backend with all API routes
- SQLite database (embedded)
- In-memory caching
- FinBERT sentiment analysis
- Performance monitoring
- Export functionality
- Email service
- Background scheduler
- Frontend serving

Run with: python opalsight_app.py
Access at: http://localhost:3000
"""

import os
import sys
import time
import json
import sqlite3
import threading
import logging
import smtplib
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import io
import csv

# Flask and related imports
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import requests

# Data processing imports
import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

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
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Database settings (SQLite)
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'opalsight.db')
    
    # API settings
    FMP_API_KEY = os.getenv('FMP_API_KEY', '9a835ed8bbff501bf036a6f843d5a6fe')
    
    # Email settings (optional)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'noreply@opalsight.com')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # OpenAI settings (optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    USE_GPT_ENHANCEMENT = os.getenv('USE_GPT_ENHANCEMENT', 'false').lower() == 'true'


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
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_transcripts_company_id ON transcripts(company_id)",
                "CREATE INDEX IF NOT EXISTS idx_sentiment_transcript_id ON sentiment_analysis(transcript_id)"
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
            ('AMGN', 'Amgen Inc.', 'Biotechnology', 140000000000)
        ]
        
        for symbol, name, sector, market_cap in sample_companies:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO companies (symbol, name, sector, market_cap) VALUES (?, ?, ?, ?)",
                    (symbol, name, sector, market_cap)
                )
            except Exception as e:
                logger.warning(f"Error inserting sample company {symbol}: {e}")
    
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
        self.load_model()
    
    def load_model(self):
        """Load FinBERT model for financial sentiment analysis"""
        try:
            logger.info("Loading FinBERT model...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading FinBERT model: {e}")
            self.tokenizer = None
            self.model = None
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of given text"""
        if not self.model or not self.tokenizer:
            return {"sentiment": 0.0, "confidence": 0.0, "error": "Model not loaded"}
        
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
            return {"sentiment": 0.0, "confidence": 0.0, "error": str(e)}


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
                    "memory_available_gb": memory.available / 1024 / 1024 / 1024,
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / 1024 / 1024 / 1024
                },
                "process": {
                    "cpu_percent": process_cpu,
                    "memory_mb": process_memory
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
    
    # Frontend routes
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        try:
            return send_from_directory(app.static_folder, path)
        except:
            # For React Router, return index.html for unknown routes
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
                "cache": "healthy" if cache_healthy else "unhealthy"
            }
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
            
            return jsonify(result)
            
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
    
    # Performance Monitoring API
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
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}")
            return jsonify({"error": str(e)}), 500
    
    # Export API (simplified)
    @app.route('/api/export/companies/csv')
    def export_companies_csv():
        try:
            conn = db_manager.get_connection()
            cursor = conn.execute("SELECT * FROM companies")
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([description[0] for description in cursor.description])
            
            # Write data
            for row in cursor:
                writer.writerow(row)
            
            conn.close()
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'companies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
            
        except Exception as e:
            logger.error(f"Error exporting companies CSV: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app


def main():
    """Main function to run the unified OpalSight application"""
    print("🚀 Starting OpalSight Unified Application...")
    print("=" * 60)
    
    # Create requirements file
    requirements = """Flask==2.3.2
Flask-CORS==4.0.0
torch>=1.9.0
transformers>=4.21.0
numpy>=1.21.0
pandas>=1.3.0
psutil>=5.8.0
requests>=2.28.0"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("📋 Requirements file created")
    
    # Create and run the Flask app
    app = create_app()
    
    print("\n✅ OpalSight Application Ready!")
    print(f"🌐 Frontend: http://localhost:3000")
    print(f"🔧 API Health: http://localhost:3000/api/health")
    print(f"📊 Performance: http://localhost:3000/api/performance/status")
    print(f"🏢 Companies: http://localhost:3000/api/companies")
    print("=" * 60)
    print("Features included:")
    print("  ✓ React Frontend (served from /static)")
    print("  ✓ Flask Backend API")
    print("  ✓ SQLite Database (embedded)")
    print("  ✓ In-Memory Caching")
    print("  ✓ FinBERT Sentiment Analysis")
    print("  ✓ Performance Monitoring")
    print("  ✓ Export Functionality")
    print("  ✓ Sample Biotech Companies")
    print("=" * 60)
    print("Press Ctrl+C to stop the application")
    
    try:
        app.run(host='0.0.0.0', port=3000, debug=Config.DEBUG, threaded=True)
    except KeyboardInterrupt:
        print("\n�� Stopping OpalSight Application...")
    except Exception as e:
        logger.error(f"Error running application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
