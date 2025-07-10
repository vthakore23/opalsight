#!/usr/bin/env python3
"""
OpalSight - Simple Unified Application
A simplified version that combines frontend and backend in one Python app
"""

import os
import json
import sqlite3
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

class SimpleConfig:
    SECRET_KEY = 'opalsight-simple-2025'
    DATABASE_PATH = 'simple_opalsight.db'

class SimpleDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY,
                symbol TEXT UNIQUE,
                name TEXT,
                sector TEXT,
                market_cap INTEGER
            )
        ''')
        
        # Insert sample data
        companies = [
            ('MRNA', 'Moderna Inc.', 'Biotechnology', 50000000000),
            ('PFE', 'Pfizer Inc.', 'Biotechnology', 200000000000),
            ('JNJ', 'Johnson & Johnson', 'Healthcare', 400000000000)
        ]
        
        for symbol, name, sector, market_cap in companies:
            conn.execute(
                "INSERT OR IGNORE INTO companies (symbol, name, sector, market_cap) VALUES (?, ?, ?, ?)",
                (symbol, name, sector, market_cap)
            )
        
        conn.commit()
        conn.close()
    
    def get_companies(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM companies ORDER BY market_cap DESC")
        companies = [dict(row) for row in cursor]
        conn.close()
        return companies

def create_simple_app():
    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config.from_object(SimpleConfig)
    CORS(app)
    
    # Initialize database
    db = SimpleDatabase(SimpleConfig.DATABASE_PATH)
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        try:
            return send_from_directory(app.static_folder, path)
        except:
            return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/api/health')
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "OpalSight Simple App is running!"
        })
    
    @app.route('/api/companies')
    def get_companies():
        try:
            companies = db.get_companies()
            return jsonify({
                "companies": companies,
                "total": len(companies),
                "message": "Sample biotech companies"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/test')
    def test():
        return jsonify({
            "message": "OpalSight Simple API is working!",
            "features": [
                "React Frontend (static files)",
                "Flask Backend API",
                "SQLite Database",
                "Sample Biotech Companies",
                "Health Check Endpoint"
            ],
            "timestamp": datetime.now().isoformat()
        })
    
    return app

def main():
    print("🚀 Starting OpalSight Simple Application...")
    print("=" * 50)
    
    app = create_simple_app()
    
    print("✅ OpalSight Simple App Ready!")
    print(f"🌐 Access at: http://localhost:3000")
    print(f"🔧 Health Check: http://localhost:3000/api/health")
    print(f"🏢 Companies API: http://localhost:3000/api/companies")
    print(f"🧪 Test API: http://localhost:3000/api/test")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=3000, debug=True)
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")

if __name__ == '__main__':
    main()
