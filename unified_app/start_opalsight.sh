#!/bin/bash

echo "🚀 OpalSight Unified Application Launcher"
echo "========================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is required but not installed."
    echo "Please install pip and try again."
    exit 1
fi

echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install dependencies."
    echo "Please check the requirements.txt file and try again."
    exit 1
fi

echo "✅ Dependencies installed successfully!"
echo ""
echo "🎯 Starting OpalSight application..."
echo "Access the application at: http://localhost:3000"
echo ""

# Run the application
python3 opalsight_unified.py
