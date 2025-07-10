#!/bin/bash

# OpalSight Backend Startup Script
set -e

echo "Starting OpalSight Backend..."

# Navigate to backend directory
cd backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Set environment variables
export DATABASE_URL="sqlite:///$(pwd)/instance/opalsight.db"
export REDIS_URL=""
export CACHE_TYPE="simple"
export FLASK_ENV="development"
export FLASK_DEBUG="1"

# Check if database exists, if not create it
if [ ! -f "instance/opalsight.db" ]; then
    echo "Database not found. Creating database directory..."
    mkdir -p instance
fi

# Start the Flask application
echo "Starting Flask server on http://localhost:8000..."
python run.py 