"""Database models for OpalSight"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# Import all models
from .company import Company
from .transcript import Transcript
from .sentiment import SentimentAnalysis
from .trend import TrendAnalysis
from .report import MonthlyReport
from .api_usage import APIUsage
from .alert import Alert
from .watchlist import Watchlist

__all__ = [
    'db',
    'migrate',
    'Company',
    'Transcript',
    'SentimentAnalysis', 
    'TrendAnalysis',
    'MonthlyReport',
    'APIUsage',
    'Alert',
    'Watchlist'
] 