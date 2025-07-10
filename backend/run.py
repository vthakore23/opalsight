"""OpalSight Application Entry Point"""
import os
from app import create_app

# Create the application
app = create_app(os.environ.get('FLASK_ENV'))

if __name__ == '__main__':
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8000)),
        debug=app.config['DEBUG']
    ) 