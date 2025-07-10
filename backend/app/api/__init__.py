"""API Blueprint"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import routes to register them
from . import routes

# Import performance routes
from . import performance 