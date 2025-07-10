@echo off

echo Starting OpalSight Backend...

REM Navigate to backend directory
cd backend

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run: cd backend && python -m venv venv && venv\Scripts\activate.bat && pip install -r requirements.txt
    pause
    exit /b 1
)

REM Set environment variables
set DATABASE_URL=sqlite:///%cd%/instance/opalsight.db
set REDIS_URL=
set CACHE_TYPE=simple
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Check if database exists, if not create it
if not exist "instance\opalsight.db" (
    echo Database not found. Creating database directory...
    mkdir instance
)

REM Start the Flask application
echo Starting Flask server on http://localhost:8000...
python run.py

pause 